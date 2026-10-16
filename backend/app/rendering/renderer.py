"""Renderer abstraction: the queue only knows this interface.

`FfmpegRenderer` shells out to FFmpeg; tests inject scripted fakes so the
orchestration logic is verifiable on machines without FFmpeg.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from app.core.config import Settings
from app.rendering import ffmpeg


class RenderError(RuntimeError):
    """Raised when the render pipeline exits non-zero."""


@dataclass(frozen=True)
class SceneSpec:
    duration_sec: int
    command: str
    tip: str
    audio: bool
    notes: str = ""


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
    scenes: list[SceneSpec] = field(default_factory=list)


class Renderer(Protocol):
    def is_available(self) -> ffmpeg.FFmpegStatus: ...

    def render(self, spec: RenderSpec, on_progress: ProgressFn) -> None: ...


ProgressFn = "callable[[float], None]"


class FfmpegRenderer:
    """Real renderer: one FFmpeg run for the video, one for the thumbnail.

    For multi-scene episodes, renders each scene to a temp file then concats.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def is_available(self) -> ffmpeg.FFmpegStatus:
        return ffmpeg.probe_availability()

    def render(self, spec: RenderSpec, on_progress: ProgressFn) -> None:
        status = self.is_available()
        if not status.available:
            raise RenderError(status.error or "FFmpeg is not available")

        font = ffmpeg.find_font()
        if font is None:  # pragma: no cover - probed above
            raise RenderError("No usable TTF font found")

        spec.out_path.parent.mkdir(parents=True, exist_ok=True)

        if spec.scenes:
            self._render_multiscene(spec, font, on_progress)
        else:
            self._render_single(spec, font, on_progress)

        # Poster frame (non-fatal if it fails — the video is the deliverable).
        thumb_args = ffmpeg.build_thumbnail_args(
            video_path=str(spec.out_path), thumb_path=str(spec.thumb_path)
        )
        subprocess.run(
            thumb_args, capture_output=True, check=False, timeout=60
        )

    def _render_single(self, spec: RenderSpec, font: str, on_progress: ProgressFn) -> None:
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

    def _render_multiscene(self, spec: RenderSpec, font: str, on_progress: ProgressFn) -> None:
        total = sum(s.duration_sec for s in spec.scenes) or spec.duration_sec
        # fallback if no total
        if total <= 0:
            total = spec.duration_sec
        cumulative = 0
        part_files: list[Path] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            for idx, scene in enumerate(spec.scenes):
                part_path = tmp / f"part_{idx:03d}.mp4"
                scene_dir = tmp / f"scene_{idx}"
                scene_dir.mkdir(parents=True, exist_ok=True)
                command_card, tip_card = ffmpeg.write_text_cards(scene_dir, scene.command, scene.tip)
                args = ffmpeg.build_render_args(
                    duration_sec=scene.duration_sec,
                    command_card=command_card,
                    tip_card=tip_card if scene.tip else None,
                    audio=scene.audio,
                    out_path=str(part_path),
                    font_file=font,
                )
                # progress for this scene weighted
                base = cumulative
                span = scene.duration_sec

                def make_cb(b: int, s: int):
                    def cb(frac: float):
                        # frac is 0..100 for this scene
                        overall = (b + (frac / 100.0) * s) / total * 100.0
                        on_progress(min(99.0, overall))
                    return cb

                self._run(args, spec, make_cb(base, span))
                part_files.append(part_path)
                cumulative += span

            # Concat via demuxer
            list_file = tmp / "concat.txt"
            list_file.write_text("\n".join(f"file '{p}'" for p in part_files), encoding="utf-8")
            # Try concat with re-encode to ensure compatibility; fallback to copy
            concat_args = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c",
                "copy",
                str(spec.out_path),
            ]
            # attempt copy; if fails, re-encode
            result = subprocess.run(concat_args, capture_output=True, text=True)
            if result.returncode != 0:
                # re-encode fallback
                concat_args_re = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(list_file),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    str(spec.out_path),
                ]
                result2 = subprocess.run(concat_args_re, capture_output=True, text=True)
                if result2.returncode != 0:
                    raise RenderError(result2.stderr.strip().splitlines()[-1] if result2.stderr.strip() else "Concat failed")
            on_progress(100.0)

    def _run(self, args: list[str], spec: RenderSpec, on_progress: ProgressFn) -> None:
        total_us = spec.duration_sec * 1_000_000
        # For multiscene, total_us is per-scene; caller handles weighting, but we still need per-scene total
        # Use last -t arg as duration if present
        # Fallback to spec.duration_sec if args don't contain -t
        try:
            t_idx = args.index("-t")
            dur = int(args[t_idx + 1])
            total_us = dur * 1_000_000
        except Exception:
            pass
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
