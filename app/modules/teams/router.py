from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.teams import service
from app.modules.teams.schemas import (
    MemberAdd,
    MemberRead,
    MemberRoleUpdate,
    TeamCreate,
    TeamRead,
    TeamUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(
    data: TeamCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.create_team(db, data, user)


@router.get("", response_model=list[TeamRead])
def list_my_teams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.list_my_teams(db, user)


@router.get("/{team_id}", response_model=TeamRead)
def get_team(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.get_team(db, team_id, user)


@router.patch("/{team_id}", response_model=TeamRead)
def update_team(
    team_id: int,
    data: TeamUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.update_team(db, team_id, data, user)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service.delete_team(db, team_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{team_id}/members", response_model=list[MemberRead])
def list_members(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.list_members(db, team_id, user)


@router.post(
    "/{team_id}/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED
)
def add_member(
    team_id: int,
    data: MemberAdd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.add_member(db, team_id, data, user)


@router.patch("/{team_id}/members/{user_id}", response_model=MemberRead)
def change_role(
    team_id: int,
    user_id: int,
    data: MemberRoleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.change_role(db, team_id, user_id, data.role, user)


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service.remove_member(db, team_id, user_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)