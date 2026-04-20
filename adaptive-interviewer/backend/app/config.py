"""Settings for the adaptive-interviewer service.

Shares env vars with the rest of the Darpan Labs platform (same
DATABASE_URL, same LLM keys). Adds a couple of adaptive-specific knobs
with `ADAPTIVE_` prefix so they can be tuned without touching the
other services.
"""

from functools import lru_cache
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Adaptive AI Interviewer"
    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "development"

    api_prefix: str = "/api/v1"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ]

    database_url: str = "postgresql+asyncpg://manavrsjain@localhost:5432/darpan"
    database_echo: bool = False

    llm_provider: str = "openai"
    llm_model: str = "gpt-4-turbo-preview"
    llm_classifier_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.6
    llm_max_tokens: int = 1400
    llm_max_retries: int = 3

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    sentry_dsn: Optional[str] = None

    # Adaptive-specific tuning
    adaptive_hard_budget_minutes: int = 65
    adaptive_phase1_budget_minutes: int = 10
    adaptive_phase3_budget_minutes: int = 33
    adaptive_phase4_budget_minutes: int = 15
    adaptive_classify_min_confidence: float = 0.60
    adaptive_classify_hybrid_floor: float = 0.50
    adaptive_classify_hybrid_second: float = 0.30
    adaptive_max_reclassifications: int = 1
    adaptive_probe_silence_seconds: int = 90

    @model_validator(mode="after")
    def ensure_asyncpg_driver(self):
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
