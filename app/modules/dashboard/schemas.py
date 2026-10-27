from pydantic import BaseModel


class StatusCounts(BaseModel):
    todo: int = 0
    in_progress: int = 0
    done: int = 0


class ProjectProgress(BaseModel):
    project_id: int
    name: str
    total_tasks: int
    done_tasks: int
    overdue_tasks: int
    progress_percent: float


class MemberWorkload(BaseModel):
    user_id: int
    full_name: str
    total_tasks: int
    open_tasks: int


class TeamDashboard(BaseModel):
    total_projects: int
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    tasks_by_status: StatusCounts
    projects: list[ProjectProgress]
    workload: list[MemberWorkload]