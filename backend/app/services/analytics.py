"""Dashboard analytics — the only place KPI math lives.

Contract (matches the frontend's `DashboardData`):
  * range  : inclusive [from, to] window, `days` = day count
  * series : one point per day of the window (zero-filled, no gaps)
  * kpis   : window totals vs the immediately-preceding window of equal length
  * rows   : episodes dated inside the window (+ collection/status filters),
             each with its daily stats aggregated across the window
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.constants import (
    COLLECTION_NAMES,
    DEFAULT_RANGE_DAYS,
    MAX_RANGE_DAYS,
    STATUSES,
)
from app.core.errors import ValidationError
from app.db.models import ContentDailyStats, YoutubeContent
from app.schemas.dashboard import (
    DashboardData,
    DashboardRow,
    Filters,
    KpiPair,
    RangeInfo,
    SeriesPoint,
)

_WATCH_HOURS_DIVISOR = 3600.0


# ── filter parsing ───────────────────────────────────────────────────────────
def parse_filters(
    from_raw: str | None,
    to_raw: str | None,
    collection: str | None,
    status: str | None,
) -> Filters:
    """Validate and normalise query params into a Filters object."""
    today = date.today()
    from_date = (
        _parse_day(from_raw)
        if from_raw
        else today - timedelta(days=DEFAULT_RANGE_DAYS - 1)
    )
    to_date = _parse_day(to_raw) if to_raw else today

    if from_date > to_date:
        raise ValidationError("`from` must not be after `to`")
    if (to_date - from_date).days + 1 > MAX_RANGE_DAYS:
        raise ValidationError(f"Range cannot exceed {MAX_RANGE_DAYS} days")

    collection = (collection or "All").strip() or "All"
    if collection != "All" and collection not in COLLECTION_NAMES:
        raise ValidationError(f"Unknown collection: {collection}")
    status = (status or "All").strip() or "All"
    if status != "All" and status not in STATUSES:
        raise ValidationError(f"Unknown status: {status}")

    return Filters(
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
        collection=collection,
        status=status,
    )


def _parse_day(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValidationError(f"Invalid date `{raw}` — expected YYYY-MM-DD") from exc


# ── aggregation helpers ──────────────────────────────────────────────────────
_AGG_COLUMNS = (
    func.sum(ContentDailyStats.views),
    func.sum(ContentDailyStats.impressions),
    func.sum(ContentDailyStats.watch_seconds),
    func.sum(ContentDailyStats.likes),
    func.sum(ContentDailyStats.subs_gained),
)


def _per_episode_window(
    session: Session,
    day_from: date,
    day_to: date,
    content_ids: list[int] | None = None,
) -> dict[int, tuple[int, int, int, int]]:
    """Aggregate daily stats over [day_from, day_to] grouped by content_id."""
    conditions = [
        ContentDailyStats.day >= day_from,
        ContentDailyStats.day <= day_to,
    ]
    if content_ids is not None:
        if not content_ids:  # empty filter result — skip the query entirely
            return {}
        conditions.append(ContentDailyStats.content_id.in_(content_ids))
    rows = session.execute(
        select(ContentDailyStats.content_id, *_AGG_COLUMNS)
        .where(and_(*conditions))
        .group_by(ContentDailyStats.content_id)
    ).all()
    return {
        row[0]: (int(row[1] or 0), int(row[2] or 0), int(row[4] or 0), int(row[5] or 0))
        for row in rows
    }


def _daily_series(
    session: Session, day_from: date, day_to: date
) -> tuple[list[SeriesPoint], int]:
    """One point per day in the window (zero-filled, no gaps) + total impressions."""
    rows = session.execute(
        select(ContentDailyStats.day, *_AGG_COLUMNS)
        .where(and_(ContentDailyStats.day >= day_from, ContentDailyStats.day <= day_to))
        .group_by(ContentDailyStats.day)
        .order_by(ContentDailyStats.day)
    ).all()

    by_day = {row[0]: row for row in rows}
    points: list[SeriesPoint] = []
    total_impressions = 0
    day = day_from
    while day <= day_to:
        _, views, impressions, watch_seconds, likes, subs = by_day.get(
            day, (day, 0, 0, 0, 0, 0)
        )
        views, impressions = int(views or 0), int(impressions or 0)
        total_impressions += impressions
        points.append(
            SeriesPoint(
                day=day.isoformat(),
                views=views,
                watch_hours=round(int(watch_seconds or 0) / _WATCH_HOURS_DIVISOR, 2),
                subs=int(subs or 0),
                ctr=round(views / impressions, 4) if impressions else 0.0,
                likes=int(likes or 0),
            )
        )
        day += timedelta(days=1)
    return points, total_impressions


def _window_totals(points: list[SeriesPoint], impressions: int) -> dict[str, float]:
    views = sum(p.views for p in points)
    return {
        "views": float(views),
        "watchHours": round(sum(p.watch_hours for p in points), 2),
        "subs": float(sum(p.subs for p in points)),
        "ctr": round(views / impressions, 4) if impressions else 0.0,
        "likes": float(sum(p.likes for p in points)),
    }


# ── main entry point ─────────────────────────────────────────────────────────
def get_dashboard_data(session: Session, filters: Filters) -> DashboardData:
    from_date = date.fromisoformat(filters.from_date)
    to_date = date.fromisoformat(filters.to_date)
    days = (to_date - from_date).days + 1
    prev_from = from_date - timedelta(days=days)
    prev_to = from_date - timedelta(days=1)

    # 1) Episodes inside the window (collection/status filters applied).
    episode_conditions = [
        YoutubeContent.date >= from_date,
        YoutubeContent.date <= to_date,
    ]
    if filters.collection != "All":
        episode_conditions.append(YoutubeContent.collection == filters.collection)
    if filters.status != "All":
        episode_conditions.append(YoutubeContent.status == filters.status)
    episodes = list(
        session.scalars(
            select(YoutubeContent)
            .where(and_(*episode_conditions))
            .order_by(YoutubeContent.episode)
        ).all()
    )

    # 2) Current- and previous-window aggregates per episode.
    ids = [e.id for e in episodes]
    current_by_id = _per_episode_window(session, from_date, to_date, ids)
    rows = [
        _to_dashboard_row(
            episode,
            *current_by_id.get(episode.id, (0, 0, 0, 0)),
        )
        for episode in episodes
    ]

    # 3) Daily series + KPI pairs (current window vs preceding window).
    series, impressions_now = _daily_series(session, from_date, to_date)
    prev_series, impressions_prev = _daily_series(session, prev_from, prev_to)
    kpis = _kpi_pairs(series, impressions_now, prev_series, impressions_prev)

    return DashboardData(
        range=RangeInfo(
            from_date=from_date.isoformat(), to_date=to_date.isoformat(), days=days
        ),
        kpis=kpis,
        series=series,
        rows=rows,
        generated_at=datetime.now(UTC).isoformat(),
    )


def _kpi_pairs(
    series: list[SeriesPoint],
    impressions_now: int,
    prev_series: list[SeriesPoint],
    impressions_prev: int,
) -> dict[str, KpiPair]:
    current = _window_totals(series, impressions_now)
    previous = _window_totals(prev_series, impressions_prev)
    return {key: KpiPair(value=current[key], prev=previous[key]) for key in current}


def _to_dashboard_row(
    episode: YoutubeContent,
    views: int,
    impressions: int,
    likes: int,
    subs: int,
) -> DashboardRow:
    return DashboardRow(
        id=episode.id,
        episode=episode.episode,
        date=episode.date.isoformat(),
        title=episode.title,
        status=episode.status,
        collection=episode.collection,
        sound_music=episode.sound_music,
        effects=episode.effects,
        subtitles=episode.subtitles,
        thumbnail=episode.thumbnail,
        duration_sec=episode.duration_sec,
        script=episode.script,
        render_status=episode.render_status,
        render_progress=episode.render_progress,
        render_error=episode.render_error,
        video_path=episode.video_path,
        has_video=episode.video_path is not None,
        views=views,
        impressions=impressions,
        likes=likes,
        subs=subs,
    )
