from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="RF_",
        case_sensitive=False,
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/research_finder.db"

    # AI Provider
    ai_enabled: bool = False
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"
    ai_max_analyses_per_run: int = 10
    ai_max_analyses_per_day: int = 50

    # Logging
    log_level: str = "INFO"
    log_file: str = "data/research_finder.log"

    # Discovery defaults
    default_radius_km: float = 5.0
    default_min_rating: float = 3.0
    default_min_reviews: int = 10

    @property
    def data_dir(self) -> Path:
        path = Path("data")
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
