from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.comments.models import Comment


def create(db: Session, *, task_id: int, author_id: int, body: str) -> Comment:
    comment = Comment(task_id=task_id, author_id=author_id, body=body)
    db.add(comment)
    db.flush()
    return comment


def get(db: Session, comment_id: int) -> Comment | None:
    return db.get(Comment, comment_id)


def list_for_task(db: Session, task_id: int) -> list[Comment]:
    return list(
        db.scalars(select(Comment).where(Comment.task_id == task_id).order_by(Comment.id))
    )


def update(db: Session, comment: Comment, body: str) -> Comment:
    comment.body = body
    db.flush()
    return comment


def delete(db: Session, comment: Comment) -> None:
    db.delete(comment)
    db.flush()