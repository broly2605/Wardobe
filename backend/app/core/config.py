"""Application configuration.

All runtime configuration is sourced from environment variables (loaded from a
local ``.env`` file in development). Centralizing configuration here keeps the
rest of the codebase free of ``os.environ`` lookups and makes the app trivial
to reconfigure for a cloud deployment — only the ``.env`` values change.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Absolute path to the ``backend/`` directory, used to resolve relative paths
# (uploads dir, .env) regardless of the current working directory.
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/wardrobe",
        description="Async SQLAlchemy connection string (asyncpg driver).",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/wardrobe",
        description="Sync connection string used by Alembic migrations.",
    )

    # --- AI provider (OpenAI) ---
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")
    openai_vision_model: str = Field(default="gpt-4o-mini")

    # --- Storage ---
    upload_dir: str = Field(default="uploads")

    # --- CORS ---
    # ``NoDecode`` disables pydantic-settings' default JSON parsing for this
    # complex field so our validator can accept a plain comma-separated string.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # --- App ---
    app_env: str = Field(default="development")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        """Allow CORS origins to be supplied as a comma-separated string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def upload_path(self) -> Path:
        """Absolute path to the uploads directory (created on startup)."""
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = BASE_DIR / path
        return path

    @property
    def ai_enabled(self) -> bool:
        """Whether an OpenAI key is configured. When False the app falls back
        to the fully-offline rule-based stylist."""
        return bool(self.openai_api_key and self.openai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (read once per process)."""
    return Settings()


settings = get_settings()
