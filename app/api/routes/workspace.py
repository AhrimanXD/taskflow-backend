from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser, SessionDep
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate
router = APIRouter()

@router.get("")
async def get_workspaces_by_user(db: SessionDep):
    pass

@router.post("")
async def create_workspace(
        workspace_data: WorkspaceCreate,
        db: SessionDep,
        current_user: CurrentUser):
    pass
