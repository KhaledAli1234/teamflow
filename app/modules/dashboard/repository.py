
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.modules.projects.models import Project
from app.modules.tasks.models import Task, TaskStatus
from app.modules.users.models import User

_done = Task.status == TaskStatus.DONE


def _is_overdue():
    return (Task.due_date < func.current_date()) & (Task.status != TaskStatus.DONE)


def count_projects(db: Session, team_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Project).where(Project.team_id == team_id)) or 0


def status_counts(db: Session, team_id: int) -> dict[str, int]:
    rows = db.execute(
        select(Task.status, func.count())
        .join(Project, Project.id == Task.project_id)
        .where(Project.team_id == team_id)
        .group_by(Task.status)
    )
    return {status.value: count for status, count in rows}


def overdue_count(db: Session, team_id: int) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Task)
        .join(Project, Project.id == Task.project_id)
        .where(Project.team_id == team_id, _is_overdue())
    ) or 0


def project_progress(
    db: Session, *, team_id: int | None = None, project_id: int | None = None
) -> list[tuple[int, str, int, int, int]]:
    overdue_cond = _is_overdue()
    stmt = (
        select(
            Project.id,
            Project.name,
            func.count(Task.id),
            func.count(case((_done, 1))),
            func.count(case((overdue_cond, 1))),
        )
        .outerjoin(Task, Task.project_id == Project.id)
        .group_by(Project.id, Project.name)
        .order_by(Project.id)
    )
    if team_id is not None:
        stmt = stmt.where(Project.team_id == team_id)
    if project_id is not None:
        stmt = stmt.where(Project.id == project_id)
    return list(db.execute(stmt).all())


def workload(db: Session, team_id: int) -> list[tuple[int, str, int, int]]:
    return list(
        db.execute(
            select(
                User.id,
                User.full_name,
                func.count(Task.id),
                func.count(case((Task.status != TaskStatus.DONE, 1))),
            )
            .join(Task, Task.assignee_id == User.id)
            .join(Project, Project.id == Task.project_id)
            .where(Project.team_id == team_id)
            .group_by(User.id, User.full_name)
            .order_by(User.id)
        ).all()
    )