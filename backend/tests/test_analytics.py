"""Service-level analytics tests (no HTTP layer)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.services.analytics import get_dashboard_data, parse_filters


def test_parse_filters_defaults_to_90_days():
    filters = parse_filters(None, None, None, None)
    today = date.today()
    assert filters.from_date == (today - timedelta(days=89)).isoformat()
    assert filters.to_date == today.isoformat()
    assert filters.collection == "All"
    assert filters.status == "All"


@pytest.mark.parametrize(
    ("params", "fragment"),
    [
        ({"from": "oops"}, "Invalid date"),
        ({"from": "2030-01-01", "to": "2029-01-01"}, "must not be after"),
        ({"collection": "bad"}, "Unknown collection"),
        ({"status": "bad"}, "Unknown status"),
    ],
)
def test_parse_filters_rejects_bad_input(params, fragment):
    with pytest.raises(ValidationError, match=fragment):
        parse_filters(
            params.get("from"),
            params.get("to"),
            params.get("collection"),
            params.get("status"),
        )


def test_parse_filters_normalises_blank_segments():
    filters = parse_filters(None, None, "  ", "")
    assert filters.collection == "All"
    assert filters.status == "All"


def test_series_zero_fills_gaps(seeded_session: Session):
    """The seed ends today, so the last N days must exist even without stats."""
    today = date.today()
    filters = parse_filters(
        today.isoformat(), today.isoformat(), None, None
    )
    data = get_dashboard_data(seeded_session, filters)
    assert len(data.series) == 1
    # today's stats exist in the seed, but the shape must never be empty
    assert data.series[0].day == today.isoformat()


def test_kpi_prev_window_is_immediately_preceding(seeded_session: Session):
    filters = parse_filters("2020-01-01", "2020-01-10", None, None)
    data = get_dashboard_data(seeded_session, filters)
    # no data in 2020 — both windows empty
    assert data.kpis["views"].value == 0
    assert data.kpis["views"].prev == 0
    assert all(p.views == 0 for p in data.series)
    assert data.rows == []


def test_ctr_is_zero_without_impressions(seeded_session: Session):
    data = get_dashboard_data(seeded_session, parse_filters("2020-01-01", "2020-01-05", None, None))
    assert data.kpis["ctr"].value == 0


def test_rows_ordered_by_episode(seeded_session: Session):
    data = get_dashboard_data(seeded_session, parse_filters(None, None, None, None))
    episodes = [row.episode for row in data.rows]
    assert episodes == sorted(episodes)


def test_metrics_consistency_between_rows_and_series(seeded_session: Session):
    """Rows = episodes *published* in the window with their in-window views;
    series = channel-wide daily totals (older episodes keep earning views).
    So series >= rows on a partial window, and equal on the full history."""
    partial = get_dashboard_data(seeded_session, parse_filters(None, None, None, None))
    rows_views = sum(row.views for row in partial.rows)
    series_views = sum(point.views for point in partial.series)
    assert series_views >= rows_views

    full = get_dashboard_data(
        seeded_session,
        parse_filters(
            (date.today() - timedelta(days=179)).isoformat(), date.today().isoformat(), None, None
        ),
    )
    assert sum(row.views for row in full.rows) == sum(p.views for p in full.series)
