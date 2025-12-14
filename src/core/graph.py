from langgraph.graph import StateGraph, END
from typing import Literal, Dict, Any
from pathlib import Path
import json

from src.core.config import settings
from src.core.state import GraphState
from src.core.models import CodeGenerationRequest
from src.components.context_builder import ContextBuilder
from src.components.linter import CodeLinter
from src.components.renderer import ManimRunner
from src.components.critic import VisionCritic 
from src.llm.client import LLMClient
from src.llm.prompts import (
    build_planner_system_prompt, 
    build_planner_user_prompt,
    build_code_user_prompt,
    build_fixer_system_prompt,
    build_fixer_user_prompt
)
from src.utils.code_ops import extract_code

class ManimGraph:
    def __init__(self):
        self.context_builder = ContextBuilder()
        
        # 实例化 Client
        # Planner 和 Fixer 需要强推理能力，使用 max 模型
        self.planner_llm = LLMClient(model=settings.PLANNER_MODEL) 
        # Coder 只需要强编码能力，使用 coder 模型
        self.coder_llm = LLMClient(model=settings.CODER_MODEL)
        
        self.linter = CodeLinter()
        self.runner = ManimRunner()
        self.critic = VisionCritic() 
        
        self.MAX_SYNTAX_RETRIES = 3
        self.MAX_VISUAL_RETRIES = 2 

        # 创建用于保存修复计划的目录
        self.FIX_PLAN_OUTPUT_DIR = settings.OUTPUT_DIR / "fix_plan"
        self.FIX_PLAN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
 

    # --- Node 1: Planner (布局规划) ---
    def node_plan_layout(self, state: GraphState) -> Dict[str, Any]:
        print("\n🤔 [Node: Planner] Thinking about layout...")
        
        # 如果是视觉重试，且已经有 Fix 指令，我们可以跳过 Planner 重新规划，
        # 或者是让 Planner 基于 Critic 的反馈微调 Plan。
        # 这里的策略：如果是重试，直接沿用旧 Plan，跳过此节点 (通过路由控制，或者在这里直接返回旧值)
        if state.get("layout_plan"):
            print("   ─ Using existing plan for retry.")
            return {}

        scene = state["scene_spec"]
        sys_prompt = build_planner_system_prompt()
        user_prompt = build_planner_user_prompt(scene)
        
        plan = self.planner_llm.generate_text(sys_prompt, user_prompt)
        print(f"   ─ Plan generated: {plan[:50]}...")
        
        return {"layout_plan": plan}

    # --- Node 2: Fixer (错误分析与指导) [NEW] ---
    def node_analyze_error(self, state: GraphState) -> Dict[str, Any]:
        print("\n🔧 [Node: Fixer] Analyzing error and planning fix...")
        
        code = state.get("code")
        plan = state.get("layout_plan")
        
        # 确定错误的来源（Critic 的反馈 还是 Linter 的报错）
        if state.get("critic_feedback"):
            error_context = f"Visual QA Failed: {state['critic_feedback']}"
            print("   👉 Analyzing Visual Issue")
        elif state.get("error_log"):
            error_context = f"Runtime/Syntax Error: {state['error_log']}"
            print("   👉 Analyzing Code Error")
        else:
            error_context = "Unknown error."

        # 构建 Prompt
        # Fixer 需要看到 API 定义才能给出准确的修复建议
        sys_prompt = build_fixer_system_prompt(self.context_builder.api_stubs, self.context_builder.examples)
        user_prompt = build_fixer_user_prompt(plan, code, error_context)
        
        # 使用推理能力强的模型 (qwen3-max)
        instructions = self.planner_llm.generate_text(sys_prompt, user_prompt)
        
        # 保存修复计划到文件
        scene_id = state["scene_spec"].scene_id
        vis_try = state.get("visual_retries", 0)
        fix_plan_filename = self.FIX_PLAN_OUTPUT_DIR / f"{scene_id}_fix_v{vis_try}.json"
        with open(fix_plan_filename, "w", encoding="utf-8") as f:
            json.dump({"error_context": error_context, "fix_instructions": instructions}, f, ensure_ascii=False, indent=2)
        print(f"   ─ Fix strategy saved to {fix_plan_filename}")
        
        print(f"   ─ Fix Strategy: {instructions[:80]}...")
        return {"fix_instructions": instructions}

    # --- Node 3: Coder (代码生成) ---
    def node_generate_code(self, state: GraphState) -> Dict[str, Any]:
        """生成或修复代码"""
        syn_try = state.get("retries", 0)
        vis_try = state.get("visual_retries", 0)
        print(f"\n🤖 [Node: Coder] (Syntax Try: {syn_try}, Visual Try: {vis_try})")

        req = CodeGenerationRequest(
            scene=state["scene_spec"],
            previous_code=state.get("code"),
            # 注意：这里不再直接传 raw feedback，而是依靠 fix_instructions
            feedback_context=None 
        )

        plan = state.get("layout_plan", "")
        fix_instructions = state.get("fix_instructions")

        # 构建 Prompt
        sys_prompt = self.context_builder.build_system_prompt()
        user_prompt = build_code_user_prompt(req, plan, fix_instructions)
        
        # 调用 Coder
        raw_resp = self.coder_llm.generate_code(sys_prompt, user_prompt)
        new_code = extract_code(raw_resp)

        return {"code": new_code}

    # --- Node 4: Lint (静态检查) ---
    def node_check_syntax(self, state: GraphState) -> Dict[str, Any]:
        print("[Node: Lint] Checking code syntax...")
        res = self.linter.validate(state["code"])
        if res.passed:
            return {"error_log": None}
        else:
            print(f"   ❌ Syntax/DryRun Failed: {res.error_type}")
            return {"error_log": res.traceback}

    # --- Node 5: Render (渲染) ---
    def node_render(self, state: GraphState) -> Dict[str, Any]:
        print("🎨 [Node: Render] Rendering in Docker...")
        
        scene_id = state["scene_spec"].scene_id
        vis_try = state.get("visual_retries", 0)
        
        render_id = f"{scene_id}_v{vis_try}" if vis_try > 0 else scene_id

        try:
            artifact = self.runner.render(state["code"], render_id)
            return {"artifact": artifact, "error_log": None}
        except Exception as e:
            return {"error_log": str(e), "artifact": None}

    # --- Node 6: Critic (视觉审查) ---
    def node_critic(self, state: GraphState) -> Dict[str, Any]:
        print("👀 [Node: Critic] Inspecting visual layout...")
        artifact = state.get("artifact")
        
        if not artifact or not artifact.last_frame_path or artifact.last_frame_path == "N/A":
             print("   ─ No image found to critique.")
             return {"critic_feedback": None}

        feedback = self.critic.review_layout(artifact.last_frame_path, state["scene_spec"])
        
        # 注意：这里我们适配了新的 prompt 返回结构，models.py 中的 CritiqueFeedback 需要包含 'suggestion'
        # 但新的 Critic prompt 返回的是 'reason'。
        # 我们在这里做一个简单的映射，把 reason 存入 suggestion 字段，以便向后兼容 Fixer。
        suggestion = feedback.suggestion if feedback.suggestion else getattr(feedback, 'reason', "Visual check failed")

        if feedback.passed:
            print(f"   ✅ Visual QC Passed (Score: {feedback.score})")
            return {"critic_feedback": None}
        else:
            print(f"   ❌ Visual QC Failed (Score: {feedback.score}): {suggestion}")
            return {"critic_feedback": suggestion, "critic_score": feedback.score}

    # --- Helper Nodes: State Management ---
    def node_prep_syntax_retry(self, state: GraphState):
        return {"retries": state.get("retries", 0) + 1}

    def node_prep_visual_retry(self, state: GraphState):
        return {
            "visual_retries": state.get("visual_retries", 0) + 1,
            "retries": 0, # 重置语法重试计数
            "error_log": None
        }

    # --- Edges ---
    def edge_router_after_lint(self, state: GraphState) -> Literal["render", "fixer", "failed"]:
        if state.get("error_log"):
            if state.get("retries", 0) >= self.MAX_SYNTAX_RETRIES:
                return "failed"
            return "fixer" # 失败 -> Fixer 分析
        return "render"

    def edge_router_after_render(self, state: GraphState) -> Literal["critic", "finish", "fixer"]:
        if state.get("error_log"):
            # 渲染报错（如超时），也交给 Fixer 看看能不能简化代码
            return "fixer"
        
        if state.get("visual_retries", 0) >= self.MAX_VISUAL_RETRIES:
            print("   ─ Max visual retries reached. Skipping critic.")
            return "finish"

        return "critic"

    def edge_router_after_critic(self, state: GraphState) -> Literal["finish", "fixer"]:
        if state.get("critic_feedback") is None:
            return "finish"
        
        if state.get("visual_retries", 0) >= self.MAX_VISUAL_RETRIES:
            return "finish"
            
        return "fixer" # 视觉失败 -> Fixer 分析

    def edge_router_after_fixer(self, state: GraphState) -> Literal["prep_syn", "prep_vis"]:
        # 根据错误类型决定增加哪个计数器
        # 如果有 error_log，说明是语法/运行时错误 -> prep_syn
        # 如果有 critic_feedback，说明是视觉错误 -> prep_vis
        if state.get("critic_feedback"):
            return "prep_vis"
        return "prep_syn"

    # --- Compile ---
    def compile(self):
        workflow = StateGraph(GraphState)
        
        # Add Nodes
        workflow.add_node("plan", self.node_plan_layout)
        workflow.add_node("generate", self.node_generate_code)
        workflow.add_node("lint", self.node_check_syntax)
        workflow.add_node("render", self.node_render)
        workflow.add_node("critic", self.node_critic)
        workflow.add_node("fixer", self.node_analyze_error) # The New Brain
        
        workflow.add_node("prep_syn", self.node_prep_syntax_retry)
        workflow.add_node("prep_vis", self.node_prep_visual_retry)
        workflow.add_node("failed", lambda x: print("❌ Workflow Failed"))

        # Define Flows
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "generate")
        workflow.add_edge("generate", "lint")
        
        # Route 1: Lint Results
        workflow.add_conditional_edges(
            "lint",
            self.edge_router_after_lint,
            {
                "render": "render",
                "fixer": "fixer", # Error -> Fixer
                "failed": "failed"
            }
        )

        # Route 2: Render Results
        workflow.add_conditional_edges(
            "render",
            self.edge_router_after_render,
            {
                "critic": "critic", 
                "fixer": "fixer", # Render Error -> Fixer
                "finish": END
            }
        )

        # Route 3: Critic Results
        workflow.add_conditional_edges(
            "critic",
            self.edge_router_after_critic,
            {
                "finish": END,
                "fixer": "fixer" # Visual Issue -> Fixer
            }
        )
        
        # Route 4: Fixer -> Retry Logic
        workflow.add_conditional_edges(
            "fixer",
            self.edge_router_after_fixer,
            {
                "prep_syn": "prep_syn",
                "prep_vis": "prep_vis"
            }
        )
        
        # Retry Logic -> Generate (Loop Closed)
        workflow.add_edge("prep_syn", "generate")
        workflow.add_edge("prep_vis", "generate")
        
        workflow.add_edge("failed", END)

        return workflow.compile()