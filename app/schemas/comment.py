from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

from app.schemas.user import UserPublic


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)

    @field_validator("body", mode="before")
    @classmethod
    def strip_body(cls, v):
        if v is None or str(v).strip() == "":
            raise ValueError("Comment cannot be empty")
        return str(v).strip()


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    author_id: UUID
    body: str
    created_at: datetime
    author: UserPublic
