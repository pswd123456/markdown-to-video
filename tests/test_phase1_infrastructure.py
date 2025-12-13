import sys
from pathlib import Path

# 将 src 加入路径以便导入
sys.path.append(str(Path(__file__).parent.parent))

from src.core.models import SceneSpec, CodeGenerationRequest
from src.core.config import settings

def test_infrastructure():
    print(f"当前时间: 2025-12-14")
    print(f"项目根目录: {settings.OUTPUT_DIR}")

    # 1. 测试 SceneSpec 校验
    try:
        scene = SceneSpec(
            scene_id="scene_001",
            description="演示数据库连接",
            duration=5.0,
            elements=["DB", "App"],
            audio_script="用户连接到数据库。"
        )
        print("✅ SceneSpec 模型校验通过")
    except Exception as e:
        print(f"❌ SceneSpec 校验失败: {e}")

    # 2. 测试 Request 组装
    req = CodeGenerationRequest(
        scene=scene,
        previous_code="class MyScene(Scene): pass",
        feedback_context="SyntaxError: line 1"
    )
    
    if req.is_retry:
        print("✅ Retry 逻辑判定正确")
    else:
        print("❌ Retry 逻辑判定错误")

    print("\n阶段一基建验证完成。")

if __name__ == "__main__":
    test_infrastructure()