import dashscope
import requests
import subprocess
from pathlib import Path
from src.core.config import settings
from src.utils.logger import logger

class TTSEngine:
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置 DashScope
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
        
        # 使用 Qwen TTS 模型
        self.model = "qwen3-tts-flash" 
        self.voice = "Cherry"

    def get_duration(self, audio_path: str) -> float:
        """获取音频时长(秒)"""
        if not audio_path or not Path(audio_path).exists():
            return 0.0
            
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            audio_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            val = result.stdout.strip()
            return float(val) if val else 0.0
        except Exception as e:
            logger.error(f"⚠️ Failed to get duration for {audio_path}: {e}")
            return 0.0

    def generate(self, text: str, scene_id: str) -> str:
        """
        生成音频文件，返回路径
        """
        file_path = self.output_dir / f"{scene_id}.mp3"
        
        if file_path.exists():
            logger.info(f"🔊 [TTS] Using cached audio for {scene_id}")
            return str(file_path)

        logger.info(f"🔊 [TTS] Generating audio for {scene_id} (DashScope Qwen)...")
        try:
            # 尝试使用 MultiModalConversation (Refer to apiexample)
            response = dashscope.MultiModalConversation.call(
                model=self.model,
                api_key=settings.DASHSCOPE_API_KEY,
                text=text,
                voice=self.voice,
                language_type="Chinese"
            )
            
            # Check for success
            if response.status_code == 200:
                output = response.output
                # Need to handle output safely as it could be object or dict depending on SDK version
                # Based on example output:
                # "output": { "audio": { "url": "..." } }
                
                audio_info = None
                if isinstance(output, dict):
                    audio_info = output.get('audio')
                else:
                    audio_info = getattr(output, 'audio', None)
                
                audio_url = None
                if audio_info:
                    if isinstance(audio_info, dict):
                        audio_url = audio_info.get('url')
                    else:
                        audio_url = getattr(audio_info, 'url', None)

                if audio_url:
                    logger.info(f"🔊 [TTS] Downloading audio from {audio_url}")
                    resp = requests.get(audio_url)
                    resp.raise_for_status()
                    with open(file_path, 'wb') as f:
                        f.write(resp.content)
                    return str(file_path)
                else:
                     logger.error(f"⚠️ [TTS] Audio URL not found in response: {response}")
                     return ""

            logger.error(f"⚠️ [TTS] DashScope Failed: {response.message}")
            return ""
                
        except Exception as e:
            logger.error(f"⚠️ [TTS] DashScope Exception: {e}")
            return ""
