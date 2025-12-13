import dashscope
from dashscope.audio.tts import SpeechSynthesizer
from pathlib import Path
from src.core.config import settings
from src.utils.logger import logger

class TTSEngine:
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置 DashScope
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        # 使用 Qwen TTS 模型
        self.model = "qwen3-tts-flash" 
        self.voice = "Cherry"

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
            # 尝试使用 qwen-tts 专用调用方式，或者通用方式
            # 这里使用通用入口，但指定模型和声音
            result = SpeechSynthesizer.call(
                model=self.model,
                text=text,
                voice=self.voice,
                format='mp3'
            )
            
            if result.get_audio_data() is not None:
                with open(file_path, 'wb') as f:
                    f.write(result.get_audio_data())
                return str(file_path)
            else:
                logger.error(f"⚠️ [TTS] DashScope Failed: {result.message}")
                return ""
                
        except Exception as e:
            logger.error(f"⚠️ [TTS] DashScope Exception: {e}")
            return ""