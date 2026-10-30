from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.modules.users import repository
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserUpdate


def register_user(db: Session, data: UserCreate) -> User:
    email = data.email.lower()
    if repository.get_by_email(db, email):
        raise ConflictError("Email already registered")
    user = repository.create(
        db,
        email=email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> User:
    user = repository.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found")
    return user


def update_me(db: Session, user: User, data: UserUpdate) -> User:
    """Updates the current user's profile. Only non-empty fields are applied."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user