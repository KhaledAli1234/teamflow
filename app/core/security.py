import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from jwt import InvalidTokenError

from app.core.config import settings

_hasher = PasswordHasher()
# بنستخدمه علشان وقت الرد يبقى متساوي سواء الإيميل موجود أو لأ
DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return _hasher.verify(hashed_password, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"require": ["exp", "sub", "type"]},
    )
    if payload["type"] != "access":
        raise InvalidTokenError("Wrong token type")
    return payload

def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)