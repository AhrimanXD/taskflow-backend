from pydantic import BaseModel, EmailStr, ConfigDict
from app.schemas.workspace import WorkspaceResponse
from app.models.invitation import InviteRole, Status
from app.schemas.user import UserPublic
from datetime import datetime

class InvitationCreate(BaseModel):
    invitee_email: EmailStr
    role: InviteRole = InviteRole.MEMBER

class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invitee: UserPublic
    inviter: UserPublic
    workspace: WorkspaceResponse 
    status: Status
    created_at: datetime
