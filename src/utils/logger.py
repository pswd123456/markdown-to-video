import logging
import json
from datetime import datetime
from typing import Dict, Any

from src.core.config import settings

# 配置基础 Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(settings.OUTPUT_DIR / "pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AutoManim")

class MetricsTracker:
    """
    单例模式，用于跟踪整个 Session 的消耗
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsTracker, cls).__new__(cls)
            cls._instance.reset()
        return cls._instance

    def reset(self):
        self.total_scenes = 0
        self.successful_scenes = 0
        self.total_cost_tokens = 0 # 估算
        self.syntax_retries = 0
        self.visual_retries = 0
        self.start_time = datetime.now()
        self.scene_metrics: Dict[str, Any] = {}

    def log_scene_finish(self, scene_id: str, success: bool, retries: int, vis_retries: int):
        self.total_scenes += 1
        if success:
            self.successful_scenes += 1
        self.syntax_retries += retries
        self.visual_retries += vis_retries
        
        self.scene_metrics[scene_id] = {
            "success": success,
            "syntax_retries": retries,
            "visual_retries": vis_retries
        }

    def print_summary(self):
        duration = datetime.now() - self.start_time
        logger.info("\n" + "="*40)
        logger.info(f"📊 EXECUTION SUMMARY (Duration: {duration})")
        logger.info(f"   Success Rate: {self.successful_scenes}/{self.total_scenes}")
        logger.info(f"   Total Syntax Retries (Linter): {self.syntax_retries}")
        logger.info(f"   Total Visual Retries (Critic): {self.visual_retries}")
        logger.info("="*40 + "\n")

    def save_report(self):
        report_path = settings.OUTPUT_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(self.scene_metrics, f, indent=2)
        logger.info(f"📝 Metrics report saved to: {report_path}")

metrics = MetricsTracker()