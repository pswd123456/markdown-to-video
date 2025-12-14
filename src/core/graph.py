import asyncio
from langgraph.graph import StateGraph, END, START
from langgraph.constants import Send
from typing import Literal, Dict, Any, List

from src.core.config import settings
from src.core.state import GraphState, AggregateState
from src.core.models import CodeGenerationRequest
from src.components.context_builder import ContextBuilder
from src.components.linter import CodeLinter
from src.components.renderer import ManimRunner
from src.components.critic import VisionCritic 
from src.components.tts import TTSEngine
from src.llm.client import LLMClient
from src.llm.prompts import (
    build_planner_system_prompt, 
    build_planner_user_prompt,
    build_code_user_prompt,
    build_fixer_system_prompt,
    build_fixer_user_prompt
)
from src.utils.code_ops import extract_code
from src.utils.logger import logger, metrics

class ManimGraph:
    """
    子图：处理单个场景的生命周期 (TTS -> Plan -> Code -> Lint -> Render -> Critic)
    """
    def __init__(self):
        self.context_builder = ContextBuilder()
        
        # 使用异步 LLM Client
        self.planner_llm = LLMClient(model=settings.PLANNER_MODEL)
        self.coder_llm = LLMClient(model=settings.CODER_MODEL)
        
        self.linter = CodeLinter()
        self.runner = ManimRunner()
        self.critic = VisionCritic() 
        self.tts = TTSEngine()
        
        self.MAX_SYNTAX_RETRIES = 3
        self.MAX_VISUAL_RETRIES = 2 

    # --- Node 0: TTS (New in Graph) ---
    async def node_tts(self, state: GraphState) -> Dict[str, Any]:
        """
        并行生成音频，并修正 duration
        """
        # [Debug] 防御性检查
        if "scene_spec" not in state:
            logger.error(f"❌ [Node: TTS] Missing 'scene_spec' in state. Keys: {list(state.keys())}")
            raise KeyError("scene_spec")

        scene = state["scene_spec"]
        logger.info(f"🔊 [Node: TTS] Generating audio for {scene.scene_id}...")
        
        # 将同步的 TTS 生成放到线程池
        audio_path = await asyncio.to_thread(
            self.tts.generate, 
            scene.audio_script, 
            scene.scene_id
        )
        
        if audio_path:
            # 获取时长
            duration = await asyncio.to_thread(self.tts.get_duration, audio_path)
            if duration > 0:
                scene.duration = round(duration + 0.5, 2)
                logger.info(f"   ⏱️ [TTS] Updated {scene.scene_id} duration to {scene.duration}s")
        
        # 更新 state 中的 scene_spec (duration 可能变了)
        return {"scene_spec": scene}

    # --- Node 1: Planner ---
    async def node_plan_layout(self, state: GraphState) -> Dict[str, Any]:
        # [Debug] 确保 scene_spec 存在
        if "scene_spec" not in state:
             logger.error("❌ [Node: Planner] 'scene_spec' missing!")
             raise KeyError("scene_spec")

        logger.info(f"🤔 [Node: Planner] {state['scene_spec'].scene_id}")
        
        if state.get("layout_plan"):
            return {}

        scene = state["scene_spec"]
        # Async call
        plan = await self.planner_llm.generate_text(
            build_planner_system_prompt(), 
            build_planner_user_prompt(scene)
        )
        
        # Save file (non-blocking ideally, but small file IO is ok)
        try:
            plan_dir = settings.OUTPUT_DIR / "plan"
            plan_dir.mkdir(parents=True, exist_ok=True)
            with open(plan_dir / f"{scene.scene_id}_plan.md", "w", encoding="utf-8") as f:
                f.write(plan)
        except Exception:
            pass

        return {"layout_plan": plan}

    # --- Node 2: Fixer ---
    async def node_analyze_error(self, state: GraphState) -> Dict[str, Any]:
        logger.info(f"🔧 [Node: Fixer] {state['scene_spec'].scene_id}")
        
        code = state.get("code")
        plan = state.get("layout_plan")
        
        error_context = ""
        if state.get("critic_feedback"):
            error_context = f"VISUAL REPORT:\n{state['critic_feedback']}"
        elif state.get("error_log"):
            error_context = f"TRACEBACK:\n{state['error_log']}"

        sys_prompt = build_fixer_system_prompt(
            self.context_builder.api_stubs, 
            self.context_builder.examples
        )
        user_prompt = build_fixer_user_prompt(plan, code, error_context)
        
        # Async call
        instructions = await self.planner_llm.generate_text(sys_prompt, user_prompt)

        # --- [Add] Save Fix Plan ---
        try:
            scene = state["scene_spec"]
            vis_try = state.get("visual_retries", 0)
            syn_try = state.get("retries", 0)
            
            fix_dir = settings.OUTPUT_DIR / "fix_plan"
            fix_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{scene.scene_id}_fix_v{vis_try}_s{syn_try}.md"
            with open(fix_dir / filename, "w", encoding="utf-8") as f:
                f.write(f"# Fix Plan (Runtime_Linter/Visual_Critic)\n\n## Input Error Context\n{error_context}\n\n## Generated Instructions\n{instructions}")
        except Exception as e:
            logger.warning(f"Failed to save fix plan: {e}")

        return {"fix_instructions": instructions}

    # --- Node 3: Coder ---
    async def node_generate_code(self, state: GraphState) -> Dict[str, Any]:
        logger.info(f"🤖 [Node: Coder] {state['scene_spec'].scene_id}")

        req = CodeGenerationRequest(
            scene=state["scene_spec"],
            previous_code=state.get("code"),
            feedback_context=None 
        )

        plan = state.get("layout_plan", "")
        fix_instructions = state.get("fix_instructions")
        
        error_summary = "No error."
        if state.get("critic_feedback"):
            error_summary = f"Visual: {state['critic_feedback']}"
        elif state.get("error_log"):
            error_summary = f"Runtime: {state['error_log']}"

        sys_prompt = self.context_builder.build_system_prompt()
        user_prompt = build_code_user_prompt(req, plan, fix_instructions, error_summary)
        
        # Async call
        raw_resp = await self.coder_llm.generate_code(sys_prompt, user_prompt)
        new_code = extract_code(raw_resp)

        # --- [Add] Save Generated Code ---
        try:
            scene = state["scene_spec"]
            vis_try = state.get("visual_retries", 0)
            syn_try = state.get("retries", 0)
            
            code_dir = settings.OUTPUT_DIR / "scenes_code"
            code_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{scene.scene_id}_code_v{vis_try}_s{syn_try}.py"
            with open(code_dir / filename, "w", encoding="utf-8") as f:
                f.write(new_code)
        except Exception as e:
            logger.warning(f"Failed to save generated code: {e}")

        return {"code": new_code}

    # --- Node 4: Lint (CPU Bound) ---
    async def node_check_syntax(self, state: GraphState) -> Dict[str, Any]:
        # Linter 包含 subprocess 调用，虽然是 CPU 密集，但最好也扔到线程池
        res = await asyncio.to_thread(self.linter.validate, state["code"])
        if res.passed:
            return {"error_log": None}
        else:
            return {"error_log": res.traceback}

    # --- Node 5: Render (Heavy IO/CPU) ---
    async def node_render(self, state: GraphState) -> Dict[str, Any]:
        scene_id = state["scene_spec"].scene_id
        vis_try = state.get("visual_retries", 0)
        # 这里的 render_id 仅用于生成文件名，避免重试时覆盖旧文件
        render_id = f"{scene_id}_v{vis_try}" if vis_try > 0 else scene_id

        try:
            # 使用新的 render_async 方法 (带信号量)
            artifact = await self.runner.render_async(state["code"], render_id)
            
            # 【关键修复】: 
            # 无论 render_id 是什么（例如 "scene_01_v1"），
            # 这里的 artifact.scene_id 必须还原为原始 ID ("scene_01")。
            # 这样 Assembler 才能根据 "scene_01" 找到 "scene_01.mp3"。
            if artifact:
                artifact.scene_id = scene_id
            
            return {"artifact": artifact, "error_log": None}
        except Exception as e:
            return {"error_log": str(e), "artifact": None}

    # --- Node 6: Critic (VLM API) ---
    async def node_critic(self, state: GraphState) -> Dict[str, Any]:
        logger.info(f"👀 [Node: Critic] {state['scene_spec'].scene_id}")
        artifact = state.get("artifact")
        
        if not artifact or not artifact.last_frame_path or artifact.last_frame_path == "N/A":
             return {"critic_feedback": None}

        # Critic 内部调用了 OpenAI API，需要看它是否也是 async
        # 假设 Critic 目前是同步的 (requests/standard openai)，我们用 to_thread
        # 理想情况是把 Critic 也改成 async，这里用 to_thread 兼容
        feedback = await self.critic.review_layout(
            artifact.last_frame_path, 
            state["scene_spec"]
        )
        
        # --- [Add] Save Critic Report ---
        try:
            scene = state["scene_spec"]
            vis_try = state.get("visual_retries", 0)
            
            critic_dir = settings.OUTPUT_DIR / "critic"
            critic_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{scene.scene_id}_critic_v{vis_try}.txt"
            content = f"Passed: {feedback.passed}\nScore: {feedback.score}\nEvidence: {feedback.suggestion}"
            
            with open(critic_dir / filename, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.warning(f"Failed to save critic report: {e}")

        visual_evidence = feedback.suggestion if feedback.suggestion else "Visual check failed."

        if feedback.passed:
            return {"critic_feedback": None}
        else:
            return {"critic_feedback": visual_evidence}

    # --- Node 7: Finalizer ---
    async def node_finalize(self, state: GraphState) -> Dict[str, Any]:
        """
        [重要] 子图结束节点。
        将单数 artifact 转换为列表 output_artifacts，以便父图 reducer 合并。
        """
        art = state.get("artifact")
        if art:
            # 记录成功指标
            metrics.log_scene_finish(
                state["scene_spec"].scene_id, True, 
                state.get("retries",0), state.get("visual_retries",0)
            )
            return {"output_artifacts": [art]}
        else:
            # 失败记录
            metrics.log_scene_finish(
                state["scene_spec"].scene_id, False, 0, 0
            )
            return {"output_artifacts": []} # 返回空列表

    # --- Routing ---
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

    def edge_router_after_render(self, state: GraphState) -> Literal["critic", "finalize", "fixer"]:
        if state.get("error_log"):
            return "fixer"
        if state.get("visual_retries", 0) >= self.MAX_VISUAL_RETRIES:
            return "finalize"
        return "critic"

    def edge_router_after_critic(self, state: GraphState) -> Literal["finalize", "fixer"]:
        if state.get("critic_feedback") is None:
            return "finalize"
        if state.get("visual_retries", 0) >= self.MAX_VISUAL_RETRIES:
            return "finalize"
        return "fixer"

    def edge_router_after_fixer(self, state: GraphState) -> Literal["prep_syn", "prep_vis"]:
        if state.get("critic_feedback"):
            return "prep_vis"
        return "prep_syn"

    def compile(self):
        workflow = StateGraph(GraphState)
        
        workflow.add_node("tts", self.node_tts)
        workflow.add_node("plan", self.node_plan_layout)
        workflow.add_node("generate", self.node_generate_code)
        workflow.add_node("lint", self.node_check_syntax)
        workflow.add_node("render", self.node_render)
        workflow.add_node("critic", self.node_critic)
        workflow.add_node("fixer", self.node_analyze_error)
        workflow.add_node("prep_syn", self.node_prep_syntax_retry)
        workflow.add_node("prep_vis", self.node_prep_visual_retry)
        workflow.add_node("finalize", self.node_finalize)
        workflow.add_node("failed", self.node_finalize) # 失败也走 finalize，返回空列表

        # Flow
        workflow.set_entry_point("tts")
        workflow.add_edge("tts", "plan")
        workflow.add_edge("plan", "generate")
        workflow.add_edge("generate", "lint")
        
        workflow.add_conditional_edges("lint", self.edge_router_after_lint, 
                                       {"render": "render", "fixer": "fixer", "failed": "failed"})
        
        workflow.add_conditional_edges("render", self.edge_router_after_render, 
                                       {"critic": "critic", "fixer": "fixer", "finalize": "finalize"})
        
        workflow.add_conditional_edges("critic", self.edge_router_after_critic, 
                                       {"finalize": "finalize", "fixer": "fixer"})
        
        workflow.add_conditional_edges("fixer", self.edge_router_after_fixer, 
                                       {"prep_syn": "prep_syn", "prep_vis": "prep_vis"})
        
        workflow.add_edge("prep_syn", "generate")
        workflow.add_edge("prep_vis", "generate")
        workflow.add_edge("finalize", END)
        workflow.add_edge("failed", END)

        return workflow.compile()

class ParallelManimFlow:
    """
    总控图：负责 Map (分发场景) 和 Reduce (收集结果)
    """
    def __init__(self):
        # 编译单场景子图
        self.scene_graph = ManimGraph().compile()

    def map_scenes(self, state: AggregateState):
        """
        Mapper: 将 scenes 列表转换为并行的 Send 任务
        """
        # [Debug] 打印 state，确认 scenes 是否存在
        # print(f"DEBUG: Mapping scenes: {len(state.get('scenes', []))}")
        
        tasks = []
        for scene in state["scenes"]:
            # 构建完整的 GraphState 初始值
            # 必须包含 GraphState 所有的 Required 字段
            # Optional 字段可以设为 None
            initial_scene_state: GraphState = {
                "scene_spec": scene,
                "retries": 0,
                "visual_retries": 0,
                "code": None,
                "error_log": None,
                "critic_feedback": None,
                "layout_plan": None,
                "fix_instructions": None,
                "artifact": None,
                "output_artifacts": []
            }
            tasks.append(Send("process_scene", initial_scene_state))
        return tasks

    def compile(self):
        workflow = StateGraph(AggregateState)

        # 添加处理节点的子图
        workflow.add_node("process_scene", self.scene_graph)

        # 设置入口，使用 map_scenes 进行动态扇出
        workflow.add_conditional_edges(START, self.map_scenes)
        
        # 所有 process_scene 完成后，Reducer 会自动工作，直接结束
        workflow.add_edge("process_scene", END)

        return workflow.compile()