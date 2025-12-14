import operator
from typing import TypedDict, Optional, List, Annotated, Any
from src.core.models import SceneSpec, RenderArtifact

class GraphState(TypedDict):
    """
    [子图状态] 单个场景的生命周期状态
    """
    # --- 输入数据 ---
    scene_spec: SceneSpec
    
    # --- 中间状态 ---
    code: Optional[str]         # 当前生成的 Python 代码
    error_log: Optional[str]    # Linter 报错或 Runtime 报错
    retries: int                # 语法错误重试次数 (0-based)
    visual_retries: int         # 视觉修正重试次数
    critic_feedback: Optional[str] # 视觉专家的修改建议
    layout_plan: Optional[str]
    fix_instructions: Optional[str]
    
    # --- 最终产物 (单数) ---
    # 子图内部流转使用
    artifact: Optional[RenderArtifact]

    # --- 输出到父图 (复数) ---
    # 这是一个 trick: 子图结束时将 artifact 包装进这个列表
    # 父图的 reducer 会自动捕获它
    # 注意：LangGraph 的 reducer 需要确保类型匹配，Annotated[List, add] 是标准的
    output_artifacts: Annotated[List[RenderArtifact], operator.add]

class AggregateState(TypedDict):
    """
    [父图状态] 全局 Map-Reduce 状态
    """
    # 输入: 所有待处理的场景
    scenes: List[SceneSpec]
    
    # 输出: 聚合后的所有产物 (Reducer)
    output_artifacts: Annotated[List[RenderArtifact], operator.add]