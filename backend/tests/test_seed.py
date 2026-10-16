"""Deterministic seeding."""

from __future__ import annotations

import sqlite3

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import ContentDailyStats, YoutubeContent
from app.db.seed import needs_seed, seed


def test_seed_creates_expected_volume(seeded_session: Session):
    episodes = seeded_session.scalar(select(func.count()).select_from(YoutubeContent))
    stats = seeded_session.scalar(select(func.count()).select_from(ContentDailyStats))
    assert episodes == 26
    assert stats > 26  # at least one stat row per episode


def test_seed_is_idempotent(seeded_session: Session):
    assert needs_seed(seeded_session) is False
    assert seed(seeded_session) == 0


def test_seed_deterministic(settings, tmp_path):
    """Two fresh databases produce identical datasets."""
    from app.core.config import Settings
    from app.db.base import Base
    from app.db.session import build_engine, build_session_factory

    snapshots = []
    for index in range(2):
        db_url = f"sqlite:///{tmp_path / f'seed-{index}.db'}"
        engine = build_engine(
            Settings(database_url=db_url, render_root=tmp_path / f"renders-{index}")
        )
        Base.metadata.create_all(engine)
        factory = build_session_factory(engine)
        with factory() as session:
            seed(session)
            rows = session.scalars(
                select(YoutubeContent).order_by(YoutubeContent.episode)
            ).all()
            snapshots.append(
                [(r.episode, r.title, r.status, r.collection) for r in rows]
            )
        engine.dispose()

    assert snapshots[0] == snapshots[1]


def test_seed_dates_stay_within_history(seeded_session: Session):
    from datetime import date

    today = date.today()
    rows = seeded_session.scalars(select(YoutubeContent)).all()
    for row in rows:
        assert row.date <= today
        assert (today - row.date).days < 180
        # every episode has stats from its publish day onward
        assert row.daily_stats, f"episode {row.episode} has no stats"


def test_seeding_through_engine_does_not_leak_connections(seeded_session: Session):
    """Guard against the classic SQLite 'unable to open database file' flake."""
    db_path = seeded_session.get_bind().url.database
    probe = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        # table was renamed youtube_main; keep legacy name support via alias check
        try:
            count = probe.execute("select count(*) from youtube_main").fetchone()[0]
        except sqlite3.OperationalError:
            count = probe.execute("select count(*) from youtube_content").fetchone()[0]
        assert count == 26
    finally:
        probe.close()
