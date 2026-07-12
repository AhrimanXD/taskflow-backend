from uuid import UUID
import re

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.crud.comment import (
    create_comment,
    delete_comment,
    get_comment_by_id,
    get_comments_by_task,
)
from app.crud.member import get_workspace_members
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

_MENTION_RE = re.compile(r"@(\w+)")


def _mentioned_user_ids(body: str, members) -> set[UUID]:
    """Resolve @username tokens in a comment against the workspace's members
    (case-insensitive). Unknown handles are ignored."""
    by_name = {m.user.username.lower(): m.user_id for m in members}
    ids = set()
    for handle in set(_MENTION_RE.findall(body)):
        uid = by_name.get(handle.lower())
        if uid is not None:
            ids.add(uid)
    return ids


@router.get("", response_model=list[CommentResponse])
async def list_comments(
    workspace_id: UUID, task_id: UUID, db: SessionDep, current_user: CurrentUser
):
    """List a task's comments. Any workspace member."""
    get_workspace_task_or_raise(db, workspace_id, task_id, current_user.id)
    return get_comments_by_task(db, task_id)


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    workspace_id: UUID,
    task_id: UUID,
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
    # @mentions take precedence: mentioned members get a "mentioned you"
    # notification, and the task's creator/assignee get the generic "commented"
    # one only if they weren't already mentioned (no double-ping).
    mentioned = _mentioned_user_ids(body.body, get_workspace_members(db, workspace_id))
    mentioned.discard(current_user.id)
    for rid in mentioned:
        await notify(
            db,
            recipient_id=rid,
            actor_id=current_user.id,
            type="comment.mention",
            message=f'{current_user.username} mentioned you in a comment on "{task.title}"',
            workspace_id=workspace_id,
        )
    for rid in {task.owner_id, task.assignee_id} - {None} - mentioned:
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
    workspace_id: UUID,
    task_id: UUID,
    comment_id: UUID,
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
