from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.schemas import Page, UserSummary
from app.modules.teams.models import TeamRole


class TeamCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class TeamUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_by: int
    created_at: datetime


class MemberAdd(BaseModel):
    email: EmailStr
    role: TeamRole = TeamRole.MEMBER


class MemberRoleUpdate(BaseModel):
    role: TeamRole


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role: TeamRole
    joined_at: datetime
    user: UserSummary


TeamPage = Page[TeamRead]
MemberPage = Page[MemberRead]