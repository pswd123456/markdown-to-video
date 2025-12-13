import ast
import subprocess
import tempfile
import sys
import os
from pathlib import Path
from typing import Tuple

from src.core.models import LintResult, ErrorType
from src.utils.code_ops import extract_code

class CodeLinter:
    def __init__(self):
        # 预设一些为了安全或性能需要屏蔽的关键词（可选）
        self.forbidden_imports = ["os.system", "subprocess", "eval", "exec"]

    def validate(self, raw_text: str) -> LintResult:
        """
        主入口：清洗代码 -> AST检查 -> Dry Run
        """
        code = extract_code(raw_text)

        # Level 1: AST Syntax Check
        syntax_result = self._check_syntax(code)
        if not syntax_result.passed:
            return syntax_result

        # Level 2: Runtime Dry Run (Manim simulation)
        return self._dry_run(code)

    def _check_syntax(self, code: str) -> LintResult:
        """使用 Python 内置 AST 模块进行静态分析"""
        try:
            tree = ast.parse(code)
            
            # 简单的安全性扫描 (可选)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    # 这里可以加入对非法库的检查逻辑
                    pass
                    
            return LintResult(passed=True)
            
        except SyntaxError as e:
            return LintResult(
                passed=False,
                error_type=ErrorType.SYNTAX,
                line_number=e.lineno,
                traceback=f"SyntaxError: {e.msg} at line {e.lineno}\n{e.text}"
            )

    def _dry_run(self, code: str) -> LintResult:
        """
        在子进程中执行 Manim 的 Dry Run 模式。
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            script_path = temp_path / "scene_check.py"
            
            tex_dir = temp_path / "media" / "Tex"
            tex_dir.mkdir(parents=True, exist_ok=True)
            
            (temp_path / "media" / "texts").mkdir(parents=True, exist_ok=True)
            # --- 【修复结束】 ---

            # 写入用户代码
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 构造 Manim 命令
            # 显式指定 --media_dir 为当前临时目录，防止它去系统其他地方乱写
            cmd = [
                sys.executable, "-m", "manim", 
                str(script_path), 
                "-ql", 
                "--dry_run", 
                "--disable_caching",
                "--media_dir", str(temp_path / "media") # 显式指定输出路径
            ]

            try:
                # 运行子进程，设置超时防止死循环 (e.g. while True)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30, # 30秒超时熔断
                    cwd=temp_dir
                )

                if result.returncode == 0:
                    return LintResult(passed=True)
                else:
                    # 提取 stderr 中的关键报错信息
                    cleaned_tb = self._clean_traceback(result.stderr)
                    return LintResult(
                        passed=False,
                        error_type=ErrorType.RUNTIME,
                        traceback=cleaned_tb
                    )

            except TimeoutError:  # 直接捕获内置异常
                return LintResult(
                    passed=False,
                    error_type=ErrorType.RUNTIME,
                    traceback="TimeoutError: Code execution exceeded 30 seconds."
                )
            except Exception as e:
                return LintResult(
                    passed=False,
                    error_type=ErrorType.RUNTIME,
                    traceback=f"System Error: {str(e)}"
                )

    def _clean_traceback(self, stderr: str) -> str:
        """
        清洗 Manim 冗长的报错信息，只保留最后 10 行关键堆栈。
        这也是 'Context Injection' 的一部分：不要给 LLM 发送几千行的日志。
        """
        lines = stderr.split('\n')
        # 过滤掉 Manim 的常规 INFO 日志
        error_lines = [line for line in lines if "INFO" not in line]
        
        # 截取最后 15 行，通常包含 Traceback 的核心
        keep_lines = error_lines[-15:]
        return "\n".join(keep_lines).strip()