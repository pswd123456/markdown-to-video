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
from src.utils.code_ops import extract_code

class ManimGraph:
    def __init__(self):
        self.context_builder = ContextBuilder()
        self.llm = LLMClient()
        self.linter = CodeLinter()
        self.runner = ManimRunner()
        self.critic = VisionCritic() 
        
        self.MAX_SYNTAX_RETRIES = 3
        self.MAX_VISUAL_RETRIES = 2 # 视觉修正比较贵，试2次即可

    # --- Node: Generate ---
    def node_generate_code(self, state: GraphState) -> Dict[str, Any]:
        """生成或修复代码 (处理两种反馈来源)"""
        # 计算当前是第几次尝试 (仅用于日志)
        syn_try = state.get("retries", 0)
        vis_try = state.get("visual_retries", 0)
        print(f"🤖 [Node: Generate] (Syntax Try: {syn_try}, Visual Try: {vis_try})")

        # 确定反馈内容：优先看 Critic 反馈，其次看 Linter 反馈
        feedback = None
        if state.get("critic_feedback"):
            feedback = f"Visual QA Failed: {state['critic_feedback']}"
            print("   👉 Fixing based on Visual Feedback")
        elif state.get("error_log"):
            feedback = f"Runtime Error: {state['error_log']}"
            print("   👉 Fixing based on Linter Error")

        req = CodeGenerationRequest(
            scene=state["scene_spec"],
            previous_code=state.get("code"),
            feedback_context=feedback
        )

        sys_prompt = self.context_builder.build_system_prompt()
        user_prompt = self.context_builder.build_user_prompt(req)
        
        raw_resp = self.llm.generate_code(sys_prompt, user_prompt)
        new_code = extract_code(raw_resp)

        return {"code": new_code}

    # --- Node: Lint ---
    def node_check_syntax(self, state: GraphState) -> Dict[str, Any]:
        print("[Node: Lint] Checking code syntax...")
        res = self.linter.validate(state["code"])
        if res.passed:
            return {"error_log": None}
        else:
            return {"error_log": res.traceback}

    # --- Node: Render ---
    def node_render(self, state: GraphState) -> Dict[str, Any]:
        print("🎨 [Node: Render] Rendering in Docker...")
        try:
            artifact = self.runner.render(state["code"], state["scene_spec"].scene_id)
            return {"artifact": artifact, "error_log": None}
        except Exception as e:
            return {"error_log": str(e), "artifact": None}

    # --- Node: Critic (New) ---
    def node_critic(self, state: GraphState) -> Dict[str, Any]:
        print("👀 [Node: Critic] Inspecting visual layout...")
        artifact = state.get("artifact")
        
        # 极端情况：渲染成功但没图 (ffmpeg bug?)
        if not artifact or not artifact.last_frame_path or artifact.last_frame_path == "N/A":
             print("   ⚠️ No image found to critique.")
             return {"critic_feedback": None} # Skip critique

        feedback = self.critic.review_layout(artifact.last_frame_path, state["scene_spec"])
        
        if feedback.passed:
            print(f"   ✅ Visual QC Passed (Score: {feedback.score})")
            return {"critic_feedback": None}
        else:
            print(f"   ❌ Visual QC Failed (Score: {feedback.score}): {feedback.suggestion}")
            
            # Save failed code to output/debug/
            debug_dir = settings.OUTPUT_DIR / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            vis_try = state.get("visual_retries", 0)
            scene_id = state["scene_spec"].scene_id
            
            # Save the code
            code_path = debug_dir / f"scene_{scene_id}_failed_vis_retry_{vis_try}.py"
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(state["code"] or "")
            print(f"   💾 Saved erroneous code to {code_path}")

            return {"critic_feedback": feedback.suggestion}

    # --- Helper Nodes ---
    def node_prep_syntax_retry(self, state: GraphState):
        return {"retries": state.get("retries", 0) + 1}

    def node_prep_visual_retry(self, state: GraphState):
        # 视觉重试时，我们需要清除 error_log 以免混淆 generator，同时重置语法计数器
        return {
            "visual_retries": state.get("visual_retries", 0) + 1,
            "retries": 0, # 新代码要重新算语法检查次数
            "error_log": None 
        }

    # --- Edges ---
    def edge_router_after_lint(self, state: GraphState) -> Literal["render", "retry_syntax", "failed"]:
        if state.get("error_log"):
            if state.get("retries", 0) >= self.MAX_SYNTAX_RETRIES:
                return "failed"
            return "retry_syntax"
        return "render"

    def edge_router_after_render(self, state: GraphState) -> Literal["critic", "finish", "failed"]:
        # 如果渲染本身报错了（比如 OOM），直接 Fail (或者可以加逻辑跳回 Generate)
        if state.get("error_log"):
             return "failed" 
        
        # Optimization: Skip expensive visual critique if we can't retry anyway
        if state.get("visual_retries", 0) >= self.MAX_VISUAL_RETRIES:
            print("   ⛔ Max visual retries reached. Skipping final critic check.")
            return "finish"

        return "critic"

    def edge_router_after_critic(self, state: GraphState) -> Literal["finish", "retry_visual"]:
        if state.get("critic_feedback") is None:
            return "finish" # 没意见，或者通过了
        
        if state.get("visual_retries", 0) >= self.MAX_VISUAL_RETRIES:
            print("   ⛔ Max visual retries reached. Accepting result as is.")
            return "finish" # 累了，就这样吧
            
        return "retry_visual"

    # --- Compile ---
    def compile(self):
        workflow = StateGraph(GraphState)

        # Add Nodes
        workflow.add_node("generate", self.node_generate_code)
        workflow.add_node("lint", self.node_check_syntax)
        workflow.add_node("render", self.node_render)
        workflow.add_node("critic", self.node_critic)
        
        workflow.add_node("prep_syn", self.node_prep_syntax_retry)
        workflow.add_node("prep_vis", self.node_prep_visual_retry)
        workflow.add_node("failed", lambda x: print("Workflow Failed"))

        # Define Flows
        workflow.set_entry_point("generate")
        workflow.add_edge("generate", "lint")
        
        # 路由 1: 语法检查
        workflow.add_conditional_edges(
            "lint",
            self.edge_router_after_lint,
            {
                "render": "render",
                "retry_syntax": "prep_syn",
                "failed": "failed"
            }
        )
        workflow.add_edge("prep_syn", "generate")

        # 路由 2: 渲染后 -> 视觉审查
        workflow.add_conditional_edges(
            "render",
            self.edge_router_after_render,
            {"critic": "critic", "failed": "failed", "finish": END}
        )

        # 路由 3: 视觉审查结果
        workflow.add_conditional_edges(
            "critic",
            self.edge_router_after_critic,
            {
                "finish": END,
                "retry_visual": "prep_vis"
            }
        )
        workflow.add_edge("prep_vis", "generate") # 带着视觉反馈回到生成器
        workflow.add_edge("failed", END)

        return workflow.compile()