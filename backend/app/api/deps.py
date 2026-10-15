"""FastAPI dependency wiring — the seam tests use to swap implementations."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.rendering.queue import RenderQueue


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Iterator[Session]:
    """One session per request; commits on success, rolls back on error."""
    session = request.app.state.session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_queue(request: Request) -> RenderQueue:
    return request.app.state.render_queue
