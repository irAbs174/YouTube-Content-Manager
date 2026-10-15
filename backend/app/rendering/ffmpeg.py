"""FFmpeg availability probing and command construction.

Kept pure (no subprocess execution) so it is unit-testable on machines
without FFmpeg installed. `renderer.py` owns actual execution.

On-screen text is passed via `textfile=` rather than `text=` so no
filtergraph escaping is ever needed — FFmpeg's double-level escaping
(`:` `'` `\` `,` `%`) is a legendary footgun.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from app.core.constants import VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH

COMMAND_CARD = "command-card.txt"
TIP_CARD = "tip-card.txt"

# Candidate font files for drawtext (first readable match wins).
FONT_CANDIDATES: tuple[str, ...] = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "C:/Windows/Fonts/consola.ttf",
)


@dataclass(frozen=True)
class FFmpegStatus:
    available: bool
    drawtext: bool
    error: str | None = None


def find_font() -> str | None:
    """First readable TTF from the well-known candidates."""
    for candidate in FONT_CANDIDATES:
        try:
            with open(candidate, "rb"):
                return candidate
        except OSError:
            continue
    return None


def write_text_cards(directory: Path, command: str, tip: str) -> tuple[Path, Path]:
    """Persist the on-screen cards next to the render output."""
    command_card = directory / COMMAND_CARD
    tip_card = directory / TIP_CARD
    command_card.write_text(f"❯ {command}", encoding="utf-8")
    tip_card.write_text(tip, encoding="utf-8")
    return command_card, tip_card


def build_render_args(
    *,
    duration_sec: int,
    command_card: Path,
    tip_card: Path | None,
    audio: bool,
    out_path: str,
    font_file: str,
) -> list[str]:
    """Args for a 1080x1920 Short: dark canvas, command + tip cards, optional
    generated audio (low drone + pink noise). Progress goes to stdout."""
    filters: list[str] = [
        f"drawtext=fontfile='{font_file}'"
        f":textfile='{command_card}'"
        ":fontcolor=white:fontsize=64:x=(w-text_w)/2:y=0.40*th"
        ":borderw=4:bordercolor=black@0.85",
    ]
    if tip_card is not None:
        filters.append(
            f"drawtext=fontfile='{font_file}'"
            f":textfile='{tip_card}'"
            ":fontcolor=0xcbd5e1:fontsize=44:x=(w-text_w)/2:y=0.58*th"
            ":borderw=3:bordercolor=black@0.85"
        )
    filters.append("format=yuv420p")

    args = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x0b1020:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={duration_sec}:r={VIDEO_FPS}",
    ]
    if audio:
        args += [
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=55:duration={duration_sec}",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=color=pink:amplitude=0.05:duration={duration_sec}",
            "-filter_complex",
            f"[0:v]{','.join(filters)}[v];"
            "[1:a][2:a]amix=inputs=2:duration=first,alimiter=limit=0.5[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
        ]
    else:
        args += ["-vf", ",".join(filters), "-an"]

    args += [
        "-t",
        str(duration_sec),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-progress",
        "pipe:1",
        "-nostats",
        out_path,
    ]
    return args


def build_thumbnail_args(*, video_path: str, thumb_path: str) -> list[str]:
    """Extract a poster frame one second into the video."""
    return [
        "ffmpeg",
        "-y",
        "-ss",
        "1",
        "-i",
        video_path,
        "-frames:v",
        "1",
        "-q:v",
        "3",
        thumb_path,
    ]


def probe_availability() -> FFmpegStatus:
    """Best-effort local probe: binary, font, drawtext filter support."""
    if shutil.which("ffmpeg") is None:
        return FFmpegStatus(
            available=False, drawtext=False, error="FFmpeg is not installed."
        )
    if find_font() is None:
        return FFmpegStatus(
            available=False,
            drawtext=False,
            error="No usable TTF font found for FFmpeg drawtext.",
        )
    return FFmpegStatus(available=True, drawtext=True)
