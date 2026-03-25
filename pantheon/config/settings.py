"""
Central configuration for Project Pantheon.

All constants and configuration variables live here. Never hardcode values elsewhere
in the project. This configuration uses pydantic-settings to automatically load
values from the .env file.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    # LLM Providers
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str
    OPENROUTER_API_KEY: str
    MISTRAL_API_KEY: str = ""
    SAMBANOVA_API_KEY: str = ""

    # Upstox
    UPSTOX_API_KEY: str = ""
    UPSTOX_API_SECRET: str = ""
    UPSTOX_REDIRECT_URI: str = "http://localhost:8000/callback"
    UPSTOX_NOTIFIER_PORT: int = 8000

    # Database
    DATABASE_URL: str
    DATABASE_URL_ASYNC: str

    @field_validator("DATABASE_URL", "DATABASE_URL_ASYNC", mode="before")
    @classmethod
    def strip_quotes(cls, v: str) -> str:
        """Strip surrounding quotes that GitHub Secrets may preserve from .env values."""
        if isinstance(v, str):
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
        return v

    # LangSmith
    LANGSMITH_TRACING: str = "true"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "Project Pantheon"

    # External APIs
    FINNHUB_API_KEY: str = ""
    SCREENER_EMAIL: str = ""
    SCREENER_PASSWORD: str = ""
    SENTRY_DSN: str = ""

    # MMCI Algorithm parameters
    DISSENT_THRESHOLD: float = 0.15
    LEARNING_RATE: float = 0.05
    MAX_ALLOC: float = 0.20
    WEIGHT_FLOOR: float = 0.05
    WEIGHT_CEILING: float = 0.40
    MIN_MODELS_REQUIRED: int = 3
    MODEL_TIMEOUT_SECONDS: int = 20
    MODEL_RETRY_ATTEMPTS: int = 3

    # Regime thresholds
    BULL_MA200_MULTIPLIER: float = 1.02
    BEAR_MA200_MULTIPLIER: float = 0.98

    # Rate limits
    GEMINI_PRO_DAILY_BUDGET: int = 90
    GEMINI_FLASH_DAILY_BUDGET: int = 200
    BATCH_SIZE: int = 10

    # Caching
    FUNDAMENTALS_CACHE_DAYS: int = 7
    NEWS_RETENTION_HOURS: int = 72
    NODE_CACHE_TTL_HOURS: int = 4

    # Schedule (IST hours)
    ANALYSIS_HOUR_IST: int = 17
    ANALYSIS_MINUTE_IST: int = 0
    NEWS_POLL_INTERVAL_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
