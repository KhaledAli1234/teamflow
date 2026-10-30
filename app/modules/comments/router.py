from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.comments import service
from app.modules.comments.schemas import CommentCreate, CommentPage, CommentRead, CommentUpdate
from app.modules.users.models import User

router = APIRouter(tags=["comments"])


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment",
    description="Adds a comment to a task. Notifies the task assignee and creator.",
)
def add_comment(
    task_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.add_comment(db, task_id, data, user)


@router.get(
    "/tasks/{task_id}/comments",
    response_model=CommentPage,
    summary="List comments on a task",
)
def list_comments(
    task_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.list_comments(db, task_id, user, page=page, page_size=page_size)


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentRead,
    summary="Edit a comment",
    description="Only the comment's author can edit it.",
)
def edit_comment(
    comment_id: int,
    data: CommentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.edit_comment(db, comment_id, data, user)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
    description="The comment's author or a team admin/project manager can delete a comment.",
)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service.delete_comment(db, comment_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)