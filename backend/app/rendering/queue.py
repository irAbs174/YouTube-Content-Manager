"""Render queue orchestration.

A single asyncio worker consumes job ids submitted by the API layer:

    submit(id)  →  DB: render_status=queued, progress=0  →  asyncio.Queue
    worker      →  DB: running → (renderer thread) → done/failed

Progress callbacks from the renderer thread write DB updates (throttled to
one percentage point). One job renders at a time — FFmpeg is CPU-bound and
shorts are 5-180s, so a single worker keeps the machine responsive.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging

from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.db.models import YoutubeContent
from app.rendering.renderer import Renderer, RenderSpec
from app.rendering.storage import episode_dir, thumb_abs_path, video_rel_path

logger = logging.getLogger(__name__)

Queued = "queued"
Running = "running"
Done = "done"
Failed = "failed"


class RenderQueue:
    def __init__(
        self,
        settings: Settings,
        session_factory: sessionmaker[Session],
        renderer: Renderer,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._renderer = renderer
        self._jobs: asyncio.Queue[int] = asyncio.Queue()
        self._worker: asyncio.Task | None = None
        self._pending: set[int] = set()  # ids queued but not yet picked up

    # ── lifecycle ────────────────────────────────────────────────────────────
    async def start(self) -> None:
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._run_forever(), name="render-worker")
            logger.info("render worker started")

    async def stop(self) -> None:
        if self._worker is None:
            return
        self._worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._worker
        self._worker = None
        logger.info("render worker stopped")

    # ── public API ───────────────────────────────────────────────────────────
    def submit(self, episode_id: int) -> str:
        """Queue an episode. Returns 'queued', 'already_queued' or 'missing'."""
        with self._session() as session:
            row = session.get(YoutubeContent, episode_id)
            if row is None:
                return "missing"
            if row.render_status in (Queued, Running):
                return "already_queued"

            row.render_status = Queued
            row.render_progress = 0
            row.render_error = None
            session.commit()

        self._pending.add(episode_id)
        self._jobs.put_nowait(episode_id)
        return "queued"

    def availability(self) -> object:
        """Expose the renderer's availability probe (FFmpegStatus)."""
        return self._renderer.is_available()

    # ── worker internals ─────────────────────────────────────────────────────
    def _session(self):
        from app.db.session import session_scope

        return session_scope(self._session_factory)

    async def _run_forever(self) -> None:
        while True:
            episode_id = await self._jobs.get()
            self._pending.discard(episode_id)
            try:
                await self._process(episode_id)
            except Exception:  # noqa: BLE001 — worker must never die
                logger.exception("render job %s crashed the worker", episode_id)
            finally:
                self._jobs.task_done()

    async def _process(self, episode_id: int) -> None:
        with self._session() as session:
            row = session.get(YoutubeContent, episode_id)
            if row is None or row.script is None:
                # Episode was deleted, or has nothing to render.
                if row is not None:
                    row.render_status = Failed
                    row.render_error = "Nothing to render (missing on-screen script)"
                    session.commit()
                return

            row.render_status = Running
            row.render_progress = 0
            session.commit()
            spec = RenderSpec(
                episode_id=episode_id,
                duration_sec=row.duration_sec,
                command=str(row.script.get("command", "")),
                tip=str(row.script.get("tip", "")),
                audio=bool(row.script.get("audio", True)),
                out_path=episode_dir(self._settings, episode_id) / "video.mp4",
                thumb_path=thumb_abs_path(self._settings, episode_id),
            )

        loop = asyncio.get_running_loop()
        last_reported = 0.0

        def on_progress(fraction: float) -> None:
            nonlocal last_reported
            pct = min(100.0, max(0.0, fraction))
            if pct - last_reported < 1.0 and pct < 100.0:
                return  # throttle to ~1 percentage point
            last_reported = pct
            with self._session() as session:
                row = session.get(YoutubeContent, episode_id)
                if row is None or row.render_status not in (Running, Queued):
                    return  # deleted or reset mid-render
                row.render_progress = int(round(pct))
                session.commit()

        try:
            await loop.run_in_executor(None, self._renderer.render, spec, on_progress)
        except Exception as exc:  # noqa: BLE001 — every failure becomes a Failed row
            message = str(exc) or "Render failed"
            with self._session() as session:
                row = session.get(YoutubeContent, episode_id)
                if row is not None:
                    row.render_status = Failed
                    row.render_error = message[:500]
                    row.render_progress = 0
                    session.commit()
            logger.warning("render %s failed: %s", episode_id, message)
            return

        with self._session() as session:
            row = session.get(YoutubeContent, episode_id)
            if row is None:  # deleted mid-render — drop the result
                return
            row.render_status = Done
            row.render_progress = 100
            row.render_error = None
            row.video_path = video_rel_path(episode_id)
            session.commit()
