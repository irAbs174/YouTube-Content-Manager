"""GET /api/renders?ids=1,2,3 — lightweight render-state polling."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db
from app.db.models import User, YoutubeMain
from app.schemas.renders import RenderState

router = APIRouter(prefix="/api", tags=["renders"])

_MAX_IDS = 50


@router.get("/renders", response_model=list[RenderState])
def renders(
    ids: str = Query(default=""),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[RenderState]:
    parsed: list[int] = []
    for chunk in ids.split(","):
        try:
            value = int(chunk)
        except ValueError:
            continue
        if value > 0 and value not in parsed:
            parsed.append(value)
    if not parsed:
        return []

    rows = session.scalars(
        select(YoutubeMain).where(YoutubeMain.id.in_(parsed[:_MAX_IDS]))
    ).all()
    # if auth, filter to user's rows only (hide others)
    if current_user is not None:
        rows = [r for r in rows if r.user_id == current_user.id]
    by_id = {row.id: row for row in rows}
    # Preserve the caller's id order (the dashboard matches rows by id).
    return [
        RenderState(
            id=row.id,
            render_status=row.render_status,
            render_progress=row.render_progress,
            render_error=row.render_error,
            has_video=row.video_path is not None,
        )
        for value in parsed[:_MAX_IDS]
        if (row := by_id.get(value)) is not None
    ]
