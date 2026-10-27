from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.tasks import service
from app.modules.tasks.models import TaskPriority, TaskStatus
from app.modules.tasks.schemas import (
    TaskCreate,
    TaskPage,
    TaskRead,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.modules.users.models import User

router = APIRouter(tags=["tasks"])


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    project_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.create_task(db, project_id, data, user)


@router.get("/projects/{project_id}/tasks", response_model=TaskPage)
def list_tasks(
    project_id: int,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    assignee_id: int | None = None,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.list_tasks(
        db,
        project_id,
        user,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return service.get_task(db, task_id, user)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.update_task(db, task_id, data, user)


@router.patch("/tasks/{task_id}/status", response_model=TaskRead)
def change_status(
    task_id: int,
    data: TaskStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.change_status(db, task_id, data, user)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    service.delete_task(db, task_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)