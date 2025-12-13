import subprocess
import os
from pathlib import Path
from typing import List
from src.core.models import RenderArtifact
from src.utils.logger import logger
from src.core.config import settings

class Assembler:
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.output_dir.mkdir(exist_ok=True)

    def assemble(self, artifacts: List[RenderArtifact], audio_paths: List[str], output_filename: str = "final_movie.mp4") -> str:
        logger.info("🎞️ [Assembler] Starting assembly...")
        
        concat_list_path = self.output_dir / "concat_list.txt"
        segment_paths = []
        
        for i, (art, audio) in enumerate(zip(artifacts, audio_paths)):
            if not art or not Path(art.video_path).exists():
                continue
            
            segment_out = self.output_dir / f"segment_{i:03d}.mp4"
            
            # === 步骤 A: 准备音频 (清洗为 WAV 以保证兼容性) ===
            final_audio_input = None
            temp_wav = None # 用于标记是否生成了临时文件
            
            # 只有当文件存在且大于 100 字节时才处理
            if audio and Path(audio).exists() and os.path.getsize(audio) > 100:
                temp_wav = self.output_dir / f"temp_audio_{i}.wav"
                
                # 转为标准 WAV
                wav_cmd = [
                    "ffmpeg", "-y", "-v", "quiet",
                    "-i", str(audio),
                    "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
                    str(temp_wav)
                ]
                
                try:
                    subprocess.run(wav_cmd, check=True)
                    final_audio_input = str(temp_wav)
                except subprocess.CalledProcessError:
                    logger.warning(f"   ⚠️ Audio cleaning failed for segment {i}, using original.")
                    final_audio_input = str(audio)
            
            # === 步骤 B: Muxing (合并) ===
            cmd = [
                "ffmpeg", "-y", "-v", "error", # 减少日志输出，只显示错误
                "-i", str(art.video_path)
            ]
            
            if final_audio_input:
                cmd.extend(["-i", final_audio_input])
                cmd.extend([
                    "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest"
                ])
            else:
                # 无音频，生成静音
                cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-an"])

            cmd.append(str(segment_out))
            
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                segment_paths.append(str(segment_out))
                logger.info(f"   ✅ Segment {i} assembled.")
                
                # === 修正 Debug 逻辑: 立即删除临时 WAV ===
                if temp_wav and temp_wav.exists():
                    temp_wav.unlink()
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"   ❌ Failed to mux segment {i}: {e.stderr.decode()}")
                continue

        if not segment_paths:
            raise ValueError("No valid segments created.")

        # === 步骤 C: Concat (拼接) ===
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for path in segment_paths:
                f.write(f"file '{Path(path).resolve()}'\n")
        
        output_path = self.output_dir / output_filename
        concat_cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list_path),
            "-c", "copy", str(output_path)
        ]
        
        subprocess.run(concat_cmd, check=True)
        logger.info(f"✨ Final video saved to: {output_path}")
        
        # 可选：清理中间生成的 segment_xxx.mp4 和列表文件
        # for p in segment_paths: Path(p).unlink(missing_ok=True)
        # concat_list_path.unlink(missing_ok=True)
        
        return str(output_path)