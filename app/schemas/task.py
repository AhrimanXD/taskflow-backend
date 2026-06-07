from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional

class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    ONGOING = "ongoing"
    COMPLETED = "completed"

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255) 
    description: str | None = None
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    assignee_id: int | None = None
    due_date: datetime | None = None

    @field_validator('title',mode='before')
    @classmethod
    def validate_title(cls, value: str):
        if value.strip() == "":
            raise ValueError("Title Cannot Be Empty String")
        value = value.strip()
        return value

    
    @field_validator('description',mode='before')
    @classmethod
    def validate_description(cls, value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None


def strip_or_none(v):
    if v is None:
        return None
    if not isinstance(v, str):
        return v
    v2 = v.strip()
    if v2 == "":
        raise ValueError("Cannot be empty or whitespace-only")
    return v2


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: TaskStatusEnum | None = None
    assignee_id: int | None = None
    due_date: datetime | None = None
    

    @field_validator("title", "description", mode="before")
    @classmethod
    def no_blank_strings(cls, v):
        return strip_or_none(v)


class TaskResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    status: str
    owner_id: int
    assignee_id: int | None
    workspace_id: int | None
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime

