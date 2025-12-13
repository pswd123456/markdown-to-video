import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.components.linter import CodeLinter

def test_linter():
    linter = CodeLinter()
    print("=== 开始 Linter 模块测试 ===\n")

    # Case 1: 完美代码
    good_code = """
from manim import *

class GoodScene(Scene):
    def construct(self):
        c = Circle()
        self.play(Create(c))
"""
    print(f"Testing Good Code...")
    res = linter.validate(good_code)
    if res.passed:
        print("✅ Passed (Expected)")
    else:
        print(f"❌ Failed: {res.traceback}")

    # Case 2: 语法错误 (缺少冒号)
    syntax_error_code = """
from manim import *
class BadSyntax(Scene)  # Missing colon
    def construct(self):
        pass
"""
    print(f"\nTesting Syntax Error...")
    res = linter.validate(syntax_error_code)
    if not res.passed and res.error_type == "SYNTAX":
        print(f"✅ Caught Syntax Error: {res.traceback.splitlines()[0]}")
    else:
        print(f"❌ Failed to catch syntax error")

    # Case 3: 运行时错误 (变量未定义)
    # 这种错误 AST 查不出来，必须 Dry Run 才能查出
    runtime_error_code = """
from manim import *
class BadRuntime(Scene):
    def construct(self):
        # 'Square' is valid, but 'CircleXYZ' does not exist
        s = Square() 
        self.add(CircleXYZ) 
"""
    print(f"\nTesting Runtime Error (Dry Run)...")
    res = linter.validate(runtime_error_code)
    if not res.passed and res.error_type == "RUNTIME":
        print(f"✅ Caught Runtime Error.")
        print(f"   Traceback Preview: {res.traceback[:100]}...")
    else:
        print(f"❌ Failed to catch runtime error. Result: {res}")

if __name__ == "__main__":
    test_linter()