"""Series routes: GET /api/series, POST /api/series (per-user)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db
from app.db.models import Series, User
from app.schemas.common import CamelModel

router = APIRouter(prefix="/api", tags=["series"])


class SeriesCreate(CamelModel):
    name: str


class SeriesOut(CamelModel):
    id: int
    name: str
    episode_count: int


@router.get("/series")
def list_series(session: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    # if no auth, return empty or all? For backward compat return all series for demo user
    if current_user is None:
        # fallback to demo user first
        from app.db.models import User as UserModel

        current_user = session.scalars(select(UserModel).limit(1)).first()
        if current_user is None:
            return []
    rows = session.scalars(select(Series).where(Series.user_id == current_user.id).order_by(Series.name)).all()
    # episode counts
    result = []
    for s in rows:
        from sqlalchemy import func

        from app.db.models import YoutubeMain

        cnt = session.scalar(select(func.count()).select_from(YoutubeMain).where(YoutubeMain.series_id == s.id)) or 0
        result.append(SeriesOut(id=s.id, name=s.name, episode_count=cnt))
    return result


@router.post("/series", response_model=SeriesOut, status_code=201)
def create_series(payload: SeriesCreate, session: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    if current_user is None:
        from app.db.models import User as UserModel

        current_user = session.scalars(select(UserModel).limit(1)).first()
        if current_user is None:
            from app.core.errors import UnauthorizedError

            raise UnauthorizedError("Not authenticated")
    name = payload.name.strip()
    if not name:
        from app.core.errors import ValidationError

        raise ValidationError("Series name cannot be empty")
    if len(name) > 200:
        from app.core.errors import ValidationError

        raise ValidationError("Series name too long")
    existing = session.scalar(select(Series).where(Series.user_id == current_user.id, Series.name == name))
    if existing is not None:
        from app.core.errors import ConflictError

        raise ConflictError(f"Series '{name}' already exists")
    row = Series(user_id=current_user.id, name=name)
    session.add(row)
    session.commit()
    session.refresh(row)
    return SeriesOut(id=row.id, name=row.name, episode_count=0)
