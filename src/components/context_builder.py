from pathlib import Path
from src.core.models import CodeGenerationRequest
from src.core.config import settings

class ContextBuilder:
    def __init__(self):
        self.api_stubs = self._load_file(settings.LIB_DIR / "api_stubs.txt")
        self.examples = self._load_file(settings.LIB_DIR / "examples.txt")

    def _load_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return f"# Warning: {path.name} not found."

    def build_system_prompt(self) -> str:
        """构建 System Prompt：定义角色和 API 约束"""
        return f"""
You are an expert Manim animation developer. 
Your goal is to write Python code using the 'manim' library to visualize the user's request.

# CONSTRAINTS
1. Output ONLY valid Python code inside ```python``` blocks.
2. The class MUST inherit from `Scene`.
3. The main logic MUST be in `construct(self)`.
4. Use `self.wait()` at the end.
5. PREFER relative positioning (next_to) over absolute coordinates.

# AVAILABLE API (Strictly follow this subset)
{self.api_stubs}

# EXAMPLES
{self.examples}
"""

    def build_user_prompt(self, request: CodeGenerationRequest) -> str:
        """构建 User Prompt：包含具体需求和（可能的）错误修正上下文"""
        
        base_prompt = f"""
# SCENE DESCRIPTION
ID: {request.scene.scene_id}
Narrative: {request.scene.audio_script}
Visual Elements: {', '.join(request.scene.elements)}
Duration: {request.scene.duration}s
"""

        # 如果是重试模式（Linter 报错了），注入错误上下文
        if request.is_retry:
            return base_prompt + f"""
# PREVIOUS ATTEMPT FAILED
The code you wrote previously had errors.
---
Previous Code:
{request.previous_code}
---
Error Log:
{request.feedback_context}
---
INSTRUCTION: Fix the code based on the error log above.
"""
        
        return base_prompt + "\nGenerate the Manim Python code for this scene."