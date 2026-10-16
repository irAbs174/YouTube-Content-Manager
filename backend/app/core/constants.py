"""Domain constants shared by every layer.

These mirror `src/lib/constants.ts` on the frontend — keep both in sync
(see tests/test_contract.py which asserts the API surface matches).
"""

from __future__ import annotations

from typing import Final

APP_NAME: Final[str] = "YouTube Content Manager API"

# ── YouTube visibility (Main sheet Status) ───────────────────────────────────
# The workbook's Status column is a select list: Public · Schedule · Private ·
# Draft · Not List.  Order matters — the Library renders the select in this
# exact order and `/api/meta` publishes it to every client.
VISIBILITIES: Final[tuple[str, ...]] = (
    "Public",
    "Schedule",
    "Private",
    "Draft",
    "Not List",
)
STATUSES: Final[tuple[str, ...]] = VISIBILITIES  # alias used by /api/meta

STATUS_COLORS: Final[dict[str, str]] = {
    "Public": "#10b981",
    "Schedule": "#f59e0b",
    "Private": "#94a3b8",
    "Draft": "#a78bfa",
    "Not List": "#64748b",
}

DEFAULT_STATUS: Final[str] = "Private"
DEFAULT_VISIBILITY: Final[str] = "Private"

SESSION_COOKIE: Final[str] = "ytcm_session"
PASSWORD_MIN: Final[int] = 8

# ── Collections ("segments" on the dashboard) ────────────────────────────────
# Each entry carries the Collections-sheet metadata (ID · Title · Description ·
# type · Share Link) so the Library "Collections" place is a real table.
COLLECTIONS: Final[tuple[dict[str, object], ...]] = (
    {
        "id": "COLL1",
        "name": "Linux Basics",
        "title": "Linux Basics | Zero to Linux Power User",
        "description": "One command per Short.\n\nLearn the 56 essential Linux commands you should know.",
        "type": "course",
        "shareLink": "https://www.youtube.com/playlist?list=PLlinuxbasics",
        "color": "#10b981",
        "sounds": ("Ubuntu Ambience", "Lo-fi Terminal", "Tux Groove"),
    },
    {
        "id": "COLL2",
        "name": "Network Hacking",
        "title": "Network Hacking | From Zero to Security Researcher",
        "description": "Learn network scanning and recon from zero.\n\nOne flag at a time.",
        "type": "Play List",
        "shareLink": "https://www.youtube.com/playlist?list=PLnetworkhacking",
        "color": "#06b6d4",
        "sounds": ("Synthwave Packet", "Dark Modem", "Port Scan Pulse"),
    },
    {
        "id": "COLL3",
        "name": "Privilege Escalation",
        "title": "Privilege Escalation | Linux Low-Hanging Fruit",
        "description": "Find the low-hanging fruit and turn it into root.\n\nPractical labs only.",
        "type": "Play List",
        "shareLink": "https://www.youtube.com/playlist?list=PLprivesc",
        "color": "#f59e0b",
        "sounds": ("Rootkit Riddim", "Sudo Steps", "Kernel Bass"),
    },
    {
        "id": "COLL4",
        "name": "OSINT",
        "title": "OSINT | Open-Source Intelligence in 60 Seconds",
        "description": "Collect intel the quiet way.\n\nReal targets, legal research.",
        "type": "Play List",
        "shareLink": "https://www.youtube.com/playlist?list=PLosint",
        "color": "#8b5cf6",
        "sounds": ("Quiet Investigation", "Archive Dust", "Signal Trace"),
    },
    {
        "id": "COLL5",
        "name": "Scripting & Automation",
        "title": "Scripting & Automation | Bash Like a Pro",
        "description": "Turn repetitive work into one-liners.\n\nBash, Python and make.",
        "type": "course",
        "shareLink": "https://www.youtube.com/playlist?list=PLscripting",
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

# ── Assets place (Assets sheet) ──────────────────────────────────────────────
# `Type` is a select list on the Assets sheet — "Fonts, img and ...".
ASSET_TYPES: Final[tuple[str, ...]] = (
    "Emojie",
    "Fonts",
    "img",
    "Video",
    "Audio",
    "SFX",
    "Template",
    "Logo",
)

# ── Languages place (Languages sheet) ────────────────────────────────────────
LANGUAGES: Final[tuple[str, ...]] = (
    "English",
    "English(USA)",
    "ENGLISH(UK)",
    "Russian",
    "Polish",
    "Persian",
    "Jepanies",
    "German",
    "French",
    "Arabic",
)

# ── Collections place: `type` select list ───────────────────────────────────
COLLECTION_TYPES: Final[tuple[str, ...]] = ("course", "Play List", "Series", "Single")

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
