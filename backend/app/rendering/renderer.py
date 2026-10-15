"""Renderer abstraction: the queue only knows this interface.

`FfmpegRenderer` shells out to FFmpeg; tests inject scripted fakes so the
orchestration logic is verifiable on machines without FFmpeg.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.core.config import Settings
from app.rendering import ffmpeg


class RenderError(RuntimeError):
    """Raised when the render pipeline exits non-zero."""


@dataclass(frozen=True)
class RenderSpec:
    """Everything needed to render one episode."""

    episode_id: int
    duration_sec: int
    command: str
    tip: str
    audio: bool
    out_path: Path
    thumb_path: Path


class Renderer(Protocol):
    def is_available(self) -> ffmpeg.FFmpegStatus: ...

    def render(self, spec: RenderSpec, on_progress: ProgressFn) -> None: ...


ProgressFn = "callable[[float], None]"


class FfmpegRenderer:
    """Real renderer: one FFmpeg run for the video, one for the thumbnail."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._status: ffmpeg.FFmpegStatus | None = None

    def is_available(self) -> ffmpeg.FFmpegStatus:
        if self._status is None:
            self._status = ffmpeg.probe_availability()
        return self._status

    def render(self, spec: RenderSpec, on_progress: ProgressFn) -> None:
        status = self.is_available()
        if not status.available:
            raise RenderError(status.error or "FFmpeg is not available")

        font = ffmpeg.find_font()
        if font is None:  # pragma: no cover - probed above
            raise RenderError("No usable TTF font found")

        spec.out_path.parent.mkdir(parents=True, exist_ok=True)
        command_card, tip_card = ffmpeg.write_text_cards(
            spec.out_path.parent, spec.command, spec.tip
        )

        args = ffmpeg.build_render_args(
            duration_sec=spec.duration_sec,
            command_card=command_card,
            tip_card=tip_card if spec.tip else None,
            audio=spec.audio,
            out_path=str(spec.out_path),
            font_file=font,
        )
        self._run(args, spec, on_progress)

        # Poster frame (non-fatal if it fails — the video is the deliverable).
        thumb_args = ffmpeg.build_thumbnail_args(
            video_path=str(spec.out_path), thumb_path=str(spec.thumb_path)
        )
        subprocess.run(
            thumb_args, capture_output=True, check=False, timeout=60
        )

    def _run(self, args: list[str], spec: RenderSpec, on_progress: ProgressFn) -> None:
        total_us = spec.duration_sec * 1_000_000
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            key, _, value = line.strip().partition("=")
            if key == "out_time_us" and value.isdigit():
                on_progress(min(99.0, 100.0 * int(value) / total_us))
        returncode = process.wait()
        stderr = process.stderr.read() if process.stderr else ""
        if returncode != 0:
            detail = stderr.strip().splitlines()[-1] if stderr.strip() else ""
            raise RenderError(detail or f"FFmpeg exited with code {returncode}")
        on_progress(100.0)
