"""
Centralized application settings using pydantic-settings.

All configuration is read from environment variables or a .env file.
This module is the single source of truth for all config values.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Loaded once at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "Astro Platform"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "postgresql://astro:astro@localhost:5432/astro_platform"
    database_async_url: str = "postgresql+asyncpg://astro:astro@localhost:5432/astro_platform"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30

    # ── Security ─────────────────────────────────────────────────────────────
    secret_key: str = "change-me-in-production"
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ── Editorial Defaults ───────────────────────────────────────────────────
    default_school: str = "luz_e_sombra"
    default_house_system: str = "placidus"

    # ── LLM (placeholder for future) ─────────────────────────────────────────
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3

    # ── Workers (placeholder for future) ─────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    ephemeris_provider: str = "analytical"
    swisseph_ephemeris_path: str | None = None

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.database_async_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance. Use as FastAPI dependency."""
    return Settings()
