from uuid import UUID
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.schemas.user import UserPublic


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    actor_id: UUID
    action: str
    object_type: str
    object_id: UUID | None
    summary: str
    created_at: datetime
    actor: UserPublic
