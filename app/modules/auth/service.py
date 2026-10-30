import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenError, UnauthorizedError
from app.core.config import settings
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    generate_refresh_token,
    hash_token,
    verify_password,
)
from app.modules.auth import repository
from app.modules.auth.schemas import Token
from app.modules.users import repository as users_repository
from app.modules.users.models import User


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _issue_tokens(db: Session, user_id: int, family_id: str | None = None) -> Token:
    raw, token_hash = generate_refresh_token()
    repository.create(
        db,
        user_id=user_id,
        token_hash=token_hash,
        family_id=family_id or uuid.uuid4().hex,
        expires_at=_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return Token(access_token=create_access_token(str(user_id)), refresh_token=raw)


def login(db: Session, email: str, password: str) -> Token:
    now = _now()
    user = users_repository.get_by_email(db, email.strip().lower())

    if user and user.locked_until and user.locked_until > now:
        raise UnauthorizedError("Account temporarily locked. Try again later.")

    password_ok = verify_password(password, user.hashed_password if user else DUMMY_HASH)
    if not user or not password_ok:
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_FAILED_LOGINS:
                user.locked_until = now + timedelta(minutes=settings.LOCKOUT_MINUTES)
                user.failed_login_attempts = 0
            db.commit()
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise ForbiddenError("Account is disabled")

    user.failed_login_attempts = 0
    user.locked_until = None
    tokens = _issue_tokens(db, user.id)
    db.commit()
    return tokens


def refresh(db: Session, raw_token: str) -> Token:
    stored = repository.get_by_hash(db, hash_token(raw_token))
    if not stored:
        raise UnauthorizedError("Invalid refresh token")

    now = _now()
    if stored.revoked_at is not None:
        repository.revoke_family(db, stored.family_id, now)
        db.commit()
        raise UnauthorizedError("Invalid refresh token")
    if stored.expires_at <= now:
        raise UnauthorizedError("Refresh token expired")

    user = users_repository.get_by_id(db, stored.user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("Invalid refresh token")

    stored.revoked_at = now
    tokens = _issue_tokens(db, user.id, family_id=stored.family_id)
    db.commit()
    return tokens


def logout(db: Session, raw_token: str) -> None:
    stored = repository.get_by_hash(db, hash_token(raw_token))
    if stored:
        repository.revoke_family(db, stored.family_id, _now())
        db.commit()


def logout_all(db: Session, user: User) -> None:
    repository.revoke_all_for_user(db, user.id, _now())
    db.commit()