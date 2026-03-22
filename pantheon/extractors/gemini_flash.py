from langchain_google_genai import ChatGoogleGenerativeAI
from extractors.base import BaseExtractor
from config.settings import settings

class GeminiFlashExtractor(BaseExtractor):
    model_id = "gemini_flash"

    def __init__(self):
        self._model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            thinking_budget=0,
            temperature=0.1,
            max_output_tokens=1024
        )

    async def _call_model(self, prompt: str) -> str:
        response = await self._model.ainvoke(prompt)
        return response.content
