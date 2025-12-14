import subprocess
import shutil
import os
import asyncio
from pathlib import Path
from typing import Optional
import uuid

from src.core.models import RenderArtifact
from src.core.config import settings

class RenderError(Exception):
    pass

class ManimRunner:
    # 全局并发信号量，限制同时运行的 Docker 容器数量
    # 避免 CPU/内存 爆炸
    _semaphore = asyncio.Semaphore(2) 

    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.docker_image = settings.DOCKER_IMAGE
        self._check_docker_availability()

    def _check_docker_availability(self):
        try:
            subprocess.run(["docker", "--version"], check=True, stdout=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("❌ Docker 未安装或未启动，无法使用 ManimRunner。")

    async def render_async(self, code: str, scene_id: str, quality: str = "l") -> RenderArtifact:
        """
        [Async] 异步渲染入口，带有并发限制
        """
        async with self._semaphore:
            # 将阻塞的同步渲染逻辑放到线程池中运行，避免阻塞 asyncio 事件循环
            return await asyncio.to_thread(self.render_sync, code, scene_id, quality)

    def render_sync(self, code: str, scene_id: str, quality: str = "l") -> RenderArtifact:
        """
        原有的同步渲染逻辑 (阻塞)
        """
        session_id = str(uuid.uuid4())[:8]
        temp_dir = self.output_dir / "temp" / f"{scene_id}_{session_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            os.chmod(str(temp_dir), 0o777)
        except Exception as e:
            pass

        script_path = temp_dir / "scene.py"
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "-v", f"{temp_dir.absolute()}:/manim/input",
            "-v", f"{temp_dir.absolute()}:/manim/output",
            self.docker_image,
            "manim",
            "/manim/input/scene.py",
            "-q" + quality,
            "--media_dir", "/manim/output",
            "--disable_caching"
        ]

        print(f"🎬 [ManimRunner] Starting render for {scene_id}...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.DOCKER_TIMEOUT + 60
            )

            if result.returncode != 0:
                error_msg = self._parse_manim_error(result.stderr)
                raise RenderError(f"Manim Failed:\n{error_msg}")

            video_path = self._find_file(temp_dir, ".mp4")
            if not video_path:
                raise RenderError("Render finished but no MP4 file found.")

            raw_clips_dir = self.output_dir / "raw_video_clips"
            raw_clips_dir.mkdir(parents=True, exist_ok=True)
            final_video_path = raw_clips_dir / f"{scene_id}.mp4"
            shutil.move(str(video_path), str(final_video_path))

            img_dir = self.output_dir / "picture"
            img_dir.mkdir(parents=True, exist_ok=True)
            final_image_path = img_dir / f"{scene_id}.png"

            try:
                subprocess.run([
                    "ffmpeg", "-y", 
                    "-sseof", "-1",
                    "-i", str(final_video_path), 
                    "-update", "1", 
                    "-q:v", "2", 
                    str(final_image_path)
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"⚠️ Warning: Failed to extract frame: {e}")
                final_image_path = "N/A"

            shutil.rmtree(temp_dir, ignore_errors=True)

            return RenderArtifact(
                scene_id=scene_id,
                video_path=str(final_video_path),
                last_frame_path=str(final_image_path),
                code_content=code
            )

        except TimeoutError:
            raise RenderError("Render Timed Out (Docker container killed).")
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RenderError(f"System Error: {str(e)}")

    def _find_file(self, root_dir: Path, extension: str) -> Optional[Path]:
        for path in root_dir.rglob(f"*{extension}"):
            return path
        return None

    def _parse_manim_error(self, stderr: str) -> str:
        lines = stderr.split('\n')
        return "\n".join(lines[-10:])