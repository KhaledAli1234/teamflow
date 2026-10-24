from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.modules.users import repository
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate


def register_user(db: Session, data: UserCreate) -> User:
    email = data.email.lower()
    if repository.get_by_email(db, email):
        raise ConflictError("Email already registered")
    return repository.create(
        db,
        email=email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )


def get_user(db: Session, user_id: int) -> User:
    user = repository.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found")
    return user