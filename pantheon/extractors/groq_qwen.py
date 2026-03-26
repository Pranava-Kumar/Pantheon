from langchain_openai import ChatOpenAI
from extractors.base import CascadingExtractor
from config.settings import settings

_FALLBACK_CHAIN = [
    ("qwen-2.5-32b",      "groq"),
    ("mixtral-8x7b-32768", "groq"),
]

class GroqQwenExtractor(CascadingExtractor):
    model_id = "groq_qwen"

    def __init__(self):
        super().__init__()
        for model_name, provider in _FALLBACK_CHAIN:
            self._models.append((
                model_name,
                ChatOpenAI(
                    model=model_name,
                    base_url="https://api.groq.com/openai/v1",
                    api_key=settings.GROQ_API_KEY,
                    temperature=0.1,
                    max_tokens=600
                )
            ))
        self._failures = [0] * len(self._models)
