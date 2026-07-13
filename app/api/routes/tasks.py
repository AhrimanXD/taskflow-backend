from uuid import UUID
from fastapi import APIRouter, status

from app.api.dependencies import SessionDep, CurrentUser
from app.crud.task import create_task, get_tasks_by_owner, update_task, delete_task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task import get_personal_task_or_raise

router = APIRouter()


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    """Get the current user's PERSONAL tasks (workspace tasks live under
    /api/workspaces/{id}/tasks)."""
    tasks = get_tasks_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return tasks


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_data: TaskCreate,
    db: SessionDep,
    current_user: CurrentUser
):
    """Create a personal task. Personal tasks are not assignable, so any
    assignee_id in the body is ignored."""
    task_data = task_data.model_copy(update={"assignee_id": None})
    task = create_task(db, task_data, owner_id=current_user.id)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: SessionDep,
    current_user: CurrentUser
):
    """Get a specific personal task by ID."""
    return get_personal_task_or_raise(db, task_id, current_user.id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_existing_task(
    task_id: UUID,
    task_data: TaskUpdate,
    db: SessionDep,
    current_user: CurrentUser
):
    """Update a personal task. assignee_id is ignored — personal tasks are
    not assignable."""
    task = get_personal_task_or_raise(db, task_id, current_user.id)
    if "assignee_id" in task_data.model_fields_set:
        task_data = TaskUpdate(
            **task_data.model_dump(exclude_unset=True, exclude={"assignee_id"})
        )
    updated_task = update_task(db, task, task_data)
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_task(
    task_id: UUID,
    db: SessionDep,
    current_user: CurrentUser
):
    """Delete a personal task."""
    task = get_personal_task_or_raise(db, task_id, current_user.id)
    delete_task(db, task)
    return None
