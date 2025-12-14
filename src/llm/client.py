from openai import AsyncOpenAI
from src.core.config import settings

class LLMClient:
    def __init__(self, model: str = None):
        # 使用异步客户端 AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL
        )
        self.model = model if model else settings.CODER_MODEL

    async def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        """
        [Async] 调用大模型生成代码
        """
        return await self._call_llm(system_prompt, user_prompt, temperature=0.2)

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """
        [Async] 调用大模型生成普通文本 (如 Plan)
        """
        return await self._call_llm(system_prompt, user_prompt, temperature=0.5)

    async def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"# LLM Call Error: {str(e)}"