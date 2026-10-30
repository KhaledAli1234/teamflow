from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.schemas import Page, UserSummary


class CommentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    body: str = Field(min_length=1, max_length=5000)


class CommentUpdate(BaseModel):
    """Separate schema for edits — semantically distinct from creation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    body: str = Field(min_length=1, max_length=5000)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    author_id: int
    author: UserSummary
    body: str
    created_at: datetime
    updated_at: datetime


CommentPage = Page[CommentRead]