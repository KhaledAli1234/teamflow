from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenError, NotFoundError
from app.modules.projects import repository as projects_repository
from app.modules.projects import service as projects_service
from app.modules.projects.models import Project
from app.modules.tasks import repository
from app.modules.tasks.models import Task, TaskPriority, TaskStatus
from app.modules.tasks.schemas import TaskCreate, TaskPage, TaskStatusUpdate, TaskUpdate
from app.modules.teams import repository as teams_repository
from app.modules.users.models import User
from app.modules.activity import service as activity


def _is_manager(db: Session, project: Project, user: User) -> bool:
    membership = teams_repository.get_membership(db, project.team_id, user.id)
    return bool(membership and membership.role in projects_service.MANAGER_ROLES)


def _require_manager(db: Session, project: Project, user: User) -> None:
    if not _is_manager(db, project, user):
        raise ForbiddenError("Only admins or project managers can do this")


def _validate_assignee(db: Session, project_id: int, assignee_id: int | None) -> None:
    if assignee_id is None:
        return
    if not projects_repository.get_membership(db, project_id, assignee_id):
        raise ForbiddenError("Assignee must be a member of the project")


def _get_task_and_project(db: Session, task_id: int, user: User) -> tuple[Task, Project]:
    task = repository.get_task(db, task_id)
    if not task:
        raise NotFoundError("Task not found")
    project = projects_service.get_accessible_project(db, task.project_id, user)
    return task, project


def create_task(db: Session, project_id: int, data: TaskCreate, user: User) -> Task:
    project = projects_service.get_accessible_project(db, project_id, user)
    _require_manager(db, project, user)
    _validate_assignee(db, project_id, data.assignee_id)
    task = repository.create_task(
        db, project_id=project_id, created_by=user.id, data=data.model_dump()
    )
    activity.log(
        db,
        project_id=project_id,
        actor_id=user.id,
        action="task.created",
        entity_type="task",
        entity_id=task.id,
        details={"title": task.title, "assignee_id": task.assignee_id},
    )
    db.commit()
    return task

def list_tasks(
    db: Session,
    project_id: int,
    user: User,
    *,
    status: TaskStatus | None,
    priority: TaskPriority | None,
    assignee_id: int | None,
    search: str | None,
    page: int,
    page_size: int,
) -> TaskPage:
    projects_service.get_accessible_project(db, project_id, user)
    items, total = repository.list_tasks(
        db,
        project_id,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return TaskPage(items=items, total=total, page=page, page_size=page_size)


def get_task(db: Session, task_id: int, user: User) -> Task:
    task, _ = _get_task_and_project(db, task_id, user)
    return task


def update_task(db: Session, task_id: int, data: TaskUpdate, user: User) -> Task:
    task, project = _get_task_and_project(db, task_id, user)
    _require_manager(db, project, user)
    changes = data.model_dump(exclude_unset=True)
    if "assignee_id" in changes:
        _validate_assignee(db, project.id, changes["assignee_id"])
        if changes["assignee_id"] != task.assignee_id:
            activity.log(
                db,
                project_id=project.id,
                actor_id=user.id,
                action="task.assigned",
                entity_type="task",
                entity_id=task.id,
                details={"from": task.assignee_id, "to": changes["assignee_id"]},
            )
    return repository.update_task(db, task, changes)

def change_status(db: Session, task_id: int, data: TaskStatusUpdate, user: User) -> Task:
    task, project = _get_task_and_project(db, task_id, user)
    if not _is_manager(db, project, user) and task.assignee_id != user.id:
        raise ForbiddenError("You can only change the status of your own tasks")
    old_status = task.status.value
    activity.log(
        db,
        project_id=project.id,
        actor_id=user.id,
        action="task.status_changed",
        entity_type="task",
        entity_id=task.id,
        details={"from": old_status, "to": data.status.value},
    )
    return repository.update_task(db, task, {"status": data.status})

def delete_task(db: Session, task_id: int, user: User) -> None:
    task, project = _get_task_and_project(db, task_id, user)
    _require_manager(db, project, user)
    repository.delete_task(db, task)