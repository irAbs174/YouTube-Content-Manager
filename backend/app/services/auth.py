"""Email/password auth with bcrypt hashes and hashed session tokens."""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.constants import PASSWORD_MIN
from app.core.errors import ConflictError, UnauthorizedError, ValidationError
from app.db.models import SessionToken, User

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_credentials(email: str, password: str) -> str:
    email = normalize_email(email)
    if not _EMAIL_RE.match(email):
        raise ValidationError("Enter a valid email address")
    if len(password) < PASSWORD_MIN:
        raise ValidationError(f"Password must be at least {PASSWORD_MIN} characters")
    return email


def register_user(session: Session, email: str, password: str, settings: Settings) -> tuple[User, str]:
    email = _validate_credentials(email, password)
    existing = session.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise ConflictError("An account with that email already exists")
    user = User(email=email, password_hash=hash_password(password))
    session.add(user)
    session.flush()
    token = _issue_session(session, user, settings)
    session.commit()
    session.refresh(user)
    return user, token


def login_user(session: Session, email: str, password: str, settings: Settings) -> tuple[User, str]:
    email = normalize_email(email)
    if not email or not password:
        raise UnauthorizedError("Invalid email or password")
    user = session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    token = _issue_session(session, user, settings)
    session.commit()
    session.refresh(user)
    return user, token


def logout_user(session: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    token_hash = hash_session_token(raw_token)
    row = session.scalar(select(SessionToken).where(SessionToken.token_hash == token_hash))
    if row is not None:
        session.delete(row)
        session.commit()


def user_from_token(session: Session, raw_token: str | None) -> User:
    if not raw_token:
        raise UnauthorizedError("Not authenticated")
    token_hash = hash_session_token(raw_token)
    row = session.scalar(select(SessionToken).where(SessionToken.token_hash == token_hash))
    if row is None:
        raise UnauthorizedError("Not authenticated")
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires <= datetime.now(UTC):
        session.delete(row)
        session.commit()
        raise UnauthorizedError("Not authenticated")
    return row.user


def _issue_session(session: Session, user: User, settings: Settings) -> str:
    raw = secrets.token_urlsafe(32)
    session.add(
        SessionToken(
            user_id=user.id,
            token_hash=hash_session_token(raw),
            expires_at=datetime.now(UTC) + timedelta(days=settings.session_ttl_days),
        )
    )
    return raw
