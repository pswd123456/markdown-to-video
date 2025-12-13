from langgraph.graph import StateGraph, END
from typing import Literal, Dict, Any

from src.core.state import GraphState
from src.core.config import settings
from src.core.models import CodeGenerationRequest
from src.components.context_builder import ContextBuilder
from src.components.linter import CodeLinter
from src.components.renderer import ManimRunner
from src.llm.client import LLMClient
from src.utils.code_ops import extract_code

class ManimGraph:
    def __init__(self):
        # 初始化工具链
        self.context_builder = ContextBuilder()
        self.llm = LLMClient()
        self.linter = CodeLinter()
        self.runner = ManimRunner()
        
        # 配置
        self.MAX_RETRIES = 3

    # ==========================
    #         NODES
    # ==========================

    def node_generate_code(self, state: GraphState) -> Dict[str, Any]:
        """[Node] 根据当前状态生成或修复代码"""
        current_retries = state.get("retries", 0)
        print(f"🤖 [Node: Generate] Attempt {current_retries + 1}/{self.MAX_RETRIES + 1}")

        # 1. 准备请求对象
        is_retry = (current_retries > 0)
        req = CodeGenerationRequest(
            scene=state["scene_spec"],
            previous_code=state.get("code"),
            feedback_context=state.get("error_log") if is_retry else None
        )

        # 2. 构建 Prompt
        sys_prompt = self.context_builder.build_system_prompt()
        user_prompt = self.context_builder.build_user_prompt(req)

        # 3. 调用 LLM
        raw_resp = self.llm.generate_code(sys_prompt, user_prompt)
        new_code = extract_code(raw_resp)

        # 4. 返回状态更新 (LangGraph 会合并此字典到主 State)
        return {
            "code": new_code,
            # 注意：重试计数器在进入此节点前或离开后更新均可，这里选择不在此处增加，
            # 而是由 Edge 路由决定何时算作一次消耗。
            # 但为了简单，我们在发生错误进入 retry 分支时已经隐式消耗了一次机会。
        }

    def node_check_syntax(self, state: GraphState) -> Dict[str, Any]:
        """[Node] 静态代码检查 (Fail-Fast)"""
        print(f"🔍 [Node: Lint] Checking code syntax...")
        code = state["code"]
        
        lint_result = self.linter.validate(code)
        
        if lint_result.passed:
            print("   ✅ Linter passed.")
            return {"error_log": None} # 清除错误
        else:
            print(f"   ❌ Linter failed: {lint_result.error_type}")
            return {"error_log": lint_result.traceback}

    def node_render(self, state: GraphState) -> Dict[str, Any]:
        """[Node] Docker 渲染"""
        print(f"🎨 [Node: Render] Rendering in Docker...")
        try:
            artifact = self.runner.render(
                state["code"],
                state["scene_spec"].scene_id
            )
            return {"artifact": artifact}
        except Exception as e:
            print(f"   ❌ Render runtime error: {e}")
            return {"error_log": str(e)}

    # ==========================
    #         EDGES
    # ==========================

    def edge_router_after_lint(self, state: GraphState) -> Literal["render", "generate", "failed"]:
        """[Edge] Linter 后的路由逻辑"""
        
        # 1. 如果无错误，直接去渲染
        if state.get("error_log") is None:
            return "render"
        
        # 2. 如果有错误，检查是否超出重试次数
        current_retries = state.get("retries", 0)
        if current_retries >= self.MAX_RETRIES:
            print("   ⛔ Max retries reached. Giving up.")
            return "failed"
            
        # 3. 没超限，回炉重造
        print(f"   🔄 Routing back to generator (Retry {current_retries + 1})...")
        return "generate"

    def edge_update_retry_count(self, state: GraphState) -> Dict[str, Any]:
        """辅助逻辑：在回跳前增加计数器 (LangGraph 允许在 Edge 中返回状态更新吗？通常不，这里我们在 Node 中处理或者使用专门的 updater node)"""
        # 修正：LangGraph 的 Conditional Edge 只负责路由。
        # 我们需要在路由回 "generate" 之前，确保 retry 计数+1。
        # 最佳实践是添加一个轻量级的 "prepare_retry" 节点。
        pass 

    # ==========================
    #       COMPILATION
    # ==========================

    def compile(self):
        workflow = StateGraph(GraphState)

        # 1. 添加节点
        workflow.add_node("generate", self.node_generate_code)
        workflow.add_node("lint", self.node_check_syntax)
        workflow.add_node("render", self.node_render)
        
        # 添加一个专门用于更新重试计数的节点，使逻辑更清晰
        def node_prepare_retry(state: GraphState):
            return {"retries": state["retries"] + 1}
        workflow.add_node("prepare_retry", node_prepare_retry)

        # 失败节点 (标记结束)
        workflow.add_node("failed", lambda x: print("Workflow Failed."))

        # 2. 定义流程
        workflow.set_entry_point("generate")
        
        workflow.add_edge("generate", "lint")

        # 条件分支
        workflow.add_conditional_edges(
            "lint",
            self.edge_router_after_lint,
            {
                "render": "render",        # 通过 -> 渲染
                "generate": "prepare_retry", # 失败 -> 准备重试 -> 生成
                "failed": "failed"         # 彻底失败
            }
        )
        
        workflow.add_edge("prepare_retry", "generate") # 闭环

        workflow.add_edge("render", END)
        workflow.add_edge("failed", END)

        return workflow.compile()