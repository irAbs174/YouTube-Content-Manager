"""Episode CRUD + domain validation (the logic behind /api/content)."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import (
    COLLECTION_NAMES,
    MAX_DAYS_IN_FUTURE,
    STATUSES,
    SUBTITLE_OPTIONS,
)
from app.core.errors import NotFoundError, ValidationError
from app.db.models import ContentDailyStats, YoutubeContent
from app.schemas.content import EpisodeCreate, EpisodePatch


def parse_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValidationError(f"Invalid date `{raw}` — expected YYYY-MM-DD") from exc


def _validate_enum(value: str, allowed: tuple[str, ...], label: str) -> str:
    if value not in allowed:
        raise ValidationError(f"Unknown {label}: {value}")
    return value


def validate_create(payload: EpisodeCreate) -> None:
    """Cross-field rules Pydantic can't express on its own."""
    _validate_enum(payload.status, STATUSES, "status")
    _validate_enum(payload.collection, COLLECTION_NAMES, "collection")
    _validate_enum(payload.subtitles, SUBTITLE_OPTIONS, "subtitles")

    day = parse_date(payload.date)
    if day > date.today() + timedelta(days=MAX_DAYS_IN_FUTURE):
        raise ValidationError(
            f"Date cannot be more than {MAX_DAYS_IN_FUTURE} days in the future"
        )

    if payload.render and not payload.command.strip():
        raise ValidationError(
            "An on-screen command is required to render a video"
        )


def next_episode_number(session: Session) -> int:
    highest = session.scalar(select(func.max(YoutubeContent.episode)))
    return (highest or 0) + 1


def create_episode(session: Session, payload: EpisodeCreate) -> YoutubeContent:
    validate_create(payload)
    row = YoutubeContent(
        episode=next_episode_number(session),
        date=parse_date(payload.date),
        title=payload.title.strip(),
        status=payload.status,
        collection=payload.collection,
        sound_music=payload.sound_music.strip(),
        effects=payload.effects.strip(),
        subtitles=payload.subtitles,
        thumbnail=payload.thumbnail.strip(),
        duration_sec=payload.duration_sec,
        script=None,  # set by the caller when a render is requested
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def apply_render_script(
    session: Session, row: YoutubeContent, payload: EpisodeCreate
) -> None:
    """Attach the on-screen script when the episode was queued for rendering."""
    if not payload.render:
        return
    row.script = {
        "command": payload.command.strip(),
        "tip": payload.tip.strip(),
        "audio": payload.audio,
    }
    session.commit()


def update_episode(
    session: Session, episode_id: int, payload: EpisodePatch
) -> YoutubeContent:
    row = _get_or_404(session, episode_id)
    changed = False
    if payload.title is not None:
        row.title = payload.title.strip()
        changed = True
    if payload.status is not None:
        _validate_enum(payload.status, STATUSES, "status")
        row.status = payload.status
        changed = True
    if payload.title is not None and not row.title:
        raise ValidationError("Title cannot be empty")
    if changed:
        session.commit()
        session.refresh(row)
    return row


def delete_episode(session: Session, episode_id: int) -> None:
    row = _get_or_404(session, episode_id)
    # daily stats cascade via FK ondelete; SQLite needs the ORM cascade too.
    session.query(ContentDailyStats).filter(
        ContentDailyStats.content_id == episode_id
    ).delete()
    session.delete(row)
    session.commit()


def _get_or_404(session: Session, episode_id: int) -> YoutubeContent:
    row = session.get(YoutubeContent, episode_id)
    if row is None:
        raise NotFoundError("Episode not found")
    return row


def get_episode(session: Session, episode_id: int) -> YoutubeContent:
    return _get_or_404(session, episode_id)
