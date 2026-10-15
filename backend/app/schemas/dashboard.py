"""Dashboard request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import CamelModel
from app.schemas.content import EpisodeOut  # noqa: F401  (re-export convenience)


class Filters(BaseModel):
    """Parsed dashboard filters (from / to / collection / status)."""

    from_date: str
    to_date: str
    collection: str = "All"
    status: str = "All"


class RangeInfo(CamelModel):
    # `from` is a Python keyword — explicit aliases keep the JSON contract.
    from_date: str = Field(alias="from")
    to_date: str = Field(alias="to")
    days: int


class KpiPair(CamelModel):
    value: float
    prev: float


class SeriesPoint(CamelModel):
    day: str
    views: int
    watch_hours: float
    subs: int
    ctr: float
    likes: int


class DashboardRow(EpisodeOut):
    """Episode row enriched with range-aggregated performance metrics."""

    has_video: bool
    views: int = 0
    impressions: int = 0
    likes: int = 0
    subs: int = 0


class DashboardData(CamelModel):
    range: RangeInfo
    kpis: dict[str, KpiPair]
    series: list[SeriesPoint]
    rows: list[DashboardRow]
    generated_at: str
