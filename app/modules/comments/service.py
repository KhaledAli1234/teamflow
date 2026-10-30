from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenError, NotFoundError
from app.common.schemas import Page
from app.modules.activity import service as activity
from app.modules.comments import repository
from app.modules.comments.models import Comment
from app.modules.comments.schemas import CommentCreate, CommentRead, CommentUpdate
from app.modules.notifications import service as notifications
from app.modules.projects import service as projects_service
from app.modules.tasks import service as tasks_service
from app.modules.teams import repository as teams_repository
from app.modules.users.models import User


def add_comment(db: Session, task_id: int, data: CommentCreate, user: User) -> Comment:
    task = tasks_service.get_task(db, task_id, user)
    comment = repository.create(db, task_id=task.id, author_id=user.id, body=data.body)
    activity.log(
        db,
        project_id=task.project_id,
        actor_id=user.id,
        action="comment.added",
        entity_type="comment",
        entity_id=comment.id,
        details={"task_id": task.id},
    )
    recipients = {task.assignee_id, task.created_by} - {None, user.id}
    for recipient in recipients:
        notifications.notify(
            db,
            user_id=recipient,
            type="comment.added",
            message=f"New comment on: {task.title}",
            data={"task_id": task.id, "comment_id": comment.id},
        )
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(
    db: Session, task_id: int, user: User, *, page: int = 1, page_size: int = 20
) -> Page[CommentRead]:
    tasks_service.get_task(db, task_id, user)
    all_comments = repository.list_for_task(db, task_id)
    total = len(all_comments)
    start = (page - 1) * page_size
    items = all_comments[start : start + page_size]
    return Page(items=items, total=total, page=page, page_size=page_size)


def _get_comment_and_task(db: Session, comment_id: int, user: User):
    comment = repository.get(db, comment_id)
    if not comment:
        raise NotFoundError("Comment not found")
    task = tasks_service.get_task(db, comment.task_id, user)
    return comment, task


def edit_comment(db: Session, comment_id: int, data: CommentUpdate, user: User) -> Comment:
    comment, _ = _get_comment_and_task(db, comment_id, user)
    if comment.author_id != user.id:
        raise ForbiddenError("You can only edit your own comments")
    updated = repository.update(db, comment, data.body)
    db.commit()
    db.refresh(updated)
    return updated


def delete_comment(db: Session, comment_id: int, user: User) -> None:
    comment, task = _get_comment_and_task(db, comment_id, user)
    if comment.author_id != user.id:
        project = projects_service.get_accessible_project(db, task.project_id, user)
        membership = teams_repository.get_membership(db, project.team_id, user.id)
        if not membership or membership.role not in projects_service.MANAGER_ROLES:
            raise ForbiddenError("Not allowed to delete this comment")
    repository.delete(db, comment)
    db.commit()