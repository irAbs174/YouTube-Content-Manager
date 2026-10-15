"""GET /api/meta — domain values (statuses, collections, options).

Single source of truth so other clients (and future frontend code) can stay
in sync with `app.core.constants` without hardcoding.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.constants import (
    COLLECTIONS,
    EFFECT_OPTIONS,
    LIVE_INTERVAL_MS,
    STATUSES,
    SUBTITLE_OPTIONS,
)

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/meta")
def meta() -> dict:
    return {
        "statuses": list(STATUSES),
        "collections": [
            {
                "name": collection["name"],
                "color": collection["color"],
                "sounds": list(collection["sounds"]),  # type: ignore[arg-type]
            }
            for collection in COLLECTIONS
        ],
        "effectOptions": list(EFFECT_OPTIONS),
        "subtitleOptions": list(SUBTITLE_OPTIONS),
        "liveIntervalMs": LIVE_INTERVAL_MS,
    }
