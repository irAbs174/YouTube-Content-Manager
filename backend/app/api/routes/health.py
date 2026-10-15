"""GET /api/health — liveness + database reachability."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(session: Session = Depends(get_db)) -> JSONResponse:
    try:
        session.execute(text("select 1"))
        return JSONResponse({"ok": True})
    except Exception:  # noqa: BLE001 — any failure means unhealthy
        return JSONResponse({"ok": False}, status_code=500)
