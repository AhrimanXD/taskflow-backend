from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255) 
    description: Optional[str] = None
    status: str = "pending"

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
    status: Optional[str] = None
    assignee_id: int | None = None
    

    @field_validator("title", "description", "status", mode="before")
    @classmethod
    def no_blank_strings(cls, v):
        return strip_or_none(v)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    owner_id: int
    assignee_id: int | None
    workspace_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
