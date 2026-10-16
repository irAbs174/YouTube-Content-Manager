"""FastAPI dependency wiring — the seam tests use to swap implementations."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.constants import SESSION_COOKIE
from app.db.models import User
from app.rendering.queue import RenderQueue
from app.services.auth import user_from_token


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


def get_current_user_optional(request: Request, session: Session = Depends(get_db)) -> User | None:
    raw = request.cookies.get(SESSION_COOKIE)
    if not raw:
        return None
    try:
        return user_from_token(session, raw)
    except Exception:
        return None


def get_current_user(request: Request, session: Session = Depends(get_db)) -> User:
    # Re-use logic but raise proper 401 via service
    raw = request.cookies.get(SESSION_COOKIE)
    return user_from_token(session, raw)
