"""
Primary Reasoning extractor with cascading Google AI Studio fallback.

Fallback order (user-specified):
  1. gemini-2.5-flash
  2. gemini-2.5-flash-latest
  3. gemini-3-pro
  4. gemini-3-flash
  5. gemini-3.1-pro
  6. gemini-3.1-flash
  7. openrouter/auto  (final fallback — OpenRouter)
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from extractors.base import CascadingExtractor
from config.settings import settings
from loguru import logger


# Ordered fallback chain — each entry: (model_name, provider)
_FALLBACK_CHAIN = [
    ("gemini-2.5-flash",              "google"),
    ("gemini-2.5-pro",                "google"),
    ("gemini-3.0-pro-preview",        "google"),
    ("gemini-3.0-flash-preview",      "google"),
    ("gemini-3.1-pro-preview",        "google"),
    ("gemini-3.1-flash-preview",      "google"),
    ("openrouter/auto",               "openrouter"),
]


class GeminiProExtractor(CascadingExtractor):
    model_id = "gemini_pro"

    def __init__(self):
        super().__init__()
        for model_name, provider in _FALLBACK_CHAIN:
            if provider == "google":
                self._models.append((
                    model_name,
                    ChatGoogleGenerativeAI(
                        model=model_name,
                        google_api_key=settings.GOOGLE_API_KEY,
                        temperature=0.1,
                        max_output_tokens=1024,
                        max_retries=1,
                    ),
                ))
            else:  # openrouter
                self._models.append((
                    model_name,
                    ChatOpenAI(
                        model="openrouter/auto",
                        base_url="https://openrouter.ai/api/v1",
                        api_key=settings.OPENROUTER_API_KEY,
                        temperature=0.1,
                        max_tokens=1024,
                    ),
                ))
        self._failures = [0] * len(self._models)
