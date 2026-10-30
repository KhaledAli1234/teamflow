from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.teams import service
from app.modules.teams.schemas import (
    MemberAdd,
    MemberPage,
    MemberRead,
    MemberRoleUpdate,
    TeamCreate,
    TeamPage,
    TeamRead,
    TeamUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post(
    "",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a team",
    description="Creates a new team and automatically assigns the caller as its first ADMIN.",
)
def create_team(
    data: TeamCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.create_team(db, data, user)


@router.get(
    "",
    response_model=TeamPage,
    summary="List my teams",
    description="Returns a paginated list of all teams the current user belongs to.",
)
def list_my_teams(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.list_my_teams(db, user, page=page, page_size=page_size)


@router.get(
    "/{team_id}",
    response_model=TeamRead,
    summary="Get a team",
    responses={404: {"description": "Team not found or user is not a member"}},
)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.get_team(db, team_id, user)


@router.patch(
    "/{team_id}",
    response_model=TeamRead,
    summary="Update a team",
    description="Only team ADMINs can update team details.",
    responses={403: {"description": "Not an admin"}},
)
def update_team(
    team_id: int,
    data: TeamUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.update_team(db, team_id, data, user)


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a team",
    description="Only team ADMINs can delete a team. This cascades to all projects and tasks.",
)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service.delete_team(db, team_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{team_id}/members",
    response_model=MemberPage,
    summary="List team members",
)
def list_members(
    team_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.list_members(db, team_id, user, page=page, page_size=page_size)


@router.post(
    "/{team_id}/members",
    response_model=MemberRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a member",
    description="Only ADMINs can add members. The user must already be registered.",
)
def add_member(
    team_id: int,
    data: MemberAdd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.add_member(db, team_id, data, user)


@router.patch(
    "/{team_id}/members/{user_id}",
    response_model=MemberRead,
    summary="Change a member's role",
    description="Only ADMINs can change roles. The last admin cannot be demoted.",
)
def change_role(
    team_id: int,
    user_id: int,
    data: MemberRoleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.change_role(db, team_id, user_id, data.role, user)


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member",
    description="ADMINs can remove anyone. Members can remove themselves (leave). The last admin cannot be removed.",
)
def remove_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service.remove_member(db, team_id, user_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)