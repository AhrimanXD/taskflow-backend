from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.schemas.user import UserPublic


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    message: str
    workspace_id: int | None
    is_read: bool
    created_at: datetime
    actor: UserPublic | None


class UnreadCount(BaseModel):
    count: int
