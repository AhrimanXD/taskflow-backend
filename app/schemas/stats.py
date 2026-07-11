from pydantic import BaseModel

from app.schemas.activity import ActivityResponse


class StatsOverview(BaseModel):
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    overdue: int
    assigned_to_me: int
    workspace_count: int
    recent_activity: list[ActivityResponse]
