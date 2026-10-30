from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Generic paginated response. Used by all list endpoints that support pagination."""

    items: list[T]
    total: int
    page: int
    page_size: int


class UserSummary(BaseModel):
    """Lightweight user representation embedded inside other responses (members, comments, activity)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
