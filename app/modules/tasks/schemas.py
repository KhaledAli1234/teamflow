from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.tasks.models import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None
    assignee_id: int | None = Field(default=None, gt=0)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    assignee_id: int | None = Field(default=None, gt=0)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    assignee_id: int | None
    created_by: int
    created_at: datetime
    updated_at: datetime


class TaskPage(BaseModel):
    items: list[TaskRead]
    total: int
    page: int
    page_size: int