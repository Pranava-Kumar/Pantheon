from langchain_openai import ChatOpenAI
from pantheon.extractors.base import CascadingExtractor
from pantheon.config.settings import settings

_FALLBACK_CHAIN = [
    ("llama-3.3-70b-versatile",                "groq"),
    ("meta-llama/llama-4-scout-17b-16e-instruct", "groq"),
    ("llama-3.1-8b-instant",                   "groq"),
]

class GroqLlamaExtractor(CascadingExtractor):
    model_id = "groq_llama"

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
                    max_tokens=2048
                )
            ))
        self._failures = [0] * len(self._models)
