from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.projects import service
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectMemberRead,
    ProjectRead,
    ProjectUpdate,
)
from app.modules.users.models import User

router = APIRouter(tags=["projects"])


@router.post(
    "/teams/{team_id}/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    team_id: int,
    data: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.create_project(db, team_id, data, user)


@router.get("/teams/{team_id}/projects", response_model=list[ProjectRead])
def list_projects(
    team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return service.list_projects(db, team_id, user)


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return service.get_accessible_project(db, project_id, user)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.update_project(db, project_id, data, user)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    service.delete_project(db, project_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberRead])
def list_members(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return service.list_members(db, project_id, user)


@router.post(
    "/projects/{project_id}/members",
    response_model=ProjectMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    project_id: int,
    data: ProjectMemberAdd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.add_member(db, project_id, data, user)


@router.delete(
    "/projects/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service.remove_member(db, project_id, user_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)