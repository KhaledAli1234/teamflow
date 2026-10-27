from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.projects import repository
from app.modules.projects.models import Project, ProjectMember
from app.modules.projects.schemas import ProjectCreate, ProjectMemberAdd, ProjectUpdate
from app.modules.teams import service as teams_service
from app.modules.teams.models import TeamRole
from app.modules.teams import repository as teams_repository
from app.modules.users import repository as users_repository
from app.modules.users.models import User

MANAGER_ROLES = (TeamRole.ADMIN, TeamRole.PROJECT_MANAGER)


def _require_manager(db: Session, team_id: int, user: User) -> None:
    membership = teams_service.require_member(db, team_id, user)
    if membership.role not in MANAGER_ROLES:
        raise ForbiddenError("Only admins or project managers can do this")


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = repository.get_project(db, project_id)
    if not project:
        raise NotFoundError("Project not found")
    return project


def get_accessible_project(db: Session, project_id: int, user: User) -> Project:
    """المشروع يظهر لأدمن/مدير الفريق، أو لعضو المشروع. غير كده 404."""
    project = _get_project_or_404(db, project_id)
    team_member = teams_repository.get_membership(db, project.team_id, user.id)
    if not team_member:
        raise NotFoundError("Project not found")
    if team_member.role in MANAGER_ROLES:
        return project
    if not repository.get_membership(db, project_id, user.id):
        raise NotFoundError("Project not found")
    return project


def create_project(db: Session, team_id: int, data: ProjectCreate, user: User) -> Project:
    _require_manager(db, team_id, user)
    return repository.create_project(
        db, team_id=team_id, created_by=user.id, data=data.model_dump()
    )


def list_projects(db: Session, team_id: int, user: User) -> list[Project]:
    membership = teams_service.require_member(db, team_id, user)
    if membership.role in MANAGER_ROLES:
        return repository.list_projects_for_team(db, team_id)
    return repository.list_projects_for_member(db, team_id, user.id)


def update_project(db: Session, project_id: int, data: ProjectUpdate, user: User) -> Project:
    project = _get_project_or_404(db, project_id)
    _require_manager(db, project.team_id, user)
    changes = data.model_dump(exclude_unset=True)
    start = changes.get("start_date", project.start_date)
    due = changes.get("due_date", project.due_date)
    if start and due and due < start:
        raise ForbiddenError("due_date cannot be before start_date")
    return repository.update_project(db, project, changes)


def delete_project(db: Session, project_id: int, user: User) -> None:
    project = _get_project_or_404(db, project_id)
    _require_manager(db, project.team_id, user)
    repository.delete_project(db, project)


def list_members(db: Session, project_id: int, user: User) -> list[ProjectMember]:
    get_accessible_project(db, project_id, user)
    return repository.list_members(db, project_id)


def add_member(db: Session, project_id: int, data: ProjectMemberAdd, user: User) -> ProjectMember:
    project = _get_project_or_404(db, project_id)
    _require_manager(db, project.team_id, user)
    target = users_repository.get_by_email(db, data.email.lower())
    if not target or not teams_repository.get_membership(db, project.team_id, target.id):
        raise NotFoundError("User is not a member of this team")
    if repository.get_membership(db, project_id, target.id):
        raise ConflictError("User is already on this project")
    return repository.add_member(db, project_id=project_id, user_id=target.id)


def remove_member(db: Session, project_id: int, target_user_id: int, user: User) -> None:
    project = _get_project_or_404(db, project_id)
    _require_manager(db, project.team_id, user)
    member = repository.get_membership(db, project_id, target_user_id)
    if not member:
        raise NotFoundError("Member not found")
    repository.delete_member(db, member)