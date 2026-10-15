"""GET /api/renders?ids=1,2,3 — lightweight render-state polling."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import YoutubeContent
from app.schemas.renders import RenderState

router = APIRouter(prefix="/api", tags=["renders"])

_MAX_IDS = 50


@router.get("/renders", response_model=list[RenderState])
def renders(
    ids: str = Query(default=""),
    session: Session = Depends(get_db),
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
        select(YoutubeContent).where(YoutubeContent.id.in_(parsed[:_MAX_IDS]))
    ).all()
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
