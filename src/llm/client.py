from openai import OpenAI
from src.core.config import settings

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL
        )
        self.model = settings.CODER_MODEL # e.g., "qwen3-coder-plus"

    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        """
        调用大模型生成代码
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2, # 代码生成需要低温度以保证准确性
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            # 实际生产中应加入重试逻辑 (tenacity)
            return f"# LLM Call Error: {str(e)}"