from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.projects.models import Project, ProjectMember


def create_project(db: Session, *, team_id: int, created_by: int, data: dict) -> Project:
    project = Project(team_id=team_id, created_by=created_by, **data)
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=created_by))
    db.flush()
    return project


def get_project(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)


def list_projects_for_team(db: Session, team_id: int) -> list[Project]:
    return list(
        db.scalars(select(Project).where(Project.team_id == team_id).order_by(Project.id))
    )


def list_projects_for_member(db: Session, team_id: int, user_id: int) -> list[Project]:
    stmt = (
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(Project.team_id == team_id, ProjectMember.user_id == user_id)
        .order_by(Project.id)
    )
    return list(db.scalars(stmt))


def get_membership(db: Session, project_id: int, user_id: int) -> ProjectMember | None:
    return db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
    )


def list_members(db: Session, project_id: int) -> list[ProjectMember]:
    return list(
        db.scalars(select(ProjectMember).where(ProjectMember.project_id == project_id))
    )


def add_member(db: Session, *, project_id: int, user_id: int) -> ProjectMember:
    member = ProjectMember(project_id=project_id, user_id=user_id)
    db.add(member)
    db.flush()
    return member


def delete_member(db: Session, member: ProjectMember) -> None:
    db.delete(member)
    db.flush()


def update_project(db: Session, project: Project, data: dict) -> Project:
    for key, value in data.items():
        setattr(project, key, value)
    db.flush()
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.flush()