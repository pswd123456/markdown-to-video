from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

# --- Enums (为了更好的类型安全) ---

class ErrorType(str, Enum):
    SYNTAX = "SYNTAX"     # 语法错误 (AST解析失败)
    IMPORT = "IMPORT"     # 引用了不存在的库/类
    RUNTIME = "RUNTIME"   # Dry Run 时的运行时错误
    NONE = "NONE"         # 无错误

class SceneType(str, Enum):
    DYNAMIC = "dynamic"   # Manim 动态视频
    STATIC = "static"     # Marp 静态幻灯片 (Future)

# --- Data Models ---

class SceneSpec(BaseModel):
    """
    [输入] 描述一个视频场景的元数据
    通常由 Storyboard 阶段生成
    """
    scene_id: str = Field(..., description="场景唯一标识符")
    type: SceneType = Field(default=SceneType.DYNAMIC, description="场景类型: dynamic | static")
    description: str = Field(..., description="场景的自然语言描述")
    duration: float = Field(..., gt=0, description="场景持续时间(秒)")
    elements: List[str] = Field(default_factory=list, description="涉及的实体列表，如 ['Server', 'Database']")
    audio_script: str = Field(..., description="该场景对应的口播文案")

class CodeGenerationRequest(BaseModel):
    """
    [交互] 发送给 Coder LLM 的请求上下文
    实现了 Context Injection 的载体
    """
    scene: SceneSpec
    previous_code: Optional[str] = Field(None, description="上一轮生成的代码(如果有)")
    feedback_context: Optional[str] = Field(None, description="Linter 报错信息或 Critic 的视觉修改建议")

    @property
    def is_retry(self) -> bool:
        """判断当前是否为重试模式"""
        return self.previous_code is not None and self.feedback_context is not None

class LintResult(BaseModel):
    """
    [反馈] Linter 的静态检查结果
    对应文档中的 'Fail-Fast Loop'
    """
    passed: bool
    error_type: ErrorType = Field(default=ErrorType.NONE)
    traceback: Optional[str] = Field(None, description="清洗后的关键错误堆栈，用于反馈给 LLM")
    line_number: Optional[int] = Field(None, description="报错行号")

class CritiqueFeedback(BaseModel):
    """
    [反馈] Vision Critic 的视觉审查结果
    对应文档中的 'Semantic Correction'
    """
    passed: bool
    score: int = Field(..., ge=0, le=10, description="视觉评分 0-10")
    suggestion: Optional[str] = Field(
        None, 
        description="语义化修改建议 (e.g., 'Use next_to instead of shift')"
    )

class RenderArtifact(BaseModel):
    """
    [产物] 最终渲染输出
    """
    video_path: str
    last_frame_path: str
    code_content: str
    scene_id: str