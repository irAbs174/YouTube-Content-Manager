"""Domain constants shared by every layer.

These mirror `src/lib/constants.ts` on the frontend — keep both in sync
(see tests/test_contract.py which asserts the API surface matches).
"""

from __future__ import annotations

from typing import Final

APP_NAME: Final[str] = "YouTube Content Manager API"

# ── YouTube visibility (Main sheet Status) ───────────────────────────────────
VISIBILITIES: Final[tuple[str, ...]] = ("Private", "Public")
STATUSES: Final[tuple[str, ...]] = VISIBILITIES  # alias used by /api/meta

STATUS_COLORS: Final[dict[str, str]] = {
    "Private": "#94a3b8",
    "Public": "#10b981",
}

DEFAULT_STATUS: Final[str] = "Private"
DEFAULT_VISIBILITY: Final[str] = "Private"

SESSION_COOKIE: Final[str] = "ytcm_session"
PASSWORD_MIN: Final[int] = 8

# ── Collections ("segments" on the dashboard) ────────────────────────────────
COLLECTIONS: Final[tuple[dict[str, object], ...]] = (
    {
        "name": "Linux Basics",
        "color": "#10b981",
        "sounds": ("Ubuntu Ambience", "Lo-fi Terminal", "Tux Groove"),
    },
    {
        "name": "Network Hacking",
        "color": "#06b6d4",
        "sounds": ("Synthwave Packet", "Dark Modem", "Port Scan Pulse"),
    },
    {
        "name": "Privilege Escalation",
        "color": "#f59e0b",
        "sounds": ("Rootkit Riddim", "Sudo Steps", "Kernel Bass"),
    },
    {
        "name": "OSINT",
        "color": "#8b5cf6",
        "sounds": ("Quiet Investigation", "Archive Dust", "Signal Trace"),
    },
    {
        "name": "Scripting & Automation",
        "color": "#f43f5e",
        "sounds": ("Bash Beats", "Cron Groove", "Pipe Funk"),
    },
)

COLLECTION_NAMES: Final[tuple[str, ...]] = tuple(c["name"] for c in COLLECTIONS)  # type: ignore[arg-type]
DEFAULT_COLLECTION: Final[str] = COLLECTION_NAMES[0]


def collection_color(name: str) -> str | None:
    """Hex colour for a collection name, or None when unknown."""
    for collection in COLLECTIONS:
        if collection["name"] == name:
            return str(collection["color"])
    return None


# ── Misc dropdown option lists ───────────────────────────────────────────────
EFFECT_OPTIONS: Final[tuple[str, ...]] = (
    "Glitch strips",
    "Neon glow",
    "Terminal scanlines",
    "Typewriter cursor",
    "Chromatic aberration",
    "Particle rain",
    "CRT curvature",
)

SUBTITLE_OPTIONS: Final[tuple[str, ...]] = (
    "None",
    "EN",
    "EN + ES",
    "EN + FR",
    "Auto captions",
)

DEFAULT_SUBTITLES: Final[str] = "EN"

# ── Episode field limits (mirrored by the Add-episode dialog) ────────────────
TITLE_MIN: Final[int] = 3
TITLE_MAX: Final[int] = 140
DURATION_MIN_SEC: Final[int] = 5
DURATION_MAX_SEC: Final[int] = 180
COMMAND_MAX: Final[int] = 120
TIP_MAX: Final[int] = 200
TEXT_FIELD_MAX: Final[int] = 200
MAX_DAYS_IN_FUTURE: Final[int] = 365

# ── Render pipeline ──────────────────────────────────────────────────────────
RENDER_STATUSES: Final[tuple[str, ...]] = ("none", "queued", "running", "done", "failed")

VIDEO_WIDTH: Final[int] = 1080
VIDEO_HEIGHT: Final[int] = 1920
VIDEO_FPS: Final[int] = 30

# ── Dashboard ────────────────────────────────────────────────────────────────
DEFAULT_RANGE_DAYS: Final[int] = 90
MAX_RANGE_DAYS: Final[int] = 730

# ── Live-refresh cadence the frontend polls with (ms) ────────────────────────
LIVE_INTERVAL_MS: Final[int] = 15_000
