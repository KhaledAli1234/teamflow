from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.modules.projects.models import ProjectStatus


class ProjectCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: date | None = None
    due_date: date | None = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValueError("due_date cannot be before start_date")
        return self


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus | None = None
    start_date: date | None = None
    due_date: date | None = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValueError("due_date cannot be before start_date")
        return self


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    name: str
    description: str | None
    status: ProjectStatus
    start_date: date | None
    due_date: date | None
    created_by: int
    created_at: datetime


class ProjectMemberAdd(BaseModel):
    email: EmailStr


class ProjectMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    joined_at: datetime