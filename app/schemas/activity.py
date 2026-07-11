from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.schemas.user import UserPublic


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    actor_id: int
    action: str
    object_type: str
    object_id: int | None
    summary: str
    created_at: datetime
    actor: UserPublic
