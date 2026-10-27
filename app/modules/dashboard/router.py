from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.dashboard import service
from app.modules.dashboard.schemas import ProjectProgress, TeamDashboard
from app.modules.users.models import User

router = APIRouter(tags=["dashboard"])


@router.get("/teams/{team_id}/dashboard", response_model=TeamDashboard)
def team_dashboard(
    team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return service.team_dashboard(db, team_id, user)


@router.get("/projects/{project_id}/progress", response_model=ProjectProgress)
def project_progress(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return service.project_progress(db, project_id, user)