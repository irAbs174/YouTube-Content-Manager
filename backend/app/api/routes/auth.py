"""Auth routes: register, login, logout, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, Request
from pydantic import BaseModel

from app.api.deps import get_db, get_settings_dep, get_current_user
from app.core.config import Settings
from app.core.constants import SESSION_COOKIE
from app.db.models import User
from app.schemas.common import CamelModel
from sqlalchemy.orm import Session
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthPayload(CamelModel):
    email: str
    password: str


class AuthResponse(CamelModel):
    id: int
    email: str


def _set_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=settings.session_ttl_days * 24 * 3600,
        secure=False,  # set True in prod behind HTTPS
    )


def _clear_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE, path="/")


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: AuthPayload, response: Response, session: Session = Depends(get_db), settings: Settings = Depends(get_settings_dep)):
    user, token = auth_service.register_user(session, payload.email, payload.password, settings)
    _set_cookie(response, token, settings)
    return AuthResponse(id=user.id, email=user.email)


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthPayload, response: Response, session: Session = Depends(get_db), settings: Settings = Depends(get_settings_dep)):
    user, token = auth_service.login_user(session, payload.email, payload.password, settings)
    _set_cookie(response, token, settings)
    return AuthResponse(id=user.id, email=user.email)


@router.post("/logout")
def logout(request: Request, response: Response, session: Session = Depends(get_db)):
    raw = request.cookies.get(SESSION_COOKIE)
    auth_service.logout_user(session, raw)
    _clear_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=AuthResponse)
def me(current_user: User = Depends(get_current_user)):
    return AuthResponse(id=current_user.id, email=current_user.email)
