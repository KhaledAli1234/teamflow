from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.activity import service
from app.modules.activity.schemas import ActivityRead
from app.modules.users.models import User

router = APIRouter(tags=["activity"])


@router.get("/projects/{project_id}/activity", response_model=list[ActivityRead])
def project_activity(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return service.list_project_activity(db, project_id, user)