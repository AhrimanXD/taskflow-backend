from fastapi import APIRouter

from app.api.dependencies import CurrentUser, SessionDep
from app.schemas.stats import StatsOverview
from app.services.stats import get_overview

router = APIRouter()


@router.get("/overview", response_model=StatsOverview)
async def stats_overview(db: SessionDep, current_user: CurrentUser):
    """Aggregate stats for the current user's home dashboard."""
    return get_overview(db, current_user.id)
