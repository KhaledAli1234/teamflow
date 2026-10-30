from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.auth.models import RefreshToken


def create(
    db: Session, *, user_id: int, token_hash: str, family_id: str, expires_at: datetime
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id, token_hash=token_hash, family_id=family_id, expires_at=expires_at
    )
    db.add(token)
    db.flush()
    return token


def get_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
    return db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )


def revoke_family(db: Session, family_id: str, now: datetime) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )


def revoke_all_for_user(db: Session, user_id: int, now: datetime) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )