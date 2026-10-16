"""Library "spec places" — the workbook sheets as queryable, editable tables.

The master workbook (`youTube-master-content-managment-v001.xlsx`) is the
source of truth.  Every sheet that carries data becomes a *place* inside the
Library:

    Main Library · Contents · Scenes · Episodes · Collections · Languages ·
    Assets · Subtitles

Each place declares its columns (label + type + select source) so the
frontend can render all of them from one generic table component, and each
row is a plain camelCase dict ready for the JSON contract.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import (
    ASSET_TYPES,
    COLLECTION_TYPES,
    LANGUAGES,
    VISIBILITIES,
)
from app.core.errors import NotFoundError, ValidationError
from app.db.models import (
    Asset,
    Collection,
    ContentItem,
    EpisodeScene,
    Language,
    SubtitleRow,
    User,
    YoutubeMain,
)

# ── column types understood by the frontend table renderer ───────────────────
COLUMN_TEXT = "text"
COLUMN_DATE = "date"
COLUMN_BOOL = "bool"
COLUMN_COUNT = "count"
COLUMN_NUMBER = "number"
COLUMN_SELECT = "select"


def _place(
    key: str,
    title: str,
    sheet: str,
    columns: list[dict[str, Any]],
    description: str = "",
) -> dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "sheet": sheet,
        "description": description,
        "columns": columns,
    }


def _column(
    key: str,
    label: str,
    type_: str = COLUMN_TEXT,
    *,
    source: str | None = None,
    editable: bool = True,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "type": type_,
        "source": source,
        "editable": editable,
    }


# ── the spec: places + columns (mirrors the workbook headers) ───────────────
def place_specs() -> list[dict[str, Any]]:
    """Declarative description of every Library place."""
    return [
        _place(
            "main",
            "Main Library",
            "YouTube Main 📌",
            [
                _column("episodeId", "Episode", COLUMN_SELECT, source="episodes", editable=False),
                _column("date", "Date", COLUMN_DATE),
                _column("title", "Title", COLUMN_TEXT),
                _column("status", "Status", COLUMN_SELECT, source="statuses"),
                _column("collectionId", "Collection", COLUMN_SELECT, source="collections"),
                _column("soundEffects", "Sound Effects", COLUMN_BOOL),
                _column("music", "Music", COLUMN_BOOL),
                _column("subtitlesCount", "Subtitles", COLUMN_COUNT, editable=False),
                _column("thumbnailReady", "Tumbnaill", COLUMN_BOOL),
            ],
            "One row per episode — the main content table.",
        ),
        _place(
            "contents",
            "Contents",
            "Contents 🖊️",
            [
                _column("code", "ID", COLUMN_TEXT, editable=False),
                _column("episodeId", "Episode", COLUMN_SELECT, source="episodes"),
                _column("languageId", "Language", COLUMN_SELECT, source="languages"),
                _column("title", "Title", COLUMN_TEXT),
                _column("description", "Description", COLUMN_TEXT),
                _column("tags", "Tags", COLUMN_TEXT),
                _column("subtitles", "Subtitles", COLUMN_BOOL),
                _column("relatedVideoId", "Related Video", COLUMN_SELECT, source="episodes"),
                _column("pinnedComment", "Pinned Comment", COLUMN_TEXT),
                _column("music", "Music", COLUMN_BOOL),
                _column("thumbnail", "Tumbnaill", COLUMN_BOOL),
            ],
            "Content blocks that make up an episode.",
        ),
        _place(
            "scenes",
            "Scenes",
            "Scences 🎬",
            [
                _column("code", "ID", COLUMN_TEXT, editable=False),
                _column("episodeId", "Episode", COLUMN_SELECT, source="episodes"),
                _column("sceneCount", "SCN Count", COLUMN_COUNT, editable=False),
                _column("sceneNumber", "SCN Number", COLUMN_NUMBER, editable=False),
                _column("title", "Scense Title", COLUMN_TEXT),
                _column("hook", "SCN Hook", COLUMN_TEXT),
                _column("scenario", "SCN Senario", COLUMN_TEXT),
                _column("body", "SCN Body", COLUMN_TEXT),
            ],
            "Scene breakdown — hook, scenario and body per scene.",
        ),
        _place(
            "episodes",
            "Episodes",
            "Episodes ⏭️",
            [
                _column("episodeNumber", "Episode number", COLUMN_NUMBER),
                _column("collectionId", "Collection", COLUMN_SELECT, source="collections"),
                _column("episodeDisplay", "Episode", COLUMN_TEXT, editable=False),
                _column("sharedLink", "Shared Link", COLUMN_TEXT),
                _column("sceneCount", "SCN Count", COLUMN_COUNT, editable=False),
            ],
            "Episode register with the published share link.",
        ),
        _place(
            "collections",
            "Collections",
            "Collections 📃",
            [
                _column("code", "ID", COLUMN_TEXT, editable=False),
                _column("name", "name", COLUMN_TEXT),
                _column("title", "Title", COLUMN_TEXT),
                _column("description", "Description", COLUMN_TEXT),
                _column("type", "type", COLUMN_SELECT, source="collectionTypes"),
                _column("shareLink", "Share Link", COLUMN_TEXT),
            ],
            "Playlist / course lookup.",
        ),
        _place(
            "languages",
            "Languages",
            "Languages 🌍",
            [
                _column("id", "ID", COLUMN_NUMBER, editable=False),
                _column("name", "Name", COLUMN_TEXT),
            ],
            "Subtitle & content language lookup.",
        ),
        _place(
            "assets",
            "Assets",
            "Assets 👁️👁️",
            [
                _column("code", "Assets ID", COLUMN_TEXT, editable=False),
                _column("type", "Type", COLUMN_SELECT, source="assetTypes"),
                _column("name", "Name", COLUMN_TEXT),
                _column("context", "Context", COLUMN_TEXT),
                _column("description", "Description", COLUMN_TEXT),
                _column("storageLocation", "Storage Location", COLUMN_TEXT),
            ],
            "Emoji, font and image assets used by the renderer.",
        ),
        _place(
            "subtitles",
            "Subtitle",
            "Subtitles 🔍",
            [
                _column("episodeId", "Episode", COLUMN_SELECT, source="episodes"),
                _column("languageId", "Language", COLUMN_SELECT, source="languages"),
                _column("timeDuration", "Time duration", COLUMN_TEXT),
                _column("text", "Text", COLUMN_TEXT),
            ],
            "Timed subtitle cues per episode and language.",
        ),
    ]


# ── helpers ─────────────────────────────────────────────────────────────────
def resolve_user(session: Session, current_user: User | None) -> User | None:
    """Authenticated user, or the demo/first user for legacy (cookie-less) calls."""
    if current_user is not None:
        return current_user
    return session.scalars(select(User).limit(1)).first()


def _scoped(query, model, user: User | None):
    if user is None:
        return query
    return query.where(model.user_id == user.id)


def _episode_display(row: YoutubeMain) -> str:
    try:
        return row.episode_display
    except Exception:
        return f"Episode #{row.episode_number}"


def _episodes(session: Session, user: User | None) -> list[YoutubeMain]:
    query = select(YoutubeMain).order_by(YoutubeMain.episode_number, YoutubeMain.id)
    return list(session.scalars(_scoped(query, YoutubeMain, user)).all())


def _scene_counts(session: Session, episode_ids: list[int]) -> dict[int, int]:
    if not episode_ids:
        return {}
    rows = session.execute(
        select(EpisodeScene.content_id, func.count(EpisodeScene.id))
        .where(EpisodeScene.content_id.in_(episode_ids))
        .group_by(EpisodeScene.content_id)
    ).all()
    return {int(cid): int(cnt) for cid, cnt in rows}


def _subtitle_counts(session: Session, episode_ids: list[int]) -> dict[int, int]:
    if not episode_ids:
        return {}
    rows = session.execute(
        select(SubtitleRow.episode_id, func.count(SubtitleRow.id))
        .where(SubtitleRow.episode_id.in_(episode_ids))
        .group_by(SubtitleRow.episode_id)
    ).all()
    return {int(eid): int(cnt) for eid, cnt in rows}


def _format_timecode(seconds: int) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _parse_timecode(raw: str) -> int:
    """Parse `MM:SS` (or plain seconds) into seconds."""
    text = _clean(raw)
    if not text:
        raise ValidationError("Invalid time duration — expected MM:SS")
    if ":" in text:
        minutes, _, seconds = text.partition(":")
        try:
            return int(minutes) * 60 + int(seconds)
        except ValueError as exc:
            raise ValidationError("Invalid time duration — expected MM:SS") from exc
    try:
        return int(text)
    except ValueError as exc:
        raise ValidationError("Invalid time duration — expected MM:SS") from exc


def parse_time_duration(raw: str) -> tuple[int, int]:
    """Parse a `00:00–00:05` range (en dash, hyphen or a bare `MM:SS`)."""
    text = _clean(raw)
    if not text:
        raise ValidationError("Invalid time duration — expected MM:SS–MM:SS")
    for separator in ("–", "-", "..", " to "):
        if separator in text:
            left, _, right = text.partition(separator)
            return _parse_timecode(left), _parse_timecode(right)
    # A single timecode means "from the start".
    start = _parse_timecode(text)
    return 0, start


def _episode_label(row: YoutubeMain) -> str:
    return _episode_display(row)


# ── select-list options ─────────────────────────────────────────────────────
def select_options(session: Session, user: User | None) -> dict[str, list[Any]]:
    """Every option list the Library selects need."""
    episodes = _episodes(session, user)
    collections = list(session.scalars(select(Collection).order_by(Collection.name)).all())
    languages = list(session.scalars(select(Language).order_by(Language.id)).all())
    return {
        "episodes": [{"id": row.id, "label": _episode_label(row)} for row in episodes],
        "collections": [{"id": row.id, "label": row.name} for row in collections],
        "languages": [{"id": row.id, "label": row.name} for row in languages],
        "statuses": list(VISIBILITIES),
        "assetTypes": list(ASSET_TYPES),
        "collectionTypes": list(COLLECTION_TYPES),
    }


# ── places: row builders ────────────────────────────────────────────────────
def list_main(session: Session, user: User | None) -> list[dict[str, Any]]:
    episodes = _episodes(session, user)
    episode_ids = [row.id for row in episodes]
    subtitle_counts = _subtitle_counts(session, episode_ids)
    rows: list[dict[str, Any]] = []
    for row in episodes:
        rows.append(
            {
                "id": row.id,
                "episodeId": row.id,
                "episodeNumber": row.episode_number,
                "episodeDisplay": _episode_display(row),
                "date": row.date.isoformat() if row.date else "",
                "title": row.title,
                "status": row.visibility,
                "collectionId": row.collection_id,
                "collection": row.collection_name,
                "soundEffects": bool(row.sound_effects),
                "music": bool(row.music),
                "subtitlesCount": subtitle_counts.get(row.id, 0),
                "thumbnailReady": bool(row.thumbnail_ready),
                "sharedLink": row.shared_link,
                "scheduleAt": row.schedule_at.isoformat() if row.schedule_at else "",
            }
        )
    return rows


def list_contents(session: Session, user: User | None) -> list[dict[str, Any]]:
    query = (
        select(ContentItem)
        .order_by(ContentItem.episode_id, ContentItem.position, ContentItem.id)
    )
    rows = list(session.scalars(_scoped(query, ContentItem, user)).all())
    episodes = {row.id: row for row in _episodes(session, user)}
    out: list[dict[str, Any]] = []
    for row in rows:
        episode = episodes.get(row.episode_id)
        related = episodes.get(row.related_video_id) if row.related_video_id else None
        out.append(
            {
                "id": row.id,
                "code": row.code,
                "episodeId": row.episode_id,
                "episodeDisplay": _episode_display(episode) if episode else "",
                "languageId": row.language_id,
                "language": row.language.name if row.language else "",
                "title": row.title,
                "description": row.description,
                "tags": row.tags,
                "subtitles": bool(row.subtitles),
                "relatedVideoId": row.related_video_id,
                "relatedVideo": _episode_display(related) if related else "",
                "pinnedComment": row.pinned_comment,
                "music": bool(row.music),
                "thumbnail": bool(row.thumbnail),
            }
        )
    return out


def list_scenes(session: Session, user: User | None) -> list[dict[str, Any]]:
    query = select(EpisodeScene).order_by(EpisodeScene.content_id, EpisodeScene.position)
    rows = list(session.scalars(query).all())
    episodes = {row.id: row for row in _episodes(session, user)}
    counts = _scene_counts(session, list(episodes))
    out: list[dict[str, Any]] = []
    for row in rows:
        episode = episodes.get(row.content_id)
        if episode is None:
            continue  # scene of another user's episode
        out.append(
            {
                "id": row.id,
                "code": f"SCN{row.position + 1}",
                "episodeId": row.content_id,
                "episodeDisplay": _episode_display(episode),
                "sceneCount": counts.get(row.content_id, 0),
                "sceneNumber": row.position + 1,
                "title": row.title,
                "hook": row.hook,
                "scenario": row.scenario,
                "body": row.body,
                "durationSec": row.duration_sec,
            }
        )
    return out


def list_episodes(session: Session, user: User | None) -> list[dict[str, Any]]:
    episodes = _episodes(session, user)
    counts = _scene_counts(session, [row.id for row in episodes])
    out: list[dict[str, Any]] = []
    for row in episodes:
        out.append(
            {
                "id": row.id,
                "episodeNumber": row.episode_number,
                "collectionId": row.collection_id,
                "collection": row.collection_name,
                "episodeDisplay": _episode_display(row),
                "sharedLink": row.shared_link,
                "sceneCount": counts.get(row.id, 0),
            }
        )
    return out


def list_collections(session: Session, user: User | None) -> list[dict[str, Any]]:
    rows = session.scalars(select(Collection).order_by(Collection.name)).all()
    return [
        {
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "title": row.title,
            "description": row.description,
            "type": row.type,
            "shareLink": row.share_link,
            "color": row.color,
        }
        for row in rows
    ]


def list_languages(session: Session, user: User | None) -> list[dict[str, Any]]:
    rows = session.scalars(select(Language).order_by(Language.id)).all()
    return [{"id": row.id, "name": row.name} for row in rows]


def list_assets(session: Session, user: User | None) -> list[dict[str, Any]]:
    rows = session.scalars(select(Asset).order_by(Asset.id)).all()
    return [
        {
            "id": row.id,
            "code": row.code,
            "type": row.type,
            "name": row.name,
            "context": row.context,
            "description": row.description,
            "storageLocation": row.storage_location,
        }
        for row in rows
    ]


def list_subtitles(session: Session, user: User | None) -> list[dict[str, Any]]:
    query = select(SubtitleRow).order_by(SubtitleRow.episode_id, SubtitleRow.start_sec)
    rows = list(session.scalars(_scoped(query, SubtitleRow, user)).all())
    episodes = {row.id: row for row in _episodes(session, user)}
    out: list[dict[str, Any]] = []
    for row in rows:
        episode = episodes.get(row.episode_id)
        out.append(
            {
                "id": row.id,
                "episodeId": row.episode_id,
                "episodeDisplay": _episode_display(episode) if episode else "",
                "languageId": row.language_id,
                "language": row.language.name if row.language else "",
                "timeDuration": f"{_format_timecode(row.start_sec)}–{_format_timecode(row.end_sec)}",
                "startSec": row.start_sec,
                "endSec": row.end_sec,
                "text": row.text,
            }
        )
    return out


# ── mutations ───────────────────────────────────────────────────────────────
def _clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _as_bool(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    raw = _clean(value).lower()
    if raw in ("true", "1", "yes", "y", "on"):
        return True
    if raw in ("false", "0", "no", "n", "off", ""):
        return False
    raise ValidationError(f"Invalid boolean for `{field}`")


def _as_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValidationError(f"Invalid number for `{field}`")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    raw = _clean(value)
    try:
        return int(raw)
    except ValueError as exc:
        raise ValidationError(f"Invalid number for `{field}`") from exc


def _as_date(value: Any, field: str) -> date:
    if isinstance(value, date):
        return value
    raw = _clean(value)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValidationError(f"Invalid date for `{field}` — expected YYYY-MM-DD") from exc


def _as_datetime(value: Any, field: str) -> datetime | None:
    """Accept an ISO datetime (or a plain date) for the schedule moment."""
    if value is None or _clean(value) == "":
        return None
    if isinstance(value, datetime):
        return value
    raw = _clean(value)
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        pass
    try:
        return datetime.combine(date.fromisoformat(raw), datetime.min.time())
    except ValueError as exc:
        raise ValidationError(
            f"Invalid datetime for `{field}` — expected ISO-8601"
        ) from exc


def _reject_unknown(payload: dict[str, Any], allowed: set[str]) -> None:
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValidationError(f"Unknown field(s): {', '.join(unknown)}")


def _get_episode(session: Session, episode_id: int, user: User | None) -> YoutubeMain:
    row = session.get(YoutubeMain, episode_id)
    if row is None or (user is not None and row.user_id != user.id):
        raise NotFoundError("Episode not found")
    return row


def _get_collection(session: Session, collection_id: int) -> Collection:
    row = session.get(Collection, collection_id)
    if row is None:
        raise NotFoundError("Collection not found")
    return row


def _get_language(session: Session, language_id: int) -> Language:
    row = session.get(Language, language_id)
    if row is None:
        raise NotFoundError("Language not found")
    return row


def patch_main(
    session: Session, episode_id: int, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    row = _get_episode(session, episode_id, user)
    _reject_unknown(
        payload,
        {
            "title",
            "date",
            "status",
            "collectionId",
            "soundEffects",
            "music",
            "thumbnailReady",
            "sharedLink",
            "scheduleAt",
        },
    )
    if "title" in payload:
        title = _clean(payload["title"])
        if len(title) < 3:
            raise ValidationError("Title must be at least 3 characters")
        row.title = title
    if "date" in payload:
        row.date = _as_date(payload["date"], "date")
    if "status" in payload:
        status = _clean(payload["status"])
        if status not in VISIBILITIES:
            raise ValidationError(f"Unknown status: {status}")
        row.visibility = status
    if "collectionId" in payload:
        raw = payload["collectionId"]
        if raw is None or _clean(raw) == "":
            row.collection_id = None
            row.collection = ""
        else:
            collection = _get_collection(session, _as_int(raw, "collectionId"))
            row.collection_id = collection.id
            row.collection = collection.name
    if "soundEffects" in payload:
        row.sound_effects = _as_bool(payload["soundEffects"], "soundEffects")
    if "music" in payload:
        row.music = _as_bool(payload["music"], "music")
    if "thumbnailReady" in payload:
        row.thumbnail_ready = _as_bool(payload["thumbnailReady"], "thumbnailReady")
    if "sharedLink" in payload:
        row.shared_link = _clean(payload["sharedLink"])
    if "scheduleAt" in payload:
        row.schedule_at = _as_datetime(payload["scheduleAt"], "scheduleAt")
    session.commit()
    session.refresh(row)
    return _main_row(session, row)


def _main_row(session: Session, row: YoutubeMain) -> dict[str, Any]:
    count = session.scalar(
        select(func.count(SubtitleRow.id)).where(SubtitleRow.episode_id == row.id)
    )
    return {
        "id": row.id,
        "episodeId": row.id,
        "episodeNumber": row.episode_number,
        "episodeDisplay": _episode_display(row),
        "date": row.date.isoformat() if row.date else "",
        "title": row.title,
        "status": row.visibility,
        "collectionId": row.collection_id,
        "collection": row.collection_name,
        "soundEffects": bool(row.sound_effects),
        "music": bool(row.music),
        "subtitlesCount": int(count or 0),
        "thumbnailReady": bool(row.thumbnail_ready),
        "sharedLink": row.shared_link,
        "scheduleAt": row.schedule_at.isoformat() if row.schedule_at else "",
    }


def patch_content(
    session: Session, content_id: int, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    row = session.get(ContentItem, content_id)
    if row is None or (user is not None and row.user_id != user.id):
        raise NotFoundError("Content not found")
    _reject_unknown(
        payload,
        {
            "episodeId",
            "languageId",
            "title",
            "description",
            "tags",
            "subtitles",
            "relatedVideoId",
            "pinnedComment",
            "music",
            "thumbnail",
        },
    )
    if "episodeId" in payload:
        row.episode_id = _get_episode(session, _as_int(payload["episodeId"], "episodeId"), user).id
    if "languageId" in payload:
        raw = payload["languageId"]
        row.language_id = (
            None if raw is None or _clean(raw) == "" else _get_language(session, _as_int(raw, "languageId")).id
        )
    if "relatedVideoId" in payload:
        raw = payload["relatedVideoId"]
        row.related_video_id = (
            None
            if raw is None or _clean(raw) == ""
            else _get_episode(session, _as_int(raw, "relatedVideoId"), user).id
        )
    if "title" in payload:
        row.title = _clean(payload["title"])
    if "description" in payload:
        row.description = _clean(payload["description"])
    if "tags" in payload:
        row.tags = _clean(payload["tags"])
    if "subtitles" in payload:
        row.subtitles = _as_bool(payload["subtitles"], "subtitles")
    if "pinnedComment" in payload:
        row.pinned_comment = _clean(payload["pinnedComment"])
    if "music" in payload:
        row.music = _as_bool(payload["music"], "music")
    if "thumbnail" in payload:
        row.thumbnail = _as_bool(payload["thumbnail"], "thumbnail")
    session.commit()
    session.refresh(row)
    return _content_row(row)


def _content_row(row: ContentItem) -> dict[str, Any]:
    return {
        "id": row.id,
        "code": row.code,
        "episodeId": row.episode_id,
        "episodeDisplay": row.episode.episode_display if row.episode else "",
        "languageId": row.language_id,
        "language": row.language.name if row.language else "",
        "title": row.title,
        "description": row.description,
        "tags": row.tags,
        "subtitles": bool(row.subtitles),
        "relatedVideoId": row.related_video_id,
        "relatedVideo": row.related_video.episode_display if row.related_video else "",
        "pinnedComment": row.pinned_comment,
        "music": bool(row.music),
        "thumbnail": bool(row.thumbnail),
    }


def patch_scene(
    session: Session, scene_id: int, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    row = session.get(EpisodeScene, scene_id)
    if row is None:
        raise NotFoundError("Scene not found")
    episode = _get_episode(session, row.content_id, user)
    _reject_unknown(payload, {"title", "hook", "scenario", "body"})
    for field in ("title", "hook", "scenario", "body"):
        if field in payload:
            setattr(row, field, _clean(payload[field]))
    session.commit()
    session.refresh(row)
    counts = _scene_counts(session, [episode.id])
    return {
        "id": row.id,
        "code": f"SCN{row.position + 1}",
        "episodeId": episode.id,
        "episodeDisplay": _episode_display(episode),
        "sceneCount": counts.get(episode.id, 0),
        "sceneNumber": row.position + 1,
        "title": row.title,
        "hook": row.hook,
        "scenario": row.scenario,
        "body": row.body,
        "durationSec": row.duration_sec,
    }


def patch_episode_register(
    session: Session, episode_id: int, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    """Episodes place: episode number · collection · shared link."""
    row = _get_episode(session, episode_id, user)
    _reject_unknown(payload, {"episodeNumber", "collectionId", "sharedLink"})
    if "episodeNumber" in payload:
        number = _as_int(payload["episodeNumber"], "episodeNumber")
        if number < 1:
            raise ValidationError("Episode number must be 1 or greater")
        row.episode_number = number
    if "collectionId" in payload:
        raw = payload["collectionId"]
        if raw is None or _clean(raw) == "":
            row.collection_id = None
            row.collection = ""
        else:
            collection = _get_collection(session, _as_int(raw, "collectionId"))
            row.collection_id = collection.id
            row.collection = collection.name
    if "sharedLink" in payload:
        row.shared_link = _clean(payload["sharedLink"])
    session.commit()
    session.refresh(row)
    counts = _scene_counts(session, [row.id])
    return {
        "id": row.id,
        "episodeNumber": row.episode_number,
        "collectionId": row.collection_id,
        "collection": row.collection_name,
        "episodeDisplay": _episode_display(row),
        "sharedLink": row.shared_link,
        "sceneCount": counts.get(row.id, 0),
    }


def patch_collection(
    session: Session, collection_id: int, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    row = session.get(Collection, collection_id)
    if row is None:
        raise NotFoundError("Collection not found")
    _reject_unknown(payload, {"name", "title", "description", "type", "shareLink"})
    if "name" in payload:
        name = _clean(payload["name"])
        if not name:
            raise ValidationError("Collection name cannot be empty")
        row.name = name
    if "title" in payload:
        row.title = _clean(payload["title"])
    if "description" in payload:
        row.description = _clean(payload["description"])
    if "type" in payload:
        row.type = _clean(payload["type"])
    if "shareLink" in payload:
        row.share_link = _clean(payload["shareLink"])
    session.commit()
    session.refresh(row)
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "title": row.title,
        "description": row.description,
        "type": row.type,
        "shareLink": row.share_link,
        "color": row.color,
    }


def patch_language(
    session: Session, language_id: int, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    row = session.get(Language, language_id)
    if row is None:
        raise NotFoundError("Language not found")
    _reject_unknown(payload, {"name"})
    if "name" in payload:
        name = _clean(payload["name"])
        if not name:
            raise ValidationError("Language name cannot be empty")
        row.name = name
    session.commit()
    session.refresh(row)
    return {"id": row.id, "name": row.name}


def patch_asset(
    session: Session, asset_id: int, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    row = session.get(Asset, asset_id)
    if row is None:
        raise NotFoundError("Asset not found")
    _reject_unknown(payload, {"type", "name", "context", "description", "storageLocation"})
    if "type" in payload:
        row.type = _clean(payload["type"])
    if "name" in payload:
        row.name = _clean(payload["name"])
    if "context" in payload:
        row.context = _clean(payload["context"])
    if "description" in payload:
        row.description = _clean(payload["description"])
    if "storageLocation" in payload:
        row.storage_location = _clean(payload["storageLocation"])
    session.commit()
    session.refresh(row)
    return {
        "id": row.id,
        "code": row.code,
        "type": row.type,
        "name": row.name,
        "context": row.context,
        "description": row.description,
        "storageLocation": row.storage_location,
    }


def patch_subtitle(
    session: Session, subtitle_id: int, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    row = session.get(SubtitleRow, subtitle_id)
    if row is None or (user is not None and row.user_id != user.id):
        raise NotFoundError("Subtitle not found")
    _reject_unknown(
        payload, {"episodeId", "languageId", "startSec", "endSec", "text", "timeDuration"}
    )
    if "episodeId" in payload:
        row.episode_id = _get_episode(session, _as_int(payload["episodeId"], "episodeId"), user).id
    if "languageId" in payload:
        raw = payload["languageId"]
        row.language_id = (
            None if raw is None or _clean(raw) == "" else _get_language(session, _as_int(raw, "languageId")).id
        )
    if "timeDuration" in payload:
        start, end = parse_time_duration(str(payload["timeDuration"]))
        row.start_sec = start
        row.end_sec = end
    if "startSec" in payload:
        row.start_sec = max(0, _as_int(payload["startSec"], "startSec"))
    if "endSec" in payload:
        row.end_sec = max(0, _as_int(payload["endSec"], "endSec"))
    if "text" in payload:
        row.text = _clean(payload["text"])
    session.commit()
    session.refresh(row)
    _sync_subtitle_count(session, row.episode_id)
    session.refresh(row)
    return _subtitle_row(row)


def _subtitle_row(row: SubtitleRow) -> dict[str, Any]:
    return {
        "id": row.id,
        "episodeId": row.episode_id,
        "episodeDisplay": row.episode.episode_display if row.episode else "",
        "languageId": row.language_id,
        "language": row.language.name if row.language else "",
        "timeDuration": f"{_format_timecode(row.start_sec)}–{_format_timecode(row.end_sec)}",
        "startSec": row.start_sec,
        "endSec": row.end_sec,
        "text": row.text,
    }


def _sync_subtitle_count(session: Session, episode_id: int) -> None:
    """Keep the Main sheet's `Subtitles` counter in step with the cues."""
    episode = session.get(YoutubeMain, episode_id)
    if episode is None:
        return
    count = session.scalar(
        select(func.count(SubtitleRow.id)).where(SubtitleRow.episode_id == episode_id)
    )
    episode.subtitles_count = int(count or 0)
    session.commit()


