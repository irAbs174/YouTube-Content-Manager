"""Render-state polling schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import CamelModel


class RenderState(CamelModel):
    """Lightweight render status — polled by the dashboard every 1.5 s."""

    id: int
    render_status: str
    render_progress: int = Field(ge=0, le=100)
    render_error: str | None = None
    has_video: bool = False


class RenderAccepted(BaseModel):
    ok: bool = True
    id: int
    render_status: str
