from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification


def add(db: Session, notification: Notification) -> None:
    db.add(notification)


def list_for_user(db: Session, user_id: int, unread_only: bool) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    return list(db.scalars(stmt.order_by(Notification.id.desc())))


def get(db: Session, notification_id: int) -> Notification | None:
    return db.get(Notification, notification_id)


def mark_read(db: Session, notification: Notification) -> Notification:
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: int) -> int:
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return result.rowcount