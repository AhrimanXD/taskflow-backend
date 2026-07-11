from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm.exc import StaleDataError

from app.api.dependencies import CurrentUser, SessionDep
from app.crud.task import create_task, delete_task, get_tasks_by_workspace, update_task
from app.models.workspace_member import RoleEnum
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.activity import record_and_broadcast
from app.services.notification import notify
from app.services.task import (
    check_task_version_or_conflict,
    get_workspace_task_or_raise,
    validate_assignee_or_raise,
)
from app.services.workspace import get_member_role_or_raise
from app.websocket.manager import manager


router = APIRouter(prefix="/workspaces/{workspace_id}/tasks", tags=["Workspace Tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_workspace_tasks(
    workspace_id: int,
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    """List a workspace's tasks. Any member."""
    get_member_role_or_raise(db, workspace_id, current_user.id)
    return get_tasks_by_workspace(db, workspace_id, skip=skip, limit=limit)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace_task(
    workspace_id: int,
    task_data: TaskCreate,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Create a task in a workspace. Any member; workspace_id comes from the
    path, never the body. Optional assignee must be an active member."""
    get_member_role_or_raise(db, workspace_id, current_user.id)
    if task_data.assignee_id is not None:
        validate_assignee_or_raise(db, workspace_id, task_data.assignee_id)
    task = create_task(
        db, task_data, owner_id=current_user.id, workspace_id=workspace_id
    )
    event = {
        "type": "task.created",
        "workspace_id": workspace_id,
        "task": TaskResponse.model_validate(task).model_dump(mode="json"),
    }
    await manager.broadcast(event, workspace_id)
    await record_and_broadcast(
        db,
        workspace_id=workspace_id,
        actor_id=current_user.id,
        action="task.created",
        object_type="task",
        object_id=task.id,
        summary=f'created "{task.title}"',
    )
    if task.assignee_id is not None:
        await notify(
            db,
            recipient_id=task.assignee_id,
            actor_id=current_user.id,
            type="task.assigned",
            message=f'{current_user.username} assigned you "{task.title}"',
            workspace_id=workspace_id,
        )
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_workspace_task(
    workspace_id: int,
    task_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Get one workspace task. Any member."""
    task, _ = get_workspace_task_or_raise(db, workspace_id, task_id, current_user.id)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_workspace_task(
    workspace_id: int,
    task_id: int,
    task_data: TaskUpdate,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Edit a workspace task (title/status/due date/assignee). Any member.
    assignee_id: explicit null = unassign (allowed); a non-null assignee is
    validated as an active workspace member."""
    task, _ = get_workspace_task_or_raise(db, workspace_id, task_id, current_user.id)
    # OCC: reject a stale edit with the current state before we touch anything.
    check_task_version_or_conflict(task, task_data.version)
    if task_data.assignee_id is not None:
        validate_assignee_or_raise(db, workspace_id, task_data.assignee_id)
    try:
        task = update_task(db, task, task_data)
    except StaleDataError:
        # A concurrent commit slipped in between our load and flush. Surface the
        # same 409 the pre-check uses, with the freshly-current task.
        db.rollback()
        task, _ = get_workspace_task_or_raise(db, workspace_id, task_id, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "This task was changed by someone else. Please review and retry.",
                "current": TaskResponse.model_validate(task).model_dump(mode="json"),
            },
        )
    event = {
        "type": "task.updated",
        "workspace_id": workspace_id,
        "task": TaskResponse.model_validate(task).model_dump(mode="json"),
    }
    await manager.broadcast(event, workspace_id)
    # Describe the edit from the fields the client actually sent (version aside).
    changed = task_data.model_fields_set - {"version"}
    if "status" in changed and task_data.status is not None:
        summary = f'moved "{task.title}" to {task_data.status.value}'
    elif "assignee_id" in changed:
        summary = f'reassigned "{task.title}"'
    else:
        summary = f'updated "{task.title}"'
    await record_and_broadcast(
        db,
        workspace_id=workspace_id,
        actor_id=current_user.id,
        action="task.updated",
        object_type="task",
        object_id=task.id,
        summary=summary,
    )
    if "assignee_id" in changed and task.assignee_id is not None:
        await notify(
            db,
            recipient_id=task.assignee_id,
            actor_id=current_user.id,
            type="task.assigned",
            message=f'{current_user.username} assigned you "{task.title}"',
            workspace_id=workspace_id,
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace_task(
    workspace_id: int,
    task_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Delete a workspace task: the task's creator OR a workspace
    owner/admin. Plain members can't delete tasks they didn't create."""
    task, role = get_workspace_task_or_raise(db, workspace_id, task_id, current_user.id)
    if task.owner_id != current_user.id and role not in {
        RoleEnum.OWNER,
        RoleEnum.ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the task creator or a workspace owner/admin can delete this task",
        )
    title = task.title
    delete_task(db, task)
    event = {
        "type": "task.deleted",
        "workspace_id": workspace_id,
        "task": {"id": task_id},
    }
    await manager.broadcast(event, workspace_id)
    await record_and_broadcast(
        db,
        workspace_id=workspace_id,
        actor_id=current_user.id,
        action="task.deleted",
        object_type="task",
        object_id=task_id,
        summary=f'deleted "{title}"',
    )
    return None
