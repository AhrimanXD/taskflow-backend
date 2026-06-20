from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.workspace_member import RoleEnum
from app.schemas.user import UserPublic  # wherever UserPublic actually lives


class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class WorkspaceResponse(WorkspaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime


class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role: RoleEnum
    user: UserPublic
