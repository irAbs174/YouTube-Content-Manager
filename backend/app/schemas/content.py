"""Content (episode) request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.constants import (
    COMMAND_MAX,
    DEFAULT_COLLECTION,
    DEFAULT_STATUS,
    DEFAULT_SUBTITLES,
    DURATION_MAX_SEC,
    DURATION_MIN_SEC,
    TEXT_FIELD_MAX,
    TIP_MAX,
    TITLE_MAX,
    TITLE_MIN,
)
from app.schemas.common import CamelModel


class OnScreenScript(CamelModel):
    command: str = Field(max_length=COMMAND_MAX)
    tip: str = Field(default="", max_length=TIP_MAX)
    audio: bool = True


class EpisodeCreate(CamelModel):
    title: str = Field(min_length=TITLE_MIN, max_length=TITLE_MAX)
    date: str  # ISO YYYY-MM-DD, validated by the service layer
    status: str = Field(default=DEFAULT_STATUS)
    collection: str = Field(default=DEFAULT_COLLECTION)
    sound_music: str = Field(default="", max_length=TEXT_FIELD_MAX)
    effects: str = Field(default="", max_length=TEXT_FIELD_MAX)
    subtitles: str = Field(default=DEFAULT_SUBTITLES)
    thumbnail: str = Field(default="", max_length=TEXT_FIELD_MAX)
    duration_sec: int = Field(
        default=45, ge=DURATION_MIN_SEC, le=DURATION_MAX_SEC
    )
    render: bool = False
    # Render fields — required together when `render` is true.
    command: str = Field(default="", max_length=COMMAND_MAX)
    tip: str = Field(default="", max_length=TIP_MAX)
    audio: bool = True


class EpisodePatch(CamelModel):
    status: str | None = None
    title: str | None = Field(default=None, min_length=TITLE_MIN, max_length=TITLE_MAX)


class EpisodeOut(CamelModel):
    """Full episode row as returned by POST /api/content."""

    id: int
    episode: int
    date: str
    title: str
    status: str
    collection: str
    sound_music: str
    effects: str
    subtitles: str
    thumbnail: str
    duration_sec: int
    script: OnScreenScript | None = None
    render_status: str
    render_progress: int
    render_error: str | None = None
    video_path: str | None = None


class MutationOk(BaseModel):
    ok: bool = True
    id: int
