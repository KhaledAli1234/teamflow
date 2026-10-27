from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.tasks.models import Task, TaskPriority, TaskStatus


def create_task(db: Session, *, project_id: int, created_by: int, data: dict) -> Task:
    task = Task(project_id=project_id, created_by=created_by, **data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def list_tasks(
    db: Session,
    project_id: int,
    *,
    status: TaskStatus | None,
    priority: TaskPriority | None,
    assignee_id: int | None,
    search: str | None,
    page: int,
    page_size: int,
) -> tuple[list[Task], int]:
    conditions = [Task.project_id == project_id]
    if status:
        conditions.append(Task.status == status)
    if priority:
        conditions.append(Task.priority == priority)
    if assignee_id:
        conditions.append(Task.assignee_id == assignee_id)
    if search:
        conditions.append(Task.title.ilike(f"%{search}%"))

    total = db.scalar(select(func.count()).select_from(Task).where(*conditions)) or 0
    items = db.scalars(
        select(Task)
        .where(*conditions)
        .order_by(Task.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(items), total


def update_task(db: Session, task: Task, data: dict) -> Task:
    for key, value in data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()