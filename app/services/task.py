import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud.member import get_member
from app.crud.task import get_task_by_id
from app.models.task import Task
from app.models.workspace_member import RoleEnum
from app.schemas.task import TaskResponse
from app.services.workspace import get_member_role_or_raise


def check_task_version_or_conflict(task: Task, expected_version: int | None) -> None:
    """Optimistic-concurrency pre-check for workspace task edits.

    The client must send the `version` it last saw. If it's missing -> 400
    (the client didn't opt into OCC). If it's stale -> 409 with the *current*
    task in the body, so the frontend can show 'this changed — review & retry'
    instead of silently clobbering the other member's edit. The true
    read-then-commit race is still caught separately by version_id_col
    (StaleDataError) in the route.
    """
    if expected_version is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="version is required for workspace task updates",
        )
    if task.version != expected_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "This task was changed by someone else. Please review and retry.",
                "current": TaskResponse.model_validate(task).model_dump(mode="json"),
            },
        )


def get_personal_task_or_raise(db: Session, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
    """Guard for the personal tree (/api/tasks/*): owner-scoped and FENCED to
    tasks with no workspace. A workspace task is invisible here (404) even to
    its creator — it lives under /api/workspaces/{id}/tasks/* instead, so each
    tree keeps exactly one auth model."""
    task = get_task_by_id(db, task_id)
    if not task or task.workspace_id is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if task.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task",
        )
    return task


def get_workspace_task_or_raise(
    db: Session,
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[Task, RoleEnum]:
    """Guard for the workspace tree. The order of checks matters:

    1. Load the task -> 404 if it doesn't exist.
    2. IDOR check: the task's REAL parent must match the path workspace.
       Without this, a member of W1 could act on W2's task via
       /workspaces/W1/tasks/{w2_task_id} — they'd pass the membership check
       (run against the caller-supplied W1) while touching a W2 resource.
       Mismatch -> 404, not 403, so we don't leak that the task exists in
       some other workspace. This also catches personal tasks
       (workspace_id IS NULL never equals a path workspace_id).
    3. Only then check membership, against the now-verified workspace.

    Returns (task, caller's role) so routes can apply role rules (e.g. the
    delete policy) without a second membership lookup.
    """
    task = get_task_by_id(db, task_id)
    if not task or task.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    role = get_member_role_or_raise(db, workspace_id, user_id)
    return task, role


def validate_assignee_or_raise(db: Session, workspace_id: uuid.UUID, assignee_id: uuid.UUID) -> None:
    """An assignee must be an ACTIVE member of the task's workspace.

    400 (not 404): the URL is fine — it's the request body that names an
    invalid assignee. Rank-blind: any member may be assigned, role ignored.
    """
    member = get_member(db, workspace_id, assignee_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be a member of this workspace",
        )
    if not member.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee account is inactive",
        )
