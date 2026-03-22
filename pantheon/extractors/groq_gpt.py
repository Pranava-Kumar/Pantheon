from langchain_openai import ChatOpenAI
from extractors.base import BaseExtractor
from config.settings import settings

class GroqGPTExtractor(BaseExtractor):
    model_id = "groq_gpt"

    def __init__(self):
        self._model = ChatOpenAI(
            model="openai/gpt-oss-120b",
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY,
            temperature=0.1,
            max_tokens=1024
        )

    async def _call_model(self, prompt: str) -> str:
        response = await self._model.ainvoke(prompt)
        return response.content
