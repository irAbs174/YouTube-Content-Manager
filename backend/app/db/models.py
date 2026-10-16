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
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    sound_effects: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    music: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    subtitles_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    thumbnail_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    # Legacy JSON kept during renderer cutover; scenes are canonical.
    script: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
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

    __table_args__ = (
        UniqueConstraint(
            "series_id", "episode_number", name="youtube_main_series_episode_uniq"
        ),
        Index("youtube_main_date_idx", "date"),
        Index("youtube_main_user_idx", "user_id"),
        Index("youtube_main_visibility_idx", "visibility"),
    )

    @property
    def episode_display(self) -> str:
        return f"{self.series.name} #{self.episode_number}"

    @property
    def collection_name(self) -> str:
        return self.collection_row.name if self.collection_row is not None else ""


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

    episode: Mapped[YoutubeMain] = relationship(back_populates="scenes")

    __table_args__ = (
        UniqueConstraint("content_id", "position", name="episode_scenes_pos_uniq"),
    )


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
