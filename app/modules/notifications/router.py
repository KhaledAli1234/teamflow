from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.notifications import service
from app.modules.notifications.schemas import NotificationPage, NotificationRead
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "",
    response_model=NotificationPage,
    summary="List my notifications",
    description="Returns paginated notifications for the current user. Filter by `unread_only=true` to see only unread.",
)
def list_notifications(
    unread_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.list_my_notifications(db, user, unread_only, page=page, page_size=page_size)


@router.post(
    "/read-all",
    summary="Mark all notifications as read",
)
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"updated": service.mark_all_read(db, user)}


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Mark a notification as read",
)
def read_one(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.mark_read(db, notification_id, user)