"""ORM models — YouTube Main sheet + auth + scenes."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    sessions: Mapped[list[SessionToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    series: Mapped[list[Series]] = relationship(back_populates="user")
    episodes: Mapped[list[YoutubeMain]] = relationship(back_populates="user")
    contents: Mapped[list[ContentItem]] = relationship(back_populates="user")
    subtitle_rows: Mapped[list[SubtitleRow]] = relationship(back_populates="user")


class SessionToken(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="sessions")


class Series(Base):
    __tablename__ = "series"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(back_populates="series")
    episodes: Mapped[list[YoutubeMain]] = relationship(back_populates="series")

    __table_args__ = (UniqueConstraint("user_id", "name", name="series_user_name_uniq"),)


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    color: Mapped[str] = mapped_column(Text, nullable=False, default="#94a3b8")
    # Collections sheet metadata (ID · Title · Description · type · Share Link)
    code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    type: Mapped[str] = mapped_column(Text, nullable=False, default="")
    share_link: Mapped[str] = mapped_column(Text, nullable=False, default="")

    episodes: Mapped[list[YoutubeMain]] = relationship(back_populates="collection_row")


class YoutubeMain(Base):
    """One YouTube Short / Main-sheet row."""

    __tablename__ = "youtube_main"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    series_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("series.id", ondelete="RESTRICT"), nullable=False
    )
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(Text, nullable=False, default="Private")
    collection_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("collections.id", ondelete="SET NULL"), nullable=True
    )
    # Legacy string column kept for backward compat (old code writes collection name here)
    collection: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sound_effects: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    music: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    subtitles_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    thumbnail_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    # Episodes sheet — Shared Link (the published YouTube Short URL)
    shared_link: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Status = "Schedule" → the moment the episode goes live
    schedule_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Legacy JSON kept during renderer cutover; scenes are canonical.
    script: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # Legacy string columns for backward compat with existing frontend/tests
    # during the Private/Public migration — still written so old API keeps working.
    sound_music: Mapped[str] = mapped_column(Text, nullable=False, default="")
    effects: Mapped[str] = mapped_column(Text, nullable=False, default="")
    subtitles: Mapped[str] = mapped_column(Text, nullable=False, default="EN")
    thumbnail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    render_status: Mapped[str] = mapped_column(Text, nullable=False, default="none")
    render_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    render_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="episodes")
    series: Mapped[Series] = relationship(back_populates="episodes")
    collection_row: Mapped[Collection | None] = relationship(back_populates="episodes")
    scenes: Mapped[list[EpisodeScene]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
        order_by="EpisodeScene.position",
    )
    daily_stats: Mapped[list[ContentDailyStats]] = relationship(
        back_populates="content",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    contents: Mapped[list[ContentItem]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
        order_by="ContentItem.position",
        foreign_keys="ContentItem.episode_id",
    )
    subtitle_rows: Mapped[list[SubtitleRow]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
        order_by="SubtitleRow.start_sec",
    )
    related_contents: Mapped[list[ContentItem]] = relationship(
        back_populates="related_video",
        order_by="ContentItem.position",
        foreign_keys="ContentItem.related_video_id",
    )

    __table_args__ = (
        UniqueConstraint(
            "series_id", "episode_number", name="youtube_main_series_episode_uniq"
        ),
        Index("youtube_main_date_idx", "date"),
        Index("youtube_main_user_idx", "user_id"),
        Index("youtube_main_visibility_idx", "visibility"),
    )

    # ── legacy aliases for service-layer tests (episode ↔ episode_number, status ↔ visibility)
    episode = synonym("episode_number")
    status = synonym("visibility")

    @property
    def episode_display(self) -> str:
        # guard for seed rows where series not yet flushed
        try:
            return f"{self.series.name} #{self.episode_number}"
        except Exception:
            return f"Episode #{self.episode_number}"

    @property
    def collection_name(self) -> str:
        if self.collection_row is not None:
            return self.collection_row.name
        return self.collection or ""


class EpisodeScene(Base):
    __tablename__ = "episode_scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("youtube_main.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    command: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tip: Mapped[str] = mapped_column(Text, nullable=False, default="")
    audio: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Scences sheet — Scense Title · SCN Hook · SCN Senario · SCN Body
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hook: Mapped[str] = mapped_column(Text, nullable=False, default="")
    scenario: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    episode: Mapped[YoutubeMain] = relationship(back_populates="scenes")

    __table_args__ = (
        UniqueConstraint("content_id", "position", name="episode_scenes_pos_uniq"),
    )


class Language(Base):
    """Languages 🌍 — ID · Name."""

    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    contents: Mapped[list[ContentItem]] = relationship(back_populates="language")
    subtitles: Mapped[list[SubtitleRow]] = relationship(back_populates="language")


class Asset(Base):
    """Assets 👁️👁️ — Assets ID · Type · Name · Context · Description · Storage."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, default="", unique=True)
    type: Mapped[str] = mapped_column(Text, nullable=False, default="")
    name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    storage_location: Mapped[str] = mapped_column(Text, nullable=False, default="")


class ContentItem(Base):
    """Contents 🖊️ — one row per content block of an episode."""

    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    episode_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("youtube_main.id", ondelete="CASCADE"),
        nullable=False,
    )
    language_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("languages.id", ondelete="SET NULL"), nullable=True
    )
    related_video_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("youtube_main.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="")
    subtitles: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pinned_comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    music: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    thumbnail: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    episode: Mapped[YoutubeMain] = relationship(
        back_populates="contents", foreign_keys=[episode_id]
    )
    language: Mapped[Language | None] = relationship(back_populates="contents")
    user: Mapped[User] = relationship(back_populates="contents")
    related_video: Mapped[YoutubeMain | None] = relationship(
        back_populates="related_contents", foreign_keys=[related_video_id]
    )


class SubtitleRow(Base):
    """Subtitles 🔍 — Episode · Language · Time duration · Text."""

    __tablename__ = "subtitles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    episode_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("youtube_main.id", ondelete="CASCADE"),
        nullable=False,
    )
    language_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("languages.id", ondelete="SET NULL"), nullable=True
    )
    start_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    end_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    episode: Mapped[YoutubeMain] = relationship(back_populates="subtitle_rows")
    language: Mapped[Language | None] = relationship(back_populates="subtitles")
    user: Mapped[User] = relationship(back_populates="subtitle_rows")


class ContentDailyStats(Base):
    """Daily performance per episode — powers every chart and KPI."""

    __tablename__ = "content_daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("youtube_main.id", ondelete="CASCADE"),
        nullable=False,
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    watch_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subs_gained: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    content: Mapped[YoutubeMain] = relationship(back_populates="daily_stats")

    __table_args__ = (
        UniqueConstraint("content_id", "day", name="content_daily_stats_uniq"),
        Index("content_daily_stats_day_idx", "day"),
    )


# Back-compat alias used by a few tests during the cutover.
YoutubeContent = YoutubeMain
