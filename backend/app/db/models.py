"""ORM models — 1:1 with the original Drizzle schema (table & column names),
so a database created by the previous Next.js backend keeps working."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
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


class YoutubeContent(Base):
    """YouTube Master Content — one row per Short / episode."""

    __tablename__ = "youtube_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    episode: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="Draft")
    collection: Mapped[str] = mapped_column(Text, nullable=False)
    sound_music: Mapped[str] = mapped_column(Text, nullable=False, default="")
    effects: Mapped[str] = mapped_column(Text, nullable=False, default="")
    subtitles: Mapped[str] = mapped_column(Text, nullable=False, default="None")
    thumbnail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    # On-screen script for the FFmpeg renderer: { command, tip, audio }
    script: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # none | queued | running | done | failed
    render_status: Mapped[str] = mapped_column(Text, nullable=False, default="none")
    render_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    render_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Relative to the render root, e.g. "21/video.mp4". Null until success.
    video_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    daily_stats: Mapped[list[ContentDailyStats]] = relationship(
        back_populates="content",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("youtube_content_date_idx", "date"),
        Index("youtube_content_collection_idx", "collection"),
    )


class ContentDailyStats(Base):
    """Daily performance per episode — powers every chart and KPI."""

    __tablename__ = "content_daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("youtube_content.id", ondelete="CASCADE"),
        nullable=False,
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    watch_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subs_gained: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    content: Mapped[YoutubeContent] = relationship(back_populates="daily_stats")

    __table_args__ = (
        UniqueConstraint("content_id", "day", name="content_daily_stats_uniq"),
        Index("content_daily_stats_day_idx", "day"),
    )
