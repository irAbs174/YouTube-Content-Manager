"""Content routes: CRUD, render enqueue, thumbnail + video streaming."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_queue, get_settings_dep
from app.core.config import Settings
from app.core.errors import FFmpegUnavailableError, NotFoundError
from app.rendering.queue import RenderQueue
from app.schemas.content import EpisodeCreate, EpisodeOut, EpisodePatch, MutationOk
from app.services import content as content_service

router = APIRouter(prefix="/api/content", tags=["content"])

CHUNK_SIZE = 64 * 1024
_RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


def _episode_out(row, render_status: str | None = None) -> EpisodeOut:
    return EpisodeOut(
        id=row.id,
        episode=row.episode,
        date=row.date.isoformat(),
        title=row.title,
        status=row.status,
        collection=row.collection,
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
    )


@router.post("", response_model=EpisodeOut, status_code=201)
def create_episode(
    payload: EpisodeCreate,
    session: Session = Depends(get_db),
    queue: RenderQueue = Depends(get_queue),
) -> EpisodeOut:
    """Create an episode; optionally queue it for FFmpeg rendering."""
    if payload.render:
        status = queue.availability()
        if not status.available:
            raise FFmpegUnavailableError(
                f"{status.error} Uncheck \"Render video\" to save without rendering."
            )

    row = content_service.create_episode(session, payload)
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
) -> MutationOk:
    content_service.update_episode(session, episode_id, payload)
    return MutationOk(id=episode_id)


@router.delete("/{episode_id}", response_model=MutationOk)
def delete_episode(
    episode_id: int,
    session: Session = Depends(get_db),
) -> MutationOk:
    content_service.delete_episode(session, episode_id)
    return MutationOk(id=episode_id)


@router.post("/{episode_id}/render", response_model=None)
def request_render(
    episode_id: int,
    session: Session = Depends(get_db),
    queue: RenderQueue = Depends(get_queue),
) -> JSONResponse:
    """(Re)queue an FFmpeg render. 202 when freshly queued, 200 when pending."""
    row = content_service.get_episode(session, episode_id)
    status = queue.availability()
    if not status.available:
        raise FFmpegUnavailableError(
            f"{status.error} FFmpeg is required to render episode {row.episode}."
        )
    if not row.script:
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
):
    from app.rendering.storage import thumb_abs_path

    content_service.get_episode(session, episode_id)  # 404 when unknown id
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
):
    """Stream the rendered MP4 with HTTP Range support (seekable <video>)."""
    from app.rendering.storage import video_abs_path

    row = content_service.get_episode(session, episode_id)
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
