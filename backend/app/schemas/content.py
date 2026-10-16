"""Content (episode) request/response schemas."""

from __future__ import annotations

from typing import Any

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


class EpisodeSceneIn(CamelModel):
    duration_sec: int = Field(default=45, ge=DURATION_MIN_SEC, le=DURATION_MAX_SEC)
    command: str = Field(default="", max_length=COMMAND_MAX)
    tip: str = Field(default="", max_length=TIP_MAX)
    audio: bool = True
    notes: str = Field(default="", max_length=TEXT_FIELD_MAX)


class EpisodeSceneOut(CamelModel):
    id: int
    position: int
    duration_sec: int
    command: str
    tip: str
    audio: bool
    notes: str


class EpisodeCreate(CamelModel):
    title: str = Field(min_length=TITLE_MIN, max_length=TITLE_MAX)
    date: str  # ISO YYYY-MM-DD, validated by the service layer
    # legacy
    status: str | None = Field(default=None)
    collection: str | None = Field(default=None)
    sound_music: str | None = Field(default=None, max_length=TEXT_FIELD_MAX)
    effects: str | None = Field(default=None, max_length=TEXT_FIELD_MAX)
    subtitles: str | None = Field(default=None)
    thumbnail: str | None = Field(default=None, max_length=TEXT_FIELD_MAX)
    # new workbook fields
    visibility: str | None = Field(default=None)
    collection_id: int | None = Field(default=None)
    series_name: str | None = Field(default=None, max_length=TEXT_FIELD_MAX)
    series_id: int | None = Field(default=None)
    episode_number: int | None = Field(default=None, ge=1)
    sound_effects: bool | None = Field(default=None)
    music: bool | None = Field(default=None)
    subtitles_count: int | None = Field(default=None, ge=0)
    thumbnail_ready: bool | None = Field(default=None)
    duration_sec: int = Field(
        default=45, ge=DURATION_MIN_SEC, le=DURATION_MAX_SEC
    )
    render: bool = False
    # Render fields — required together when `render` is true.
    command: str = Field(default="", max_length=COMMAND_MAX)
    tip: str = Field(default="", max_length=TIP_MAX)
    audio: bool = True
    # optional scene list for Lab
    scenes: list[dict[str, Any]] | None = None


class EpisodePatch(CamelModel):
    status: str | None = None
    visibility: str | None = None
    title: str | None = Field(default=None, min_length=TITLE_MIN, max_length=TITLE_MAX)
    collection: str | None = None
    collection_id: int | None = None
    sound_music: str | None = Field(default=None, max_length=TEXT_FIELD_MAX)
    sound_effects: bool | None = None
    music: bool | None = None
    effects: str | None = Field(default=None, max_length=TEXT_FIELD_MAX)
    subtitles: str | None = None
    subtitles_count: int | None = None
    thumbnail: str | None = None
    thumbnail_ready: bool | None = None
    series_name: str | None = None
    series_id: int | None = None
    episode_number: int | None = Field(default=None, ge=1)
    date: str | None = None


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
    # new workbook fields
    visibility: str
    series_id: int
    series_name: str
    episode_number: int
    episode_display: str
    collection_id: int | None
    sound_effects: bool
    music: bool
    subtitles_count: int
    thumbnail_ready: bool
    scenes: list[EpisodeSceneOut] = Field(default_factory=list)


class MutationOk(BaseModel):
    ok: bool = True
    id: int
