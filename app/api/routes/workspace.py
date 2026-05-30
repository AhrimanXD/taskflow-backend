from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, SessionDep
from app.crud.workspace import create_workspace, delete_workspace, get_workspaces_by_user, update_workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services.workspace import get_workspace_or_raise

router = APIRouter()


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    return get_workspaces_by_user(db, user_id=current_user.id, skip=skip, limit=limit)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_new_workspace(
    workspace_data: WorkspaceCreate,
    db: SessionDep,
    current_user: CurrentUser,
):
    return create_workspace(db, workspace_data, owner_id=current_user.id)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    return get_workspace_or_raise(db, workspace_id, user_id=current_user.id)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_existing_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    db: SessionDep,
    current_user: CurrentUser,
):
    workspace = get_workspace_or_raise(db, workspace_id, user_id=current_user.id, require_owner=True)
    return update_workspace(db, workspace, workspace_data.model_dump(exclude_unset=True))


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_workspace(
    workspace_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    workspace = get_workspace_or_raise(db, workspace_id, user_id=current_user.id, require_owner=True)
    delete_workspace(db, workspace)
    return None
