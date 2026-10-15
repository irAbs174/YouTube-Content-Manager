"""FFmpeg command construction (pure — no binary required)."""

from __future__ import annotations

from pathlib import Path

from app.core.constants import VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH
from app.rendering.ffmpeg import (
    build_render_args,
    build_thumbnail_args,
    find_font,
    probe_availability,
    write_text_cards,
)


def _args(**overrides) -> list[str]:
    defaults = dict(
        duration_sec=45,
        command_card=Path("/tmp/x/command-card.txt"),
        tip_card=Path("/tmp/x/tip-card.txt"),
        audio=True,
        out_path="/tmp/x/video.mp4",
        font_file="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    )
    defaults.update(overrides)
    return build_render_args(**defaults)


def test_video_args_shape():
    args = _args()
    assert args[0] == "ffmpeg"
    assert "-y" in args
    # canvas is a 1080x1920 vertical short at 30fps
    joined = " ".join(args)
    assert f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}" in joined
    assert f"r={VIDEO_FPS}" in joined
    assert "d=45" in joined
    # progress reporting goes to stdout for the parser
    assert "pipe:1" in args
    assert "-nostats" in args


def test_audio_mixed_when_requested():
    with_audio = " ".join(_args(audio=True))
    assert "sine=frequency=55" in with_audio
    assert "anoisesrc" in with_audio
    assert "amix" in with_audio


def test_no_audio_disables_tracks():
    without = _args(audio=False)
    joined = " ".join(without)
    assert "-an" in without
    assert "sine" not in joined
    assert "anoisesrc" not in joined


def test_tip_card_omitted_when_empty():
    joined = " ".join(_args(tip_card=None))
    assert "tip-card" not in joined


def test_text_uses_textfile_not_text():
    """On-screen text must ride in via textfile= (no filtergraph escaping)."""
    joined = " ".join(_args())
    assert "textfile=" in joined
    assert ":text=" not in joined  # a literal text= option would need escaping


def test_thumbnail_args():
    args = build_thumbnail_args(video_path="/v/video.mp4", thumb_path="/v/thumb.jpg")
    assert args[:6] == ["ffmpeg", "-y", "-ss", "1", "-i", "/v/video.mp4"]
    assert args[-1] == "/v/thumb.jpg"


def test_write_text_cards(tmp_path: Path):
    command_card, tip_card = write_text_cards(tmp_path, "nc -lv 9999", "tip text")
    assert command_card.read_text(encoding="utf-8") == "❯ nc -lv 9999"
    assert tip_card.read_text(encoding="utf-8") == "tip text"
    assert command_card.name == "command-card.txt"
    assert tip_card.name == "tip-card.txt"


def test_probe_availability_returns_status():
    status = probe_availability()
    # This sandbox has no FFmpeg, but the probe must never raise either way.
    assert status.available is False or status.available is True
    if not status.available:
        assert status.error
    else:
        assert find_font() is not None
