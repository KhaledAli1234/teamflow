from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.activity import service
from app.modules.activity.schemas import ActivityPage, ActivityRead
from app.modules.users.models import User

router = APIRouter(tags=["activity"])


@router.get(
    "/projects/{project_id}/activity",
    response_model=ActivityPage,
    summary="Get project activity log",
    description="Returns paginated activity history for a project. Includes actor name embedded in each record.",
)
def project_activity(
    project_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.list_project_activity(db, project_id, user, page=page, page_size=page_size)