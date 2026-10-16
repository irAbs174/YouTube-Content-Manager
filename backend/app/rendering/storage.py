"""Render storage layout.

    <render_root>/<episode_id>/video.mp4     — rendered Short
    <render_root>/<episode_id>/thumb.jpg     — extracted poster frame
    video_path column stores the path *relative* to the render root.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import Settings

VIDEO_NAME = "video.mp4"
THUMB_NAME = "thumb.jpg"


def render_root(settings: Settings) -> Path:
    root = Path(settings.render_root).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def episode_dir(settings: Settings, episode_id: int) -> Path:
    directory = render_root(settings) / str(episode_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def video_abs_path(settings: Settings, video_path: str) -> Path:
    """Resolve a stored relative video path against the render root."""
    return (render_root(settings) / video_path).resolve()


def thumb_abs_path(settings: Settings, episode_id: int) -> Path:
    return render_root(settings) / str(episode_id) / THUMB_NAME


def video_rel_path(episode_id: int) -> str:
    return f"{episode_id}/{VIDEO_NAME}"
