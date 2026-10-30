from sqlalchemy.orm import Session

from app.common.schemas import Page
from app.modules.activity import repository
from app.modules.activity.models import ActivityLog
from app.modules.activity.schemas import ActivityRead
from app.modules.projects import service as projects_service
from app.modules.users.models import User


def log(
    db: Session,
    *,
    project_id: int | None,
    actor_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int,
    details: dict | None = None,
) -> None:
    """بيضيف السجل للـ session من غير commit. اللي بينادي عليه هو اللي يعمل commit."""
    repository.add(
        db,
        ActivityLog(
            project_id=project_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        ),
    )


def list_project_activity(
    db: Session, project_id: int, user: User, *, page: int = 1, page_size: int = 20
) -> Page[ActivityRead]:
    projects_service.get_accessible_project(db, project_id, user)
    all_logs = repository.list_for_project(db, project_id)
    total = len(all_logs)
    start = (page - 1) * page_size
    items = all_logs[start : start + page_size]
    return Page(items=items, total=total, page=page, page_size=page_size)