# ── creation ────────────────────────────────────────────────────────────────
def create_language(session: Session, payload: dict[str, Any], user: User | None) -> dict[str, Any]:
    name = _clean(payload.get("name"))
    if not name:
        raise ValidationError("Language name cannot be empty")
    existing = session.scalar(select(Language).where(Language.name == name))
    if existing is not None:
        raise ValidationError(f"Language '{name}' already exists")
    row = Language(name=name)
    session.add(row)
    session.commit()
    session.refresh(row)
    return {"id": row.id, "name": row.name}


def create_asset(session: Session, payload: dict[str, Any], user: User | None) -> dict[str, Any]:
    code = _clean(payload.get("code"))
    if not code:
        count = session.scalar(select(func.count(Asset.id))) or 0
        code = f"AST{count + 1}"
    if session.scalar(select(Asset).where(Asset.code == code)) is not None:
        raise ValidationError(f"Asset '{code}' already exists")
    row = Asset(
        code=code,
        type=_clean(payload.get("type")),
        name=_clean(payload.get("name")),
        context=_clean(payload.get("context")),
        description=_clean(payload.get("description")),
        storage_location=_clean(payload.get("storageLocation")),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return {
        "id": row.id,
        "code": row.code,
        "type": row.type,
        "name": row.name,
        "context": row.context,
        "description": row.description,
        "storageLocation": row.storage_location,
    }


def create_content(
    session: Session, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    owner = resolve_user(session, user)
    if owner is None:
        raise ValidationError("No user to own this content")
    episode_id = payload.get("episodeId")
    if episode_id is None:
        raise ValidationError("`episodeId` is required")
    episode = _get_episode(session, _as_int(episode_id, "episodeId"), user)
    position = session.scalar(
        select(func.count(ContentItem.id)).where(ContentItem.episode_id == episode.id)
    )
    code = _clean(payload.get("code")) or f"CNT{(position or 0) + 1}"
    row = ContentItem(
        user_id=episode.user_id,
        episode_id=episode.id,
        language_id=(
            None
            if payload.get("languageId") in (None, "")
            else _get_language(session, _as_int(payload["languageId"], "languageId")).id
        ),
        related_video_id=(
            None
            if payload.get("relatedVideoId") in (None, "")
            else _get_episode(session, _as_int(payload["relatedVideoId"], "relatedVideoId"), user).id
        ),
        code=code,
        position=int(position or 0),
        title=_clean(payload.get("title")),
        description=_clean(payload.get("description")),
        tags=_clean(payload.get("tags")),
        subtitles=_as_bool(payload.get("subtitles", False), "subtitles"),
        pinned_comment=_clean(payload.get("pinnedComment")),
        music=_as_bool(payload.get("music", False), "music"),
        thumbnail=_as_bool(payload.get("thumbnail", False), "thumbnail"),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _content_row(row)


def create_subtitle(
    session: Session, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    episode_id = payload.get("episodeId")
    if episode_id is None:
        raise ValidationError("`episodeId` is required")
    episode = _get_episode(session, _as_int(episode_id, "episodeId"), user)
    row = SubtitleRow(
        user_id=episode.user_id,
        episode_id=episode.id,
        language_id=(
            None
            if payload.get("languageId") in (None, "")
            else _get_language(session, _as_int(payload["languageId"], "languageId")).id
        ),
        start_sec=max(0, _as_int(payload.get("startSec", 0), "startSec")),
        end_sec=max(0, _as_int(payload.get("endSec", 0), "endSec")),
        text=_clean(payload.get("text")),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    _sync_subtitle_count(session, row.episode_id)
    session.refresh(row)
    return _subtitle_row(row)


def create_collection(
    session: Session, payload: dict[str, Any], user: User | None
) -> dict[str, Any]:
    name = _clean(payload.get("name"))
    if not name:
        raise ValidationError("Collection name cannot be empty")
    if session.scalar(select(Collection).where(Collection.name == name)) is not None:
        raise ValidationError(f"Collection '{name}' already exists")
    count = session.scalar(select(func.count(Collection.id))) or 0
    row = Collection(
        name=name,
        code=_clean(payload.get("code")) or f"COLL{count + 1}",
        title=_clean(payload.get("title")),
        description=_clean(payload.get("description")),
        type=_clean(payload.get("type")),
        share_link=_clean(payload.get("shareLink")),
        color=_clean(payload.get("color")) or "#94a3b8",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "title": row.title,
        "description": row.description,
        "type": row.type,
        "shareLink": row.share_link,
        "color": row.color,
    }


# ── back-compat helper used by the seeder ──────────────────────────────────
def ensure_languages(session: Session) -> dict[str, Language]:
    """Make sure every language of the `LANGUAGES` constant exists."""
    existing = {row.name: row for row in session.scalars(select(Language)).all()}
    for name in LANGUAGES:
        if name not in existing:
            row = Language(name=name)
            session.add(row)
            session.flush()
            existing[name] = row
    session.flush()
    return existing
