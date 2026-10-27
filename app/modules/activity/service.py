from sqlalchemy.orm import Session

from app.modules.activity import repository
from app.modules.activity.models import ActivityLog
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


def list_project_activity(db: Session, project_id: int, user: User) -> list[ActivityLog]:
    projects_service.get_accessible_project(db, project_id, user)
    return repository.list_for_project(db, project_id)