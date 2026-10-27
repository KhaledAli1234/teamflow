from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.teams.models import Team, TeamMember, TeamRole


def create_team(db: Session, *, name: str, description: str | None, created_by: int) -> Team:
    team = Team(name=name, description=description, created_by=created_by)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=created_by, role=TeamRole.ADMIN))
    db.commit()
    db.refresh(team)
    return team


def get_team(db: Session, team_id: int) -> Team | None:
    return db.get(Team, team_id)


def list_teams_for_user(db: Session, user_id: int) -> list[Team]:
    stmt = (
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_id)
        .order_by(Team.id)
    )
    return list(db.scalars(stmt))


def get_membership(db: Session, team_id: int, user_id: int) -> TeamMember | None:
    return db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.user_id == user_id
        )
    )


def list_members(db: Session, team_id: int) -> list[TeamMember]:
    return list(db.scalars(select(TeamMember).where(TeamMember.team_id == team_id)))


def add_member(db: Session, *, team_id: int, user_id: int, role: TeamRole) -> TeamMember:
    member = TeamMember(team_id=team_id, user_id=user_id, role=role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def update_team(db: Session, team: Team, data: dict) -> Team:
    for key, value in data.items():
        setattr(team, key, value)
    db.commit()
    db.refresh(team)
    return team


def delete_team(db: Session, team: Team) -> None:
    db.delete(team)
    db.commit()


def save(db: Session, obj):
    db.commit()
    db.refresh(obj)
    return obj


def delete_member(db: Session, member: TeamMember) -> None:
    db.delete(member)
    db.commit()