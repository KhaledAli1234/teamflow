from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError
from app.common.schemas import Page
from app.modules.notifications import repository
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationRead
from app.modules.users.models import User


def notify(
    db: Session,
    *,
    user_id: int,
    type: str,
    message: str,
    data: dict | None = None,
) -> None:
    """بيضيف الإشعار للـ session من غير commit، زي activity.log."""
    repository.add(
        db, Notification(user_id=user_id, type=type, message=message, data=data)
    )


def list_my_notifications(
    db: Session, user: User, unread_only: bool, *, page: int = 1, page_size: int = 20
) -> Page[NotificationRead]:
    all_notifs = repository.list_for_user(db, user.id, unread_only)
    total = len(all_notifs)
    start = (page - 1) * page_size
    items = all_notifs[start : start + page_size]
    return Page(items=items, total=total, page=page, page_size=page_size)


def mark_read(db: Session, notification_id: int, user: User) -> Notification:
    notification = repository.get(db, notification_id)
    if not notification or notification.user_id != user.id:
        raise NotFoundError("Notification not found")
    updated = repository.mark_read(db, notification)
    db.commit()
    db.refresh(updated)
    return updated


def mark_all_read(db: Session, user: User) -> int:
    count = repository.mark_all_read(db, user.id)
    db.commit()
    return count