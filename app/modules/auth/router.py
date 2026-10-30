from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.auth import service as auth_service
from app.modules.users import service as users_service
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserRead
from fastapi import APIRouter, Depends, Request, Response, status
from app.core.rate_limit import limiter
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    Token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, data: UserCreate, db: Session = Depends(get_db)):
    return users_service.register_user(db, data)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return auth_service.login(db, form.username, form.password)


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh(db, data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, db: Session = Depends(get_db)):
    auth_service.logout(db, data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    auth_service.logout_all(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    auth_service.change_password(db, user, data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
def forgot_password(
    request: Request, data: ForgotPasswordRequest, db: Session = Depends(get_db)
):
    auth_service.forgot_password(db, data.email)
    return MessageResponse(message="If the email exists, a reset link has been sent.")


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def reset_password(
    request: Request, data: ResetPasswordRequest, db: Session = Depends(get_db)
):
    auth_service.reset_password(db, data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)