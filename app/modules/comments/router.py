from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.db.session import get_db
from app.modules.comments import service
from app.modules.comments.schemas import CommentCreate, CommentRead
from app.modules.users.models import User

router = APIRouter(tags=["comments"])


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    task_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.add_comment(db, task_id, data, user)


@router.get("/tasks/{task_id}/comments", response_model=list[CommentRead])
def list_comments(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return service.list_comments(db, task_id, user)


@router.patch("/comments/{comment_id}", response_model=CommentRead)
def edit_comment(
    comment_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.edit_comment(db, comment_id, data, user)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    service.delete_comment(db, comment_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)