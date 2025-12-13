import asyncio
import edge_tts
from pathlib import Path
from src.core.config import settings
from src.utils.logger import logger

class TTSEngine:
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 使用微软著名的中文语音包 "Yunxi" (男声) 或 "Xiaoxiao" (女声)
        self.voice = "zh-CN-YunxiNeural" 

    async def _generate_async(self, text: str, file_path: Path):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(file_path))

    def generate(self, text: str, scene_id: str) -> str:
        """
        生成音频文件，返回路径
        (Edge-TTS 是异步库，这里封装成同步调用方便主程序使用)
        """
        file_path = self.output_dir / f"{scene_id}.mp3"
        
        if file_path.exists():
            logger.info(f"🔊 [TTS] Using cached audio for {scene_id}")
            return str(file_path)

        logger.info(f"🔊 [TTS] Generating audio for {scene_id} (Edge-TTS)...")
        try:
            # 在同步函数中运行异步代码
            asyncio.run(self._generate_async(text, file_path))
            return str(file_path)
        except Exception as e:
            logger.error(f"⚠️ [TTS] Edge-TTS Failed: {e}")
            # 极简回退：生成空文件避免报错，或者抛出异常
            return ""