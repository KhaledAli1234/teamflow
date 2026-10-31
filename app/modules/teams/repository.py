from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.teams.models import Team, TeamMember, TeamRole


def create_team(db: Session, *, name: str, description: str | None, created_by: int) -> Team:
    team = Team(name=name, description=description, created_by=created_by)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=created_by, role=TeamRole.ADMIN))
    db.flush()
    return team


def get_team(db: Session, team_id: int) -> Team | None:
    return db.get(Team, team_id)


def list_teams_for_user(
    db: Session, user_id: int, *, limit: int | None = None, offset: int = 0
) -> list[Team]:
    stmt = (
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_id)
        .order_by(Team.id)
        .offset(offset)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def count_teams_for_user(db: Session, user_id: int) -> int:
    stmt = select(func.count()).select_from(TeamMember).where(TeamMember.user_id == user_id)
    return db.scalar(stmt) or 0


def get_membership(
    db: Session, team_id: int, user_id: int, *, for_update: bool = False
) -> TeamMember | None:
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.user_id == user_id
    )
    if for_update:
        stmt = stmt.with_for_update()
    return db.scalar(stmt)


def list_members(
    db: Session, team_id: int, *, limit: int | None = None, offset: int = 0
) -> list[TeamMember]:
    stmt = (
        select(TeamMember)
        .where(TeamMember.team_id == team_id)
        .order_by(TeamMember.id)
        .offset(offset)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def count_members(db: Session, team_id: int) -> int:
    stmt = select(func.count()).select_from(TeamMember).where(TeamMember.team_id == team_id)
    return db.scalar(stmt) or 0


def count_admins(db: Session, team_id: int, *, for_update: bool = False) -> int:
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.role == TeamRole.ADMIN
    )
    if for_update:
        stmt = stmt.with_for_update()
        return len(list(db.scalars(stmt)))
    return db.scalar(select(func.count()).select_from(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.role == TeamRole.ADMIN
    )) or 0


def add_member(db: Session, *, team_id: int, user_id: int, role: TeamRole) -> TeamMember:
    member = TeamMember(team_id=team_id, user_id=user_id, role=role)
    db.add(member)
    db.flush()
    return member


def update_team(db: Session, team: Team, data: dict) -> Team:
    for key, value in data.items():
        setattr(team, key, value)
    db.flush()
    return team


def delete_team(db: Session, team: Team) -> None:
    db.delete(team)
    db.flush()


def save(db: Session, obj: TeamMember) -> TeamMember:
    db.flush()
    return obj


def delete_member(db: Session, member: TeamMember) -> None:
    db.delete(member)
    db.flush()