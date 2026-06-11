from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.crud.task import create_task, delete_task, get_tasks_by_workspace, update_task
from app.models.workspace_member import RoleEnum
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task import get_workspace_task_or_raise, validate_assignee_or_raise
from app.services.workspace import get_member_role_or_raise

router = APIRouter(prefix="/workspaces/{workspace_id}/tasks", tags=["Workspace Tasks"])


@router.get("", response_model=list[TaskResponse])
def list_workspace_tasks(
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
def create_workspace_task(
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
    return create_task(db, task_data, owner_id=current_user.id, workspace_id=workspace_id)


@router.get("/{task_id}", response_model=TaskResponse)
def get_workspace_task(
    workspace_id: int,
    task_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Get one workspace task. Any member."""
    task, _ = get_workspace_task_or_raise(db, workspace_id, task_id, current_user.id)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_workspace_task(
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
    if task_data.assignee_id is not None:
        validate_assignee_or_raise(db, workspace_id, task_data.assignee_id)
    return update_task(db, task, task_data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace_task(
    workspace_id: int,
    task_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Delete a workspace task: the task's creator OR a workspace
    owner/admin. Plain members can't delete tasks they didn't create."""
    task, role = get_workspace_task_or_raise(db, workspace_id, task_id, current_user.id)
    if task.owner_id != current_user.id and role not in {RoleEnum.OWNER, RoleEnum.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the task creator or a workspace owner/admin can delete this task",
        )
    delete_task(db, task)
    return None
