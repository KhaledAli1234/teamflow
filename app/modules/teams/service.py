from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.common.schemas import Page
from app.modules.teams import repository
from app.modules.teams.models import Team, TeamMember, TeamRole
from app.modules.teams.schemas import MemberAdd, MemberRead, TeamCreate, TeamRead, TeamUpdate
from app.modules.users import repository as users_repository
from app.modules.users.models import User


def _get_team_or_404(db: Session, team_id: int) -> Team:
    team = repository.get_team(db, team_id)
    if not team:
        raise NotFoundError("Team not found")
    return team


def require_member(db: Session, team_id: int, user: User) -> TeamMember:
    _get_team_or_404(db, team_id)
    membership = repository.get_membership(db, team_id, user.id)
    if not membership:
        # 404 مش 403 علشان منكشفش إن الفريق موجود
        raise NotFoundError("Team not found")
    return membership


def require_admin(db: Session, team_id: int, user: User) -> TeamMember:
    membership = require_member(db, team_id, user)
    if membership.role != TeamRole.ADMIN:
        raise ForbiddenError("Only team admins can do this")
    return membership


def create_team(db: Session, data: TeamCreate, user: User) -> Team:
    team = repository.create_team(
        db, name=data.name, description=data.description, created_by=user.id
    )
    db.commit()
    db.refresh(team)
    return team


def list_my_teams(
    db: Session, user: User, *, page: int = 1, page_size: int = 20
) -> Page[TeamRead]:
    total = repository.count_teams_for_user(db, user.id)
    items = repository.list_teams_for_user(
        db, user.id, limit=page_size, offset=(page - 1) * page_size
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


def get_team(db: Session, team_id: int, user: User) -> Team:
    require_member(db, team_id, user)
    return _get_team_or_404(db, team_id)


def update_team(db: Session, team_id: int, data: TeamUpdate, user: User) -> Team:
    require_admin(db, team_id, user)
    team = _get_team_or_404(db, team_id)
    updated = repository.update_team(db, team, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(updated)
    return updated


def delete_team(db: Session, team_id: int, user: User) -> None:
    require_admin(db, team_id, user)
    repository.delete_team(db, _get_team_or_404(db, team_id))
    db.commit()


def list_members(
    db: Session, team_id: int, user: User, *, page: int = 1, page_size: int = 20
) -> Page[MemberRead]:
    require_member(db, team_id, user)
    total = repository.count_members(db, team_id)
    items = repository.list_members(
        db, team_id, limit=page_size, offset=(page - 1) * page_size
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


def add_member(db: Session, team_id: int, data: MemberAdd, user: User) -> TeamMember:
    require_admin(db, team_id, user)
    target = users_repository.get_by_email(db, data.email.lower())
    if not target:
        raise NotFoundError("User not found")
    if repository.get_membership(db, team_id, target.id):
        raise ConflictError("User is already a member")
    member = repository.add_member(db, team_id=team_id, user_id=target.id, role=data.role)
    db.commit()
    db.refresh(member)
    return member


def change_role(
    db: Session, team_id: int, target_user_id: int, role: TeamRole, user: User
) -> TeamMember:
    require_admin(db, team_id, user)
    member = repository.get_membership(db, team_id, target_user_id, for_update=True)
    if not member:
        raise NotFoundError("Member not found")
    if member.role == TeamRole.ADMIN and role != TeamRole.ADMIN:
        admin_count = repository.count_admins(db, team_id, for_update=True)
        if admin_count <= 1:
            raise ForbiddenError("Team must keep at least one admin")
    member.role = role
    saved = repository.save(db, member)
    db.commit()
    db.refresh(saved)
    return saved


def remove_member(db: Session, team_id: int, target_user_id: int, user: User) -> None:
    membership = require_member(db, team_id, user)
    # Admin can remove anyone, member can remove themselves
    if target_user_id != user.id and membership.role != TeamRole.ADMIN:
        raise ForbiddenError("Only team admins can remove members")
    member = repository.get_membership(db, team_id, target_user_id, for_update=True)
    if not member:
        raise NotFoundError("Member not found")
    if member.role == TeamRole.ADMIN:
        admin_count = repository.count_admins(db, team_id, for_update=True)
        if admin_count <= 1:
            raise ForbiddenError("Team must keep at least one admin")
    repository.delete_member(db, member)
    db.commit()