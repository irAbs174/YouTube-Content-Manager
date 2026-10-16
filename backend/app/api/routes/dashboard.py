"""GET /api/dashboard — KPIs, daily series, filtered episode rows."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db
from app.db.models import User
from app.schemas.dashboard import DashboardData
from app.services import analytics

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardData)
def dashboard(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    collection: str | None = Query(default=None),
    status: str | None = Query(default=None),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> DashboardData:
    filters = analytics.parse_filters(from_, to, collection, status)
    # if no auth, use global data; if auth, scope to user
    return analytics.get_dashboard_data(session, filters, current_user)
