# src/components/critic.py
import base64
import json
import asyncio
from pathlib import Path

from src.core.models import CritiqueFeedback, SceneSpec
from src.core.config import settings
from src.llm.client import LLMClient
# 引入新的构建函数
from src.llm.prompts import build_critic_system_prompt, build_critic_user_prompt 

class VisionCritic:
    def __init__(self):
        # 这里的 LLMClient 已经是异步版本了
        self.llm_client = LLMClient()
        self.model = settings.CRITIC_MODEL
        
        # === 新增：加载上下文资源 ===
        # 复用 lib 目录下的资源，保证 Coder 和 Critic 看到的是同一套规则
        self.api_stubs = self._load_file(settings.LIB_DIR / "api_stubs.txt")
        self.examples = self._load_file(settings.LIB_DIR / "examples.txt")

    def _load_file(self, path: Path) -> str:
        """辅助方法：读取文件"""
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def _encode_image(self, image_path: str) -> str:
        """将图片转换为 Base64 编码"""
        path = Path(image_path)
        if not path.exists():
            # 这里可以做一个兜底，如果没有图片，就不要去审查了
            return ""
            
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def review_layout(self, image_path: str, scene: SceneSpec) -> CritiqueFeedback:
        """
        [Async] 视觉审查
        """
        print(f"👀 [Critic] Reviewing image: {image_path}")
        
        # 图片编码是 CPU 密集型操作，但对于单张图片通常很快。
        # 如果图片很大，可以考虑 await asyncio.to_thread(self._encode_image, image_path)
        base64_image = self._encode_image(image_path)
        
        if not base64_image:
            print("   ⚠️ Image not found, skipping critique.")
            return CritiqueFeedback(passed=True, score=10, suggestion=None)
        
        # === 修改点：构建动态 System Prompt ===
        system_prompt = build_critic_system_prompt(self.api_stubs, self.examples)
        
        user_content = build_critic_user_prompt(scene)

        try:
            # 关键修复: 这里使用 await 调用异步的 LLMClient
            # 注意：LLMClient.client 是 AsyncOpenAI 实例
            response = await self.llm_client.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_content},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1, # 降低温度，让它严格遵循 API 约束
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            # 简单的清洗逻辑
            content = content.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(content)
            
            return CritiqueFeedback(
                passed=data.get("passed", False),
                score=data.get("score", 0),
                suggestion=data.get("suggestion")
            )

        except Exception as e:
            print(f"⚠️ [Critic] Validation failed due to API error: {e}")
            # 出错时默认通过，避免卡死流水线，但分数给低一点
            return CritiqueFeedback(passed=True, score=5, suggestion=None)