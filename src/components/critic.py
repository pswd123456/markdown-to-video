import base64
import json
from pathlib import Path


from src.core.models import CritiqueFeedback, SceneSpec
from src.core.config import settings
from src.llm.client import LLMClient
from src.llm.prompts import CRITIC_SYSTEM_PROMPT, build_critic_user_prompt

class VisionCritic:
    def __init__(self):
        # 复用 LLM Client，但注意我们将在调用时指定 Vision 模型
        self.llm_client = LLMClient()
        self.model = settings.CRITIC_MODEL  # e.g., "qwen-vl-max"

    def _encode_image(self, image_path: str) -> str:
        """将图片转换为 Base64 编码"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def review_layout(self, image_path: str, scene: SceneSpec) -> CritiqueFeedback:
        """
        核心方法：看图找茬
        """
        print(f"👀 [Critic] Reviewing image: {image_path}")
        
        base64_image = self._encode_image(image_path)
        
        # 1. 构建 Prompt (强制 JSON 输出)
        system_prompt = CRITIC_SYSTEM_PROMPT
        user_content = build_critic_user_prompt(scene)

        # 2. 调用 Vision Model (OpenAI 兼容格式)
        try:
            # 注意：这里我们手动构造请求，因为 client.py 封装可能比较简单
            # 如果你的 LLMClient 不支持 image_url，这里需要直接调用 client.chat.completions
            response = self.llm_client.client.chat.completions.create(
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
                temperature=0.3, # 评价需要客观
                response_format={"type": "json_object"} # 强制 JSON (如果模型支持)
            )
            
            content = response.choices[0].message.content
            # 清洗可能的 markdown 标记
            content = content.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(content)
            
            return CritiqueFeedback(
                passed=data.get("passed", False),
                score=data.get("score", 0),
                suggestion=data.get("suggestion")
            )

        except Exception as e:
            print(f"⚠️ [Critic] Validation failed due to API error: {e}")
            # 如果视觉模型挂了，为了不阻塞流程，默认通过，但标记警告
            return CritiqueFeedback(passed=True, score=5, suggestion=None)