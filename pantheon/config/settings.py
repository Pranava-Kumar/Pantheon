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
    HUGGINGFACE_API_KEY: str = ""  # Free tier: 30 req/hour

    # Upstox
    UPSTOX_API_KEY: str = ""
    UPSTOX_API_SECRET: str = ""
    UPSTOX_REDIRECT_URI: str = "http://localhost:8000/callback"
    UPSTOX_NOTIFIER_PORT: int = 8000

    # Database
    DATABASE_URL: str
    DATABASE_URL_ASYNC: str
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("DATABASE_URL", "DATABASE_URL_ASYNC", "REDIS_URL", mode="before")

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
    GOOGLE_API_DELAY_SECONDS: int = 15  # Delay between stocks to stay under free tier limit
    BATCH_SEPARATOR_DELAY_SECONDS: int = 1  # Delay between model batches

    # Caching
    FUNDAMENTALS_CACHE_DAYS: int = 7
    NEWS_RETENTION_HOURS: int = 72
    NODE_CACHE_TTL_HOURS: int = 4
    CACHE_DIR: str = "./cache"  # Directory for SQLite cache files (relative to project root)

    # Security & Authentication
    JWT_SECRET_KEY: str = ""  # Must be set via environment variable in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_ORIGINS: list[str] = ["http://localhost:8501", "http://localhost:3000"]

    @field_validator("CACHE_DIR")
    @classmethod
    def resolve_cache_dir(cls, v: str) -> str:
        """Convert CACHE_DIR to absolute path and validate it's safe."""
        if not Path(v).is_absolute():
            v = str(Path(__file__).resolve().parent.parent.parent / v)

        # Validate cache directory is not a protected path
        resolved = Path(v).resolve()
        # Check against protected system paths (Unix and Windows)
        protected_paths = [
            # Unix/Linux protected paths
            Path("/etc"), Path("/usr"), Path("/bin"), Path("/sbin"), Path("/boot"), Path("/dev"),
            # Windows protected paths
            Path("C:\\Windows"), Path("C:\\Program Files"), Path("C:\\Program Files (x86)"),
            Path("C:\\Windows\\System32"), Path("C:\\Windows\\SysWOW64")
        ]
        for protected in protected_paths:
            try:
                resolved.relative_to(protected)
                raise ValueError(f"CACHE_DIR cannot be set to protected path: {v}")
            except ValueError:
                pass  # Path is not relative to this protected path, continue checking

        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str):
        """Ensure JWT secret is properly configured and not using default value."""
        # Require non-empty JWT secret for security in production
        if not v or not v.strip():
            # Allow empty secret for development/testing environments
            import os
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("JWT_SECRET_KEY cannot be empty in production. Set a secure random value.")
            # Return a default for non-production (will be overridden by .env in most cases)
            return "dev-secret-key-change-in-production"
        # Check against known default/insecure values
        insecure_defaults = [
            "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
            "your-secret-key",
            "secret",
            "changeme",
        ]
        if v in insecure_defaults:
            raise ValueError("JWT_SECRET_KEY must be changed from default value")
        return v

    # Schedule (IST hours)
    ANALYSIS_HOUR_IST: int = 17
    ANALYSIS_MINUTE_IST: int = 0
    NEWS_POLL_INTERVAL_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
    )

settings = Settings()
