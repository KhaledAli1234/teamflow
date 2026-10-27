from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenError, NotFoundError
from app.modules.comments import repository
from app.modules.comments.models import Comment
from app.modules.comments.schemas import CommentCreate
from app.modules.projects import service as projects_service
from app.modules.tasks import service as tasks_service
from app.modules.teams import repository as teams_repository
from app.modules.users.models import User
from app.modules.activity import service as activity


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
    db.commit()
    return comment

def list_comments(db: Session, task_id: int, user: User) -> list[Comment]:
    tasks_service.get_task(db, task_id, user)
    return repository.list_for_task(db, task_id)


def _get_comment(db: Session, comment_id: int, user: User) -> Comment:
    comment = repository.get(db, comment_id)
    if not comment:
        raise NotFoundError("Comment not found")
    tasks_service.get_task(db, comment.task_id, user)  # صلاحية الوصول للمهمة
    return comment


def edit_comment(db: Session, comment_id: int, data: CommentCreate, user: User) -> Comment:
    comment = _get_comment(db, comment_id, user)
    if comment.author_id != user.id:
        raise ForbiddenError("You can only edit your own comments")
    return repository.update(db, comment, data.body)


def delete_comment(db: Session, comment_id: int, user: User) -> None:
    comment = _get_comment(db, comment_id, user)
    if comment.author_id != user.id:
        task = tasks_service.get_task(db, comment.task_id, user)
        project = projects_service.get_accessible_project(db, task.project_id, user)
        membership = teams_repository.get_membership(db, project.team_id, user.id)
        if not membership or membership.role not in projects_service.MANAGER_ROLES:
            raise ForbiddenError("Not allowed to delete this comment")
    repository.delete(db, comment)