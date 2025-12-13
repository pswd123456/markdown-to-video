from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录定位 (假设当前文件在 src/core/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # LLM Configuration
    DASHSCOPE_API_KEY: str
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    CODER_MODEL: str = "qwen3-coder-plus"     # 写代码的模型
    CRITIC_MODEL: str = "qwen-vl-max"         # 看图的模型 (Vision)
    REWRITER_MODEL: str = "qwen-plus"

    # Paths
    LIB_DIR: Path = BASE_DIR / "lib"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    
    # Docker Configuration (For Phase 3)
    DOCKER_IMAGE: str = "manimcommunity/manim:v0.19.0"
    DOCKER_TIMEOUT: int = 60 # 秒

    # Manim Defaults
    VIDEO_WIDTH: int = 1920
    VIDEO_HEIGHT: int = 1080
    
    # Pydantic Settings Config
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # 忽略多余的环境变量
    )

# 单例模式实例化
settings = Settings()

# 确保输出目录存在
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)