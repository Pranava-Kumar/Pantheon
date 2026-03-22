from langchain_openai import ChatOpenAI
from extractors.base import BaseExtractor
from config.settings import settings

class GroqQwenExtractor(BaseExtractor):
    model_id = "groq_qwen"

    def __init__(self):
        self._model = ChatOpenAI(
            model="qwen/qwen3-32b",
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY,
            temperature=0.1,
            max_tokens=600,
            reasoning_effort="none"
        )

    async def _call_model(self, prompt: str) -> str:
        response = await self._model.ainvoke(prompt)
        return response.content
