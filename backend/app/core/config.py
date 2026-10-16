"""Application settings — everything overridable via `YTCM_*` env vars."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR: Path = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR: Path = BACKEND_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="YTCM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # `postgresql+psycopg://user:pass@host/db` in production; SQLite fallback
    # for local dev keeps the stack runnable without a Postgres server.
    database_url: str = f"sqlite:///{DEFAULT_DATA_DIR / 'youtube.db'}"

    # Root directory for rendered videos / extracted thumbnails.
    render_root: Path = DEFAULT_DATA_DIR / "renders"

    # Seed deterministic sample data on first startup (empty database only).
    seed_on_startup: bool = True

    # Create missing tables on startup (safe no-op when they already exist).
    create_tables_on_startup: bool = True

    # Allowed browser origins for direct (non-proxied) API access.
    cors_origins: tuple[str, ...] = (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    )

    # Signed session cookies (override in production).
    session_secret: str = "dev-insecure-change-me"
    session_ttl_days: int = 14

    # Used only when seed_on_startup is true (tests / empty local DB).
    demo_email: str = "demo@ytcm.test"
    demo_password: str = "demo-password-1"

    # Interval between render-queue worker polls (seconds).
    render_poll_interval: float = 0.05

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Cached default settings (FastAPI dependency override point for tests)."""
    return Settings()
