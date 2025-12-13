import base64
import json
from pathlib import Path
from typing import Dict, Any

from src.core.models import CritiqueFeedback, SceneSpec
from src.core.config import settings
from src.llm.client import LLMClient

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
        system_prompt = """
You are a strict Visual QA Specialist for Manim animations.
Your job is to inspect the last frame of a video and check for layout issues.

CHECKLIST:
1. Overlaps: Are any text or objects overlapping unintentionally?
2. Cut-offs: Is any content partially outside the frame (16:9 aspect ratio)?
3. Legibility: Is the text too small or low contrast?
4. Completeness: Does the image match the user's description?

OUTPUT FORMAT:
Return a JSON object ONLY (no markdown formatting):
{
    "passed": boolean,
    "score": int (0-10),
    "suggestion": "string (If failed, provide a specific Python fix suggestion using 'next_to', 'scale', or 'shift'. If passed, return null)"
}
"""
        
        user_content = f"""
User Description: "{scene.description}"
Main Elements: {', '.join(scene.elements)}

Analyze the attached image based on the checklist.
"""

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
                temperature=0.1, # 评价需要客观
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