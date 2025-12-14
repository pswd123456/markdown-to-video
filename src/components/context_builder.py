from pathlib import Path
from src.core.models import CodeGenerationRequest
from src.core.config import settings
from src.llm.prompts import build_code_system_prompt, build_code_user_prompt

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
        return build_code_system_prompt(self.api_stubs, self.examples)

    def build_user_prompt(self, request: CodeGenerationRequest) -> str:
        """构建 User Prompt：包含具体需求和（可能的）错误修正上下文"""
        return build_code_user_prompt(request)