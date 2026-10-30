from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.common.schemas import Page, UserSummary


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int | None
    actor_id: int | None
    actor: UserSummary | None
    action: str
    entity_type: str
    entity_id: int
    details: dict | None
    created_at: datetime


ActivityPage = Page[ActivityRead]