from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.notifications import service
from app.modules.notifications.schemas import NotificationRead
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.list_my_notifications(db, user, unread_only)


@router.post("/read-all")
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"updated": service.mark_all_read(db, user)}


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def read_one(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.mark_read(db, notification_id, user)