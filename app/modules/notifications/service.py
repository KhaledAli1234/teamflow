from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError
from app.modules.notifications import repository
from app.modules.notifications.models import Notification
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


def list_my_notifications(db: Session, user: User, unread_only: bool) -> list[Notification]:
    return repository.list_for_user(db, user.id, unread_only)


def mark_read(db: Session, notification_id: int, user: User) -> Notification:
    notification = repository.get(db, notification_id)
    if not notification or notification.user_id != user.id:
        raise NotFoundError("Notification not found")
    return repository.mark_read(db, notification)


def mark_all_read(db: Session, user: User) -> int:
    return repository.mark_all_read(db, user.id)