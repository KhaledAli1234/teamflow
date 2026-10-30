from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenError, NotFoundError
from app.modules.dashboard import repository
from app.modules.dashboard.schemas import (
    MemberWorkload,
    ProjectProgress,
    StatusCounts,
    TeamDashboard,
)
from app.modules.projects import service as projects_service
from app.modules.teams import service as teams_service
from app.modules.users.models import User


def _progress(row: tuple[int, str, int, int, int]) -> ProjectProgress:
    project_id, name, total, done, overdue = row
    percent = round(done / total * 100, 1) if total else 0.0
    return ProjectProgress(
        project_id=project_id,
        name=name,
        total_tasks=total,
        done_tasks=done,
        overdue_tasks=overdue,
        progress_percent=percent,
    )


def team_dashboard(db: Session, team_id: int, user: User) -> TeamDashboard:
    membership = teams_service.require_member(db, team_id, user)
    if membership.role not in projects_service.MANAGER_ROLES:
        raise ForbiddenError("Only admins or project managers can view the dashboard")

    by_status = repository.status_counts(db, team_id)
    return TeamDashboard(
        total_projects=repository.count_projects(db, team_id),
        total_tasks=sum(by_status.values()),
        completed_tasks=by_status.get("done", 0),
        overdue_tasks=repository.overdue_count(db, team_id),
        tasks_by_status=StatusCounts(**by_status),
        projects=[_progress(r) for r in repository.project_progress(db, team_id=team_id)],
        workload=[
            MemberWorkload(user_id=uid, full_name=name, total_tasks=total, open_tasks=open_)
            for uid, name, total, open_ in repository.workload(db, team_id)
        ],
    )


def project_progress(db: Session, project_id: int, user: User) -> ProjectProgress:
    projects_service.get_accessible_project(db, project_id, user)
    progress_rows = repository.project_progress(db, project_id=project_id)
    if not progress_rows:
        raise NotFoundError("Project progress not found")
    return _progress(progress_rows[0])