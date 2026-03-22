from langchain_openai import ChatOpenAI
from extractors.base import BaseExtractor
from config.settings import settings

class GeminiProExtractor(BaseExtractor):
    model_id = "gemini_pro"

    def __init__(self):
        self._model = ChatOpenAI(
            model="openrouter/auto",
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
            temperature=0.1,
            max_tokens=1024
        )

    async def _call_model(self, prompt: str) -> str:
        response = await self._model.ainvoke(prompt)
        return response.content
