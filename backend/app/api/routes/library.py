"""Library routes — the workbook's "spec places" as a JSON API.

    GET   /api/library/places       → place + column definitions + select options
    GET   /api/library/main         → YouTube Main 📌
    GET   /api/library/contents     → Contents 🖊️
    GET   /api/library/scenes       → Scences 🎬
    GET   /api/library/episodes     → Episodes ⏭️
    GET   /api/library/collections  → Collections 📃
    GET   /api/library/languages    → Languages 🌍
    GET   /api/library/assets       → Assets 👁️👁️
    GET   /api/library/subtitles    → Subtitles 🔍
    PATCH /api/library/<place>/:id  → edit one cell / one row
    POST  /api/library/<place>      → add a row (lookup tables + content + cues)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db
from app.db.models import User
from app.services import library as library_service

router = APIRouter(prefix="/api/library", tags=["library"])


def _user(session: Session, current_user: User | None) -> User | None:
    return library_service.resolve_user(session, current_user)


@router.get("/places")
def places(
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Declarative spec: every place, its columns and the select options."""
    user = _user(session, current_user)
    return {
        "places": library_service.place_specs(),
        "options": library_service.select_options(session, user),
    }


# ── read ────────────────────────────────────────────────────────────────────
@router.get("/main")
def main_rows(
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.list_main(session, _user(session, current_user))


@router.get("/contents")
def contents(
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.list_contents(session, _user(session, current_user))


@router.get("/scenes")
def scenes(
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.list_scenes(session, _user(session, current_user))


@router.get("/episodes")
def episodes(
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.list_episodes(session, _user(session, current_user))


@router.get("/collections")
def collections(
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.list_collections(session, _user(session, current_user))


@router.get("/languages")
def languages(
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.list_languages(session, _user(session, current_user))


@router.get("/assets")
def assets(
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.list_assets(session, _user(session, current_user))


@router.get("/subtitles")
def subtitles(
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.list_subtitles(session, _user(session, current_user))


# ── write ───────────────────────────────────────────────────────────────────
@router.patch("/main/{item_id}")
def patch_main(
    item_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.patch_main(
        session, item_id, payload, _user(session, current_user)
    )


@router.patch("/contents/{item_id}")
def patch_contents(
    item_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.patch_content(
        session, item_id, payload, _user(session, current_user)
    )


@router.patch("/scenes/{item_id}")
def patch_scenes(
    item_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.patch_scene(
        session, item_id, payload, _user(session, current_user)
    )


@router.patch("/episodes/{item_id}")
def patch_episodes(
    item_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.patch_episode_register(
        session, item_id, payload, _user(session, current_user)
    )


@router.patch("/collections/{item_id}")
def patch_collections(
    item_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.patch_collection(
        session, item_id, payload, _user(session, current_user)
    )


@router.patch("/languages/{item_id}")
def patch_languages(
    item_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.patch_language(
        session, item_id, payload, _user(session, current_user)
    )


@router.patch("/assets/{item_id}")
def patch_assets(
    item_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.patch_asset(
        session, item_id, payload, _user(session, current_user)
    )


@router.patch("/subtitles/{item_id}")
def patch_subtitles(
    item_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.patch_subtitle(
        session, item_id, payload, _user(session, current_user)
    )


# ── create ──────────────────────────────────────────────────────────────────
@router.post("/collections", status_code=201)
def create_collection(
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.create_collection(
        session, payload, _user(session, current_user)
    )


@router.post("/languages", status_code=201)
def create_language(
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.create_language(
        session, payload, _user(session, current_user)
    )


@router.post("/assets", status_code=201)
def create_asset(
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.create_asset(session, payload, _user(session, current_user))


@router.post("/contents", status_code=201)
def create_content(
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.create_content(
        session, payload, _user(session, current_user)
    )


@router.post("/subtitles", status_code=201)
def create_subtitle(
    payload: dict[str, Any] = Body(default_factory=dict),
    session: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return library_service.create_subtitle(
        session, payload, _user(session, current_user)
    )
