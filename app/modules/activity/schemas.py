from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int | None
    actor_id: int | None
    action: str
    entity_type: str
    entity_id: int
    details: dict | None
    created_at: datetime