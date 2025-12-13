import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.components.renderer import ManimRunner
from src.core.config import settings

def test_renderer():
    print("=== 开始 Renderer 模块测试 ===")
    
    # 临时覆盖配置，使用刚才 build 的镜像名
    settings.DOCKER_IMAGE = "auto-manim-runner:v1"
    
    runner = ManimRunner()
    
    # 一个极简的 Manim 场景
    # 注意：这里我们故意写一个能跑通的代码
    test_code = """
from manim import *

class TestCircle(Scene):
    def construct(self):
        c = Circle(color=RED)
        t = Text("Docker Test").next_to(c, UP)
        self.add(c, t)
        self.wait(1)
"""
    
    scene_id = "test_docker_001"
    
    try:
        print(f"🚀 发送渲染任务: {scene_id} (Quality: Low)")
        artifact = runner.render(test_code, scene_id, quality="l")
        
        print("\n✅ 渲染成功!")
        print(f"   Video: {artifact.video_path}")
        print(f"   Image: {artifact.last_frame_path}")
        
        # 验证文件是否真的存在
        if Path(artifact.video_path).exists():
            print("   [File Check] Video exists on disk.")
        else:
            print("   [File Check] ❌ Video file missing!")

    except Exception as e:
        print(f"\n❌ 渲染失败: {e}")

if __name__ == "__main__":
    test_renderer()