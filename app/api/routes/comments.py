from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.crud.comment import (
    create_comment,
    delete_comment,
    get_comment_by_id,
    get_comments_by_task,
)
from app.models.workspace_member import RoleEnum
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.activity import record_and_broadcast
from app.services.notification import notify
from app.services.task import get_workspace_task_or_raise
from app.websocket.manager import manager

router = APIRouter(
    prefix="/workspaces/{workspace_id}/tasks/{task_id}/comments",
    tags=["Comments"],
)


@router.get("", response_model=list[CommentResponse])
async def list_comments(
    workspace_id: int, task_id: int, db: SessionDep, current_user: CurrentUser
):
    """List a task's comments. Any workspace member."""
    get_workspace_task_or_raise(db, workspace_id, task_id, current_user.id)
    return get_comments_by_task(db, task_id)


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    workspace_id: int,
    task_id: int,
    body: CommentCreate,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Post a comment on a task. Any workspace member."""
    task, _ = get_workspace_task_or_raise(db, workspace_id, task_id, current_user.id)
    comment = create_comment(db, task_id, current_user.id, body)
    payload = CommentResponse.model_validate(comment).model_dump(mode="json")
    await manager.broadcast(
        {
            "type": "comment.created",
            "workspace_id": workspace_id,
            "task_id": task_id,
            "comment": payload,
        },
        workspace_id,
    )
    await record_and_broadcast(
        db,
        workspace_id=workspace_id,
        actor_id=current_user.id,
        action="comment.created",
        object_type="task",
        object_id=task_id,
        summary=f'commented on "{task.title}"',
    )
    # Notify the people who care about this task: its creator and assignee
    # (never the commenter themselves — notify() drops self-notifications).
    for rid in {task.owner_id, task.assignee_id} - {None}:
        await notify(
            db,
            recipient_id=rid,
            actor_id=current_user.id,
            type="comment.created",
            message=f'{current_user.username} commented on "{task.title}"',
            workspace_id=workspace_id,
        )
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_comment(
    workspace_id: int,
    task_id: int,
    comment_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Delete a comment: its author, or a workspace owner/admin."""
    _, role = get_workspace_task_or_raise(db, workspace_id, task_id, current_user.id)
    comment = get_comment_by_id(db, comment_id)
    if not comment or comment.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )
    if comment.author_id != current_user.id and role not in {
        RoleEnum.OWNER,
        RoleEnum.ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the comment author or a workspace owner/admin can delete this comment",
        )
    delete_comment(db, comment)
    await manager.broadcast(
        {
            "type": "comment.deleted",
            "workspace_id": workspace_id,
            "task_id": task_id,
            "comment": {"id": comment_id},
        },
        workspace_id,
    )
    return None
