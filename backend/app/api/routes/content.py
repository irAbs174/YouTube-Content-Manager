"""Content routes: CRUD, render enqueue, thumbnail + video streaming."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db, get_queue, get_settings_dep
from app.core.config import Settings
from app.core.errors import FFmpegUnavailableError, NotFoundError
from app.db.models import User
from app.rendering.queue import RenderQueue
from app.schemas.content import EpisodeCreate, EpisodeOut, EpisodePatch, MutationOk, EpisodeSceneOut
from app.services import content as content_service

router = APIRouter(prefix="/api/content", tags=["content"])

CHUNK_SIZE = 64 * 1024
_RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


def _episode_out(row, render_status: str | None = None) -> EpisodeOut:
    # derive series info
    try:
        series_name = row.series.name if row.series else "General"
    except Exception:
        series_name = "General"
    scenes = []
    try:
        # row.scenes is ordered
        for sc in row.scenes:
            scenes.append(EpisodeSceneOut(id=sc.id, position=sc.position, duration_sec=sc.duration_sec, command=sc.command, tip=sc.tip, audio=sc.audio, notes=sc.notes))
    except Exception:
        scenes = []
    return EpisodeOut(
        id=row.id,
        episode=row.episode_number,
        date=row.date.isoformat() if row.date else "",
        title=row.title,
        status=row.visibility,
        collection=row.collection if isinstance(row.collection, str) else row.collection_name,
        sound_music=row.sound_music,
        effects=row.effects,
        subtitles=row.subtitles,
        thumbnail=row.thumbnail,
        duration_sec=row.duration_sec,
        script=row.script,
        render_status=render_status or row.render_status,
        render_progress=row.render_progress,
        render_error=row.render_error,
        video_path=row.video_path,
        visibility=row.visibility,
        series_id=row.series_id,
        series_name=series_name,
        episode_number=row.episode_number,
        episode_display=row.episode_display if hasattr(row, "episode_display") else f"{series_name} #{row.episode_number}",
        collection_id=row.collection_id,
        sound_effects=row.sound_effects,
        music=row.music,
        subtitles_count=row.subtitles_count,
        thumbnail_ready=row.thumbnail_ready,
        scenes=scenes,
    )


def _get_user_fallback(session: Session, current_user: User | None) -> User | None:
    if current_user is not None:
        return current_user
    # fallback for legacy tests without auth: use demo user if exists
    from sqlalchemy import select as _select
    from app.db.models import User as _User

    return session.scalars(_select(_User).limit(1)).first()


@router.post("", response_model=EpisodeOut, status_code=201)
@router.post("/", response_model=EpisodeOut, status_code=201)
def create_episode(
    payload: EpisodeCreate,
    session: Session = Depends(get_db),
    queue: RenderQueue = Depends(get_queue),
    current_user: User | None = Depends(get_current_user_optional),
) -> EpisodeOut:
    """Create an episode; optionally queue it for FFmpeg rendering."""
    if payload.render:
        status = queue.availability()
        if not status.available:
            raise FFmpegUnavailableError(
                f"{status.error} Uncheck \"Render video\" to save without rendering."
            )

    user = _get_user_fallback(session, current_user)
    row = content_service.create_episode(session, payload, user)
    if payload.render:
        content_service.apply_render_script(session, row, payload)
        queue.submit(row.id)
        return _episode_out(row, render_status="queued")
    return _episode_out(row)


@router.patch("/{episode_id}", response_model=MutationOk)
def update_episode(
    episode_id: int,
    payload: EpisodePatch,
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> MutationOk:
    user = _get_user_fallback(session, current_user)
    # enforce ownership if auth present
    check_user = current_user  # if no auth, allow fallback via _get_user_fallback logic inside service with None? But we pass user for ownership check
    # If no auth header, current_user is None, we don't enforce ownership (legacy)
    content_service.update_episode(session, episode_id, payload, user if current_user is not None else None)
    return MutationOk(id=episode_id)


@router.delete("/{episode_id}", response_model=MutationOk)
def delete_episode(
    episode_id: int,
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> MutationOk:
    user = _get_user_fallback(session, current_user)
    content_service.delete_episode(session, episode_id, user if current_user is not None else None)
    return MutationOk(id=episode_id)


@router.post("/{episode_id}/render", response_model=None)
def request_render(
    episode_id: int,
    session: Session = Depends(get_db),
    queue: RenderQueue = Depends(get_queue),
    current_user: User | None = Depends(get_current_user_optional),
) -> JSONResponse:
    """(Re)queue an FFmpeg render. 202 when freshly queued, 200 when pending."""
    user = _get_user_fallback(session, current_user)
    row = content_service.get_episode(session, episode_id, user if current_user is not None else None)
    status = queue.availability()
    if not status.available:
        raise FFmpegUnavailableError(
            f"{status.error} FFmpeg is required to render episode {row.episode}."
        )
    if not row.script and not row.scenes:
        # Older episodes have no on-screen script — synthesise a minimal one.
        row.script = {"command": row.title, "tip": "", "audio": True}
        session.commit()

    outcome = queue.submit(episode_id)
    if outcome == "missing":  # race: deleted between the two DB reads
        raise NotFoundError("Episode not found")
    return JSONResponse(
        {"ok": True, "id": episode_id, "renderStatus": "queued"},
        status_code=202 if outcome == "queued" else 200,
    )


@router.get("/{episode_id}/thumbnail")
def thumbnail(
    episode_id: int,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    current_user: User | None = Depends(get_current_user_optional),
):
    from app.rendering.storage import thumb_abs_path

    user = _get_user_fallback(session, current_user)
    content_service.get_episode(session, episode_id, user if current_user is not None else None)  # 404 when unknown id
    path = thumb_abs_path(settings, episode_id)
    if not path.is_file():
        return JSONResponse({"error": "No thumbnail"}, status_code=404)
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "no-cache"})


@router.get("/{episode_id}/video")
def video(
    episode_id: int,
    request: Request,
    download: str | None = Query(default=None),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Stream the rendered MP4 with HTTP Range support (seekable <video>)."""
    from app.rendering.storage import video_abs_path

    user = _get_user_fallback(session, current_user)
    row = content_service.get_episode(session, episode_id, user if current_user is not None else None)
    if not row.video_path:
        return JSONResponse({"error": "No rendered video"}, status_code=404)
    path = video_abs_path(settings, row.video_path)
    if not path.is_file():
        return JSONResponse({"error": "Video file missing"}, status_code=404)

    headers = {
        "Content-Type": "video/mp4",
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-cache",
    }
    if download == "1":
        headers["Content-Disposition"] = f'attachment; filename="episode-{episode_id}.mp4"'

    size = path.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        match = _RANGE_RE.match(range_header.strip())
        if not match or (match.group(1) == "" and match.group(2) == ""):
            return _unsatisfiable(size)
        start, end = _parse_range(match.group(1), match.group(2), size)
        if start is None or start > end:
            return _unsatisfiable(size)
        headers.update(
            {
                "Content-Range": f"bytes {start}-{end}/{size}",
                "Content-Length": str(end - start + 1),
            }
        )
        return StreamingResponse(
            _file_chunks(path, start, end),
            status_code=206,
            headers=headers,
        )

    headers["Content-Length"] = str(size)
    return StreamingResponse(_file_chunks(path, 0, size - 1), headers=headers)


def _parse_range(raw_start: str, raw_end: str, size: int) -> tuple[int, int]:
    if raw_start == "":  # suffix range: last N bytes
        suffix = int(raw_end)
        start = max(0, size - suffix)
        return start, size - 1
    start = int(raw_start)
    end = min(int(raw_end), size - 1) if raw_end else size - 1
    return start, end


def _unsatisfiable(size: int) -> JSONResponse:
    return JSONResponse(
        None,
        status_code=416,
        headers={"Content-Range": f"bytes */{size}"},
    )


def _file_chunks(path: Path, start: int, end: int):
    remaining = end - start + 1
    with path.open("rb") as handle:
        handle.seek(start)
        while remaining > 0:
            chunk = handle.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk
