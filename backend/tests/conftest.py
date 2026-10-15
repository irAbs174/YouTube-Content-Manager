"""Shared fixtures: isolated settings, fake renderer, TestClient factories."""

from __future__ import annotations

import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.seed import seed
from app.main import create_app
from app.rendering import ffmpeg
from app.rendering.renderer import RenderSpec


class FakeRenderer:
    """Scripted renderer: writes real files, reports progress, never shells out.

    Failures can be keyed by episode id (`fail_on`) or by the on-screen
    command text (`fail_commands`) — the latter avoids the create→config race.
    """

    def __init__(
        self,
        *,
        available: bool = True,
        fail_on: dict[int, str] | None = None,
        fail_commands: dict[str, str] | None = None,
    ):
        self.available = available
        self.fail_on = fail_on or {}
        self.fail_commands = fail_commands or {}
        self.rendered: list[int] = []

    def is_available(self) -> ffmpeg.FFmpegStatus:
        if self.available:
            return ffmpeg.FFmpegStatus(available=True, drawtext=True)
        return ffmpeg.FFmpegStatus(
            available=False, drawtext=False, error="FFmpeg is not installed."
        )

    def render(self, spec: RenderSpec, on_progress) -> None:
        if not self.available:
            raise RuntimeError("FFmpeg is not installed.")
        if spec.episode_id in self.fail_on:
            raise RuntimeError(self.fail_on[spec.episode_id])
        if spec.command in self.fail_commands:
            raise RuntimeError(self.fail_commands[spec.command])
        spec.out_path.parent.mkdir(parents=True, exist_ok=True)
        for step in (10, 40, 70, 100):
            time.sleep(0.01)
            on_progress(step)
        spec.out_path.write_bytes(b"FAKE_MP4_CONTAINER:" + b"\x00" * 256)
        spec.thumb_path.parent.mkdir(parents=True, exist_ok=True)
        spec.thumb_path.write_bytes(b"FAKE_JPEG")
        self.rendered.append(spec.episode_id)


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "data"


@pytest.fixture
def settings(data_dir: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{data_dir / 'test.db'}",
        render_root=data_dir / "renders",
        seed_on_startup=True,
        create_tables_on_startup=True,
    )


@pytest.fixture
def unavailable_settings(data_dir: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{data_dir / 'test.db'}",
        render_root=data_dir / "renders",
        seed_on_startup=True,
        create_tables_on_startup=True,
    )


@pytest.fixture
def seeded_session(settings: Settings) -> Iterator[Session]:
    """Raw DB session against the seeded schema (service-layer tests)."""
    from app.db.session import build_engine, build_session_factory

    engine = build_engine(settings)
    from app.db.base import Base

    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)
    with factory() as session:
        seed(session)
        yield session
    engine.dispose()


def make_client(
    settings: Settings, renderer: FakeRenderer | None = None
) -> TestClient:
    """App + client with lifespan running (tables, seed, render worker)."""
    app = create_app(settings, renderer=renderer or FakeRenderer())
    return TestClient(app)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with make_client(settings) as test_client:
        yield test_client


def wait_for_render(
    client: TestClient, episode_id: int, *, timeout: float = 5.0, want: str = "done"
) -> dict:
    """Poll /api/renders until the episode reaches `want` (or fail the test)."""
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        response = client.get(f"/api/renders?ids={episode_id}")
        assert response.status_code == 200
        states = response.json()
        assert states, "render state vanished"
        last = states[0]
        if last["renderStatus"] == want:
            return last
        if last["renderStatus"] == "failed" and want != "failed":
            raise AssertionError(f"render failed unexpectedly: {last}")
        time.sleep(0.02)
    raise AssertionError(f"timed out waiting for render={want}; last={last}")
