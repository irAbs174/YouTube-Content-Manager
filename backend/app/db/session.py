"""Engine / session factory.

Sync SQLAlchemy is used deliberately: the workload is small dashboards and
single-row mutations, and it keeps the render worker (which shells out to
FFmpeg in a thread) simple. SQLite connections are thread-tolerant because
the render worker writes from its own thread.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings


def build_engine(settings: Settings) -> Engine:
    """Create an engine honouring SQLite's single-file semantics."""
    if settings.is_sqlite:
        # Ensure the parent directory of the SQLite file exists.
        raw = settings.database_url.split("sqlite:///", 1)[-1]
        if raw and raw != ":memory:":
            Path(raw).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False, "timeout": 30},
            future=True,
        )
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Transactional scope for background jobs (render worker, seeding)."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
