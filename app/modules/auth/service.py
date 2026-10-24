from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.modules.auth.schemas import Token
from app.modules.users import repository as users_repository


def login(db: Session, email: str, password: str) -> Token:
    user = users_repository.get_by_email(db, email.lower())
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise ForbiddenError("Account is disabled")
    return Token(access_token=create_access_token(str(user.id)))