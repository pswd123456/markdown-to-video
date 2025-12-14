from langgraph.graph import StateGraph, END
from typing import Literal, Dict, Any


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
        
        self.planner_llm = LLMClient(model=settings.PLANNER_MODEL) # High reasoning
        self.coder_llm = LLMClient(model=settings.CODER_MODEL)     # High coding
        
        self.linter = CodeLinter()
        self.runner = ManimRunner()
        self.critic = VisionCritic() 
        
        self.MAX_SYNTAX_RETRIES = 3
        self.MAX_VISUAL_RETRIES = 2 

    # --- Node 1: Planner ---
    def node_plan_layout(self, state: GraphState) -> Dict[str, Any]:
        print("\n🤔 [Node: Planner] Thinking about layout...")
        if state.get("layout_plan"):
            return {}

        scene = state["scene_spec"]
        plan = self.planner_llm.generate_text(
            build_planner_system_prompt(), 
            build_planner_user_prompt(scene)
        )
        print(f"   ─ Plan generated: {plan[:50]}...")
        
        # Save the layout plan to a file
        try:
            scene_id = state["scene_spec"].scene_id
            plan_dir = settings.OUTPUT_DIR / "plan"
            plan_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{scene_id}_plan.md"
            with open(plan_dir / filename, "w", encoding="utf-8") as f:
                f.write(plan)
            print(f"   ─ Layout plan saved to {plan_dir / filename}")
        except Exception as e:
            print(f"   ⚠️ Failed to save layout plan: {e}")

        return {"layout_plan": plan}

    # --- Node 2: Fixer (The Brain) ---
    def node_analyze_error(self, state: GraphState) -> Dict[str, Any]:
        print("\n🔧 [Node: Fixer] Analyzing error and planning fix...")
        
        code = state.get("code")
        plan = state.get("layout_plan")
        
        # 1. 识别错误类型并构建上下文
        error_context = ""
        error_source = "Unknown"
        
        if state.get("critic_feedback"):
            # 来自 Critic 的视觉证据
            error_source = "Visual_Critic"
            error_context = f"VISUAL REPORT FROM QA:\n{state['critic_feedback']}\n(Note: Translate this visual issue into Manim API corrections)"
            print("   👉 Analyzing Visual Issue")
            
        elif state.get("error_log"):
            # 来自 Linter/Runtime 的报错
            error_source = "Runtime_Linter"
            error_context = f"EXECUTION TRACEBACK:\n{state['error_log']}"
            print("   👉 Analyzing Code Error")

        # 2. 调用大模型 (qwen3-max)
        sys_prompt = build_fixer_system_prompt(
            self.context_builder.api_stubs, 
            self.context_builder.examples
        )
        user_prompt = build_fixer_user_prompt(plan, code, error_context)
        
        instructions = self.planner_llm.generate_text(sys_prompt, user_prompt)
        print(f"   ─ Fix Strategy: {instructions[:80]}...")

        # 3. 保存 Fix Plan 用于调试 (Output to file)
        try:
            scene_id = state["scene_spec"].scene_id
            vis_try = state.get("visual_retries", 0)
            syn_try = state.get("retries", 0)
            
            fix_dir = settings.OUTPUT_DIR / "fix_plan"
            fix_dir.mkdir(parents=True, exist_ok=True)
            
            # 文件名带上重试轮次
            filename = f"{scene_id}_fix_v{vis_try}_s{syn_try}.md"
            with open(fix_dir / filename, "w", encoding="utf-8") as f:
                f.write(f"# Fix Plan ({error_source})\n\n")
                f.write(f"## Input Error Context\n{error_context}\n\n")
                f.write(f"## Generated Instructions\n{instructions}")
        except Exception as e:
            print(f"   ⚠️ Failed to save fix plan: {e}")

        return {"fix_instructions": instructions}

    # --- Node 3: Coder ---
    def node_generate_code(self, state: GraphState) -> Dict[str, Any]:
        syn_try = state.get("retries", 0)
        vis_try = state.get("visual_retries", 0)
        print(f"\n🤖 [Node: Coder] (Syntax Try: {syn_try}, Visual Try: {vis_try})")

        req = CodeGenerationRequest(
            scene=state["scene_spec"],
            previous_code=state.get("code"),
            feedback_context=None # 我们用 manual prompt injection
        )

        plan = state.get("layout_plan", "")
        fix_instructions = state.get("fix_instructions")
        
        # 准备上下文给 Coder 查阅
        error_context_summary = "No previous error."
        if state.get("critic_feedback"):
            error_context_summary = f"Visual Issue: {state['critic_feedback']}"
        elif state.get("error_log"):
            error_context_summary = f"Runtime Error: {state['error_log']}"

        sys_prompt = self.context_builder.build_system_prompt()
        # 注入所有必要信息
        user_prompt = build_code_user_prompt(req, plan, fix_instructions, error_context_summary)
        
        raw_resp = self.coder_llm.generate_code(sys_prompt, user_prompt)
        new_code = extract_code(raw_resp)

        return {"code": new_code}

    # --- Node 4: Lint ---
    def node_check_syntax(self, state: GraphState) -> Dict[str, Any]:
        print("[Node: Lint] Checking code syntax...")
        res = self.linter.validate(state["code"])
        if res.passed:
            return {"error_log": None}
        else:
            print(f"   ❌ Syntax/DryRun Failed: {res.error_type}")
            return {"error_log": res.traceback}

    # --- Node 5: Render ---
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

    # --- Node 6: Critic ---
    def node_critic(self, state: GraphState) -> Dict[str, Any]:
        print("👀 [Node: Critic] Inspecting visual layout...")
        artifact = state.get("artifact")
        
        if not artifact or not artifact.last_frame_path or artifact.last_frame_path == "N/A":
             print("   ─ No image found to critique.")
             return {"critic_feedback": None}

        feedback = self.critic.review_layout(artifact.last_frame_path, state["scene_spec"])
        
        # 关键映射：把 Critic 返回的 'suggestion' (也就是 Visual Evidence) 存入状态
        # 因为我们修改了 Prompt，现在 feedback.suggestion 里面是具体的视觉描述
        visual_evidence = feedback.suggestion if feedback.suggestion else "Visual check failed (No details)."

        # 保存 Critic 结果用于调试
        try:
            scene_id = state["scene_spec"].scene_id
            vis_try = state.get("visual_retries", 0)
            critic_dir = settings.OUTPUT_DIR / "critic"
            critic_dir.mkdir(parents=True, exist_ok=True)
            
            with open(critic_dir / f"{scene_id}_critic_v{vis_try}.txt", "w", encoding="utf-8") as f:
                f.write(f"Passed: {feedback.passed}\nScore: {feedback.score}\nEvidence: {visual_evidence}")
        except Exception as e:
            print(f"   ⚠️ Failed to save critique: {e}")

        if feedback.passed:
            print(f"   ✅ Visual QC Passed (Score: {feedback.score})")
            return {"critic_feedback": None}
        else:
            print(f"   ❌ Visual QC Failed: {visual_evidence}")
            return {"critic_feedback": visual_evidence, "critic_score": feedback.score}

    # --- Helper Nodes & Edges (Routing) ---
    def node_prep_syntax_retry(self, state: GraphState):
        return {"retries": state.get("retries", 0) + 1}

    def node_prep_visual_retry(self, state: GraphState):
        return {
            "visual_retries": state.get("visual_retries", 0) + 1,
            "retries": 0,
            "error_log": None
        }

    def edge_router_after_lint(self, state: GraphState) -> Literal["render", "fixer", "failed"]:
        if state.get("error_log"):
            if state.get("retries", 0) >= self.MAX_SYNTAX_RETRIES:
                return "failed"
            return "fixer" 
        return "render"

    def edge_router_after_render(self, state: GraphState) -> Literal["critic", "finish", "fixer"]:
        if state.get("error_log"):
            return "fixer"
        if state.get("visual_retries", 0) >= self.MAX_VISUAL_RETRIES:
            return "finish"
        return "critic"

    def edge_router_after_critic(self, state: GraphState) -> Literal["finish", "fixer"]:
        if state.get("critic_feedback") is None:
            return "finish"
        if state.get("visual_retries", 0) >= self.MAX_VISUAL_RETRIES:
            return "finish"
        return "fixer"

    def edge_router_after_fixer(self, state: GraphState) -> Literal["prep_syn", "prep_vis"]:
        if state.get("critic_feedback"):
            return "prep_vis"
        return "prep_syn"

    def compile(self):
        workflow = StateGraph(GraphState)
        
        workflow.add_node("plan", self.node_plan_layout)
        workflow.add_node("generate", self.node_generate_code)
        workflow.add_node("lint", self.node_check_syntax)
        workflow.add_node("render", self.node_render)
        workflow.add_node("critic", self.node_critic)
        workflow.add_node("fixer", self.node_analyze_error)
        workflow.add_node("prep_syn", self.node_prep_syntax_retry)
        workflow.add_node("prep_vis", self.node_prep_visual_retry)
        workflow.add_node("failed", lambda x: print("❌ Workflow Failed"))

        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "generate")
        workflow.add_edge("generate", "lint")
        
        workflow.add_conditional_edges("lint", self.edge_router_after_lint, {"render": "render", "fixer": "fixer", "failed": "failed"})
        workflow.add_conditional_edges("render", self.edge_router_after_render, {"critic": "critic", "fixer": "fixer", "finish": END})
        workflow.add_conditional_edges("critic", self.edge_router_after_critic, {"finish": END, "fixer": "fixer"})
        workflow.add_conditional_edges("fixer", self.edge_router_after_fixer, {"prep_syn": "prep_syn", "prep_vis": "prep_vis"})
        
        workflow.add_edge("prep_syn", "generate")
        workflow.add_edge("prep_vis", "generate")
        workflow.add_edge("failed", END)

        return workflow.compile()