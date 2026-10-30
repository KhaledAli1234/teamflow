from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.common.schemas import Page


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    message: str
    data: dict | None
    is_read: bool
    created_at: datetime


NotificationPage = Page[NotificationRead]