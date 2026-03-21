from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import SessionDep, CurrentUser
from app.crud.task import create_task, get_task_by_id, get_tasks_by_owner, update_task, delete_task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter()


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    """Get all tasks for the current user."""
    tasks = get_tasks_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return tasks


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_new_task(
    task_data: TaskCreate,
    db: SessionDep,
    current_user: CurrentUser
):
    """Create a new task."""
    task = create_task(db, task_data, owner_id=current_user.id)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: SessionDep,
    current_user: CurrentUser
):
    """Get a specific task by ID."""
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task"
        )
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_existing_task(
    task_id: int,
    task_data: TaskUpdate,
    db: SessionDep,
    current_user: CurrentUser
):
    """Update a task."""
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this task"
        )
    updated_task = update_task(db, task, task_data)
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_task(
    task_id: int,
    db: SessionDep,
    current_user: CurrentUser
):
    """Delete a task."""
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task"
        )
    delete_task(db, task)
    return None
