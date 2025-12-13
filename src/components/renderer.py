import subprocess
import shutil
import os
from pathlib import Path
from typing import Optional
import uuid

from src.core.models import RenderArtifact
from src.core.config import settings

class RenderError(Exception):
    """渲染过程中的自定义异常"""
    pass

class ManimRunner:
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.docker_image = settings.DOCKER_IMAGE # e.g., "auto-manim-runner:v1"
        
        # 确保 Docker 守护进程在运行 (简单的连通性检查)
        self._check_docker_availability()

    def _check_docker_availability(self):
        """检查 Docker 是否可用"""
        try:
            subprocess.run(["docker", "--version"], check=True, stdout=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("❌ Docker 未安装或未启动，无法使用 ManimRunner。")

    def render(self, code: str, scene_id: str, quality: str = "l") -> RenderArtifact:
        """
        核心渲染方法
        :param quality: 'l' (480p), 'm' (720p), 'h' (1080p)
        """
        # 1. 准备唯一的临时目录 (作为宿主机与容器的交换空间)
        # 使用 UUID 防止并发冲突
        session_id = str(uuid.uuid4())[:8]
        temp_dir = self.output_dir / "temp" / f"{scene_id}_{session_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        script_path = temp_dir / "scene.py"
        
        # 2. 写入代码文件
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        # 3. 构造 Docker 命令
        # -v: 挂载目录 (Host Path : Container Path)
        # -ql: quality low
        # --disable_caching: 避免旧缓存干扰
        # -o: 指定输出文件名
        
        video_filename = f"{scene_id}.mp4"
        
        # Manim 默认会在 media/videos/scene/quality/ 目录下生成
        # 我们这里使用 Docker 的工作流，让它输出到挂载的 /manim/output
        cmd = [
            "docker", "run", "--rm",
            "--network", "none",  # 【安全】禁止联网，防范恶意代码上传数据
            "-v", f"{temp_dir.absolute()}:/manim/input",   # 输入代码
            "-v", f"{temp_dir.absolute()}:/manim/output",  # 输出视频
            self.docker_image,
            "manim",
            "/manim/input/scene.py", # 容器内的脚本路径
            # 注意：这里假设用户生成的类名未知，但 Manim 支持渲染文件中的所有 Scene
            # 如果需要指定类名，需要从 AST 解析出来，这里使用 -a (all scenes) 或默认自动检测
            "-q" + quality,
            "--media_dir", "/manim/output", # 强制输出到挂载点
            "--disable_caching"
        ]

        print(f"🎬 [ManimRunner] Starting render for {scene_id} in Docker...")
        
        try:
            # 4. 执行渲染 (设置 120秒 超时)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.DOCKER_TIMEOUT + 60 # 给 Docker 启动留点余量
            )

            if result.returncode != 0:
                error_msg = self._parse_manim_error(result.stderr)
                raise RenderError(f"Manim Failed:\n{error_msg}")

            # 5. 产物提取与整理
            # Manim 的输出目录结构比较深，通常是 /manim/output/videos/scene/quality/Snippet.mp4
            # 我们需要递归查找生成的 .mp4 文件
            video_path = self._find_file(temp_dir, ".mp4")
            image_path = self._find_file(temp_dir, ".png") # 最后一帧通常会自动生成，或需添加 -s 参数

            if not video_path:
                raise RenderError("Render finished but no MP4 file found.")

            # 将产物移动到最终的 artifacts 目录，不再保留在 temp
            final_video_path = self.output_dir / f"{scene_id}.mp4"
            final_image_path = self.output_dir / f"{scene_id}.png"
            
            shutil.move(str(video_path), str(final_video_path))
            if image_path:
                shutil.move(str(image_path), str(final_image_path))
            else:
                # 如果没有图片，尝试用 ffmpeg 截取最后一帧 (可选优化)
                final_image_path = "N/A"

            # 6. 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

            return RenderArtifact(
                scene_id=scene_id,
                video_path=str(final_video_path),
                last_frame_path=str(final_image_path),
                code_content=code
            )

        except subprocess.TimeoutError:
            raise RenderError("Render Timed Out (Docker container killed).")
        except Exception as e:
            raise RenderError(f"System Error: {str(e)}")

    def _find_file(self, root_dir: Path, extension: str) -> Optional[Path]:
        """递归查找指定后缀的第一个文件"""
        for path in root_dir.rglob(f"*{extension}"):
            return path
        return None

    def _parse_manim_error(self, stderr: str) -> str:
        """提取最后几行错误信息"""
        lines = stderr.split('\n')
        return "\n".join(lines[-10:])