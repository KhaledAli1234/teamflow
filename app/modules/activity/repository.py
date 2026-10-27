from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.activity.models import ActivityLog


def add(db: Session, log: ActivityLog) -> None:
    db.add(log)


def list_for_project(db: Session, project_id: int, limit: int = 100) -> list[ActivityLog]:
    stmt = (
        select(ActivityLog)
        .where(ActivityLog.project_id == project_id)
        .order_by(ActivityLog.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))