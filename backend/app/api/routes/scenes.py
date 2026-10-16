"""Scene CRUD for episodes: /api/content/:id/scenes"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db
from app.core.constants import COMMAND_MAX, DURATION_MAX_SEC, DURATION_MIN_SEC, TEXT_FIELD_MAX, TIP_MAX
from app.core.errors import NotFoundError, ValidationError
from app.db.models import EpisodeScene, User, YoutubeMain
from app.schemas.common import CamelModel

router = APIRouter(prefix="/api/content", tags=["scenes"])


class SceneCreate(CamelModel):
    duration_sec: int = Field(default=45, ge=DURATION_MIN_SEC, le=DURATION_MAX_SEC)
    command: str = Field(default="", max_length=COMMAND_MAX)
    tip: str = Field(default="", max_length=TIP_MAX)
    audio: bool = True
    notes: str = Field(default="", max_length=TEXT_FIELD_MAX)
    position: int | None = None


class ScenePatch(CamelModel):
    duration_sec: int | None = Field(default=None, ge=DURATION_MIN_SEC, le=DURATION_MAX_SEC)
    command: str | None = Field(default=None, max_length=COMMAND_MAX)
    tip: str | None = Field(default=None, max_length=TIP_MAX)
    audio: bool | None = None
    notes: str | None = Field(default=None, max_length=TEXT_FIELD_MAX)


class SceneOut(CamelModel):
    id: int
    position: int
    duration_sec: int
    command: str
    tip: str
    audio: bool
    notes: str


class ReorderPayload(CamelModel):
    ordered_ids: list[int]


def _get_episode_or_404(session: Session, content_id: int, user: User | None) -> YoutubeMain:
    row = session.get(YoutubeMain, content_id)
    if row is None:
        raise NotFoundError("Episode not found")
    if user is not None and row.user_id != user.id:
        raise NotFoundError("Episode not found")
    return row


def _get_user_fallback(session: Session, current_user: User | None) -> User | None:
    if current_user is not None:
        return current_user
    # fallback for legacy tests: use demo user
    from app.db.models import User as UserModel

    return session.scalars(select(UserModel).limit(1)).first()


@router.get("/{content_id}/scenes", response_model=list[SceneOut])
def list_scenes(content_id: int, session: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    user = _get_user_fallback(session, current_user)
    episode = _get_episode_or_404(session, content_id, user if current_user is not None else None)
    rows = session.scalars(select(EpisodeScene).where(EpisodeScene.content_id == episode.id).order_by(EpisodeScene.position)).all()
    return [SceneOut(id=r.id, position=r.position, duration_sec=r.duration_sec, command=r.command, tip=r.tip, audio=r.audio, notes=r.notes) for r in rows]


@router.post("/{content_id}/scenes", response_model=SceneOut, status_code=201)
def create_scene(content_id: int, payload: SceneCreate, session: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    user = _get_user_fallback(session, current_user)
    episode = _get_episode_or_404(session, content_id, user if current_user is not None else None)
    # determine position
    max_pos = session.scalar(select(EpisodeScene.position).where(EpisodeScene.content_id == episode.id).order_by(EpisodeScene.position.desc()).limit(1))
    next_pos = (max_pos + 1) if max_pos is not None else 0
    if payload.position is not None:
        # insert at position, shift others
        pos = max(0, payload.position)
        # shift existing scenes >= pos
        session.query(EpisodeScene).filter(EpisodeScene.content_id == episode.id, EpisodeScene.position >= pos).update({EpisodeScene.position: EpisodeScene.position + 1})
        next_pos = pos
    row = EpisodeScene(
        content_id=episode.id,
        position=next_pos,
        duration_sec=payload.duration_sec,
        command=payload.command,
        tip=payload.tip,
        audio=payload.audio,
        notes=payload.notes,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    # update episode duration_sec sum
    total = session.scalar(select(EpisodeScene.duration_sec).where(EpisodeScene.content_id == episode.id))
    # recalc sum
    from sqlalchemy import func

    total = session.scalar(select(func.sum(EpisodeScene.duration_sec)).where(EpisodeScene.content_id == episode.id)) or episode.duration_sec
    episode.duration_sec = int(total)
    session.commit()
    return SceneOut(id=row.id, position=row.position, duration_sec=row.duration_sec, command=row.command, tip=row.tip, audio=row.audio, notes=row.notes)


@router.patch("/{content_id}/scenes/{scene_id}", response_model=SceneOut)
def patch_scene(content_id: int, scene_id: int, payload: ScenePatch, session: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    user = _get_user_fallback(session, current_user)
    episode = _get_episode_or_404(session, content_id, user if current_user is not None else None)
    scene = session.get(EpisodeScene, scene_id)
    if scene is None or scene.content_id != episode.id:
        raise NotFoundError("Scene not found")
    if payload.duration_sec is not None:
        scene.duration_sec = payload.duration_sec
    if payload.command is not None:
        scene.command = payload.command
    if payload.tip is not None:
        scene.tip = payload.tip
    if payload.audio is not None:
        scene.audio = payload.audio
    if payload.notes is not None:
        scene.notes = payload.notes
    session.commit()
    session.refresh(scene)
    # update episode duration
    from sqlalchemy import func

    total = session.scalar(select(func.sum(EpisodeScene.duration_sec)).where(EpisodeScene.content_id == episode.id)) or episode.duration_sec
    episode.duration_sec = int(total)
    session.commit()
    return SceneOut(id=scene.id, position=scene.position, duration_sec=scene.duration_sec, command=scene.command, tip=scene.tip, audio=scene.audio, notes=scene.notes)


@router.delete("/{content_id}/scenes/{scene_id}")
def delete_scene(content_id: int, scene_id: int, session: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    user = _get_user_fallback(session, current_user)
    episode = _get_episode_or_404(session, content_id, user if current_user is not None else None)
    scene = session.get(EpisodeScene, scene_id)
    if scene is None or scene.content_id != episode.id:
        raise NotFoundError("Scene not found")
    pos = scene.position
    session.delete(scene)
    session.flush()
    # repack positions
    rows = session.scalars(select(EpisodeScene).where(EpisodeScene.content_id == episode.id).order_by(EpisodeScene.position)).all()
    for idx, r in enumerate(rows):
        r.position = idx
    # update duration
    from sqlalchemy import func

    total = session.scalar(select(func.sum(EpisodeScene.duration_sec)).where(EpisodeScene.content_id == episode.id))
    episode.duration_sec = int(total) if total else 45
    session.commit()
    return {"ok": True, "id": scene_id}


@router.put("/{content_id}/scenes/reorder")
def reorder_scenes(content_id: int, payload: ReorderPayload, session: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    user = _get_user_fallback(session, current_user)
    episode = _get_episode_or_404(session, content_id, user if current_user is not None else None)
    existing = session.scalars(select(EpisodeScene).where(EpisodeScene.content_id == episode.id)).all()
    existing_ids = {r.id for r in existing}
    if set(payload.ordered_ids) != existing_ids:
        raise ValidationError("orderedIds must contain exactly the existing scene ids")
    # map id -> row
    by_id = {r.id: r for r in existing}
    for idx, sid in enumerate(payload.ordered_ids):
        by_id[sid].position = idx
    session.commit()
    return {"ok": True}
