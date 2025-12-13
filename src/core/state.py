from typing import TypedDict, Optional
from src.core.models import SceneSpec, RenderArtifact

class GraphState(TypedDict):
    """
    LangGraph 的状态对象。
    LangGraph 会在节点间自动传递和更新这个字典。
    """
    # --- 输入数据 ---
    scene_spec: SceneSpec
    
    # --- 中间状态 ---
    code: Optional[str]         # 当前生成的 Python 代码
    error_log: Optional[str]    # Linter 报错或 Runtime 报错
    retries: int                # 当前尝试次数 (0-based)
    
    # --- 最终产物 ---
    artifact: Optional[RenderArtifact]