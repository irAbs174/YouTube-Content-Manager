"""Service-level content tests (no HTTP layer)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.db.models import ContentDailyStats, YoutubeContent
from app.schemas.content import EpisodeCreate, EpisodePatch
from app.services.content import (
    create_episode,
    delete_episode,
    next_episode_number,
    update_episode,
)

TODAY = date.today()


def _payload(**overrides) -> EpisodeCreate:
    base = dict(
        title="service layer episode",
        date=TODAY.isoformat(),
        status="Private",
        collection="Linux Basics",
        soundMusic="",
        effects="",
        subtitles="EN",
        thumbnail="",
        durationSec=45,
        render=False,
        command="",
        tip="",
        audio=True,
    )
    base.update(overrides)
    return EpisodeCreate(**base)


def test_next_episode_number_increments(seeded_session: Session):
    first = next_episode_number(seeded_session)
    create_episode(seeded_session, _payload())
    assert next_episode_number(seeded_session) == first + 1


def test_create_strips_whitespace(seeded_session: Session):
    row = create_episode(seeded_session, _payload(title="  padded title  "))
    assert row.title == "padded title"


def test_create_rejects_far_future(seeded_session: Session):
    with pytest.raises(ValidationError, match="future"):
        create_episode(seeded_session, _payload(date=(TODAY + timedelta(days=400)).isoformat()))


def test_create_rejects_render_without_command(seeded_session: Session):
    with pytest.raises(ValidationError, match="command"):
        create_episode(seeded_session, _payload(render=True, command=" "))


def test_update_title_and_status(seeded_session: Session):
    row = create_episode(seeded_session, _payload())
    updated = update_episode(
        seeded_session, row.id, EpisodePatch(status="Public", title="new title")
    )
    assert updated.status == "Public"
    assert updated.title == "new title"


def test_update_no_fields_is_noop(seeded_session: Session):
    row = create_episode(seeded_session, _payload())
    same = update_episode(seeded_session, row.id, EpisodePatch())
    assert same.status == row.status


def test_update_missing_raises_404(seeded_session: Session):
    with pytest.raises(NotFoundError):
        update_episode(seeded_session, 999_999, EpisodePatch(status="Private"))


def test_delete_cascades_daily_stats(seeded_session: Session):
    row = create_episode(seeded_session, _payload())
    seeded_session.add(
        ContentDailyStats(content_id=row.id, day=TODAY, views=10, impressions=100)
    )
    seeded_session.commit()

    delete_episode(seeded_session, row.id)

    remaining = seeded_session.scalars(
        select(ContentDailyStats).where(ContentDailyStats.content_id == row.id)
    ).all()
    assert remaining == []
    assert seeded_session.get(YoutubeContent, row.id) is None
