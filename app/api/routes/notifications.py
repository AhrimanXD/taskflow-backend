from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.crud.notification import (
    count_unread,
    get_notification_by_id,
    get_notifications_for_user,
    mark_all_read,
    mark_read,
)
from app.schemas.notification import NotificationResponse, UnreadCount

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    db: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 30
):
    """The current user's notifications, newest first."""
    return get_notifications_for_user(db, current_user.id, skip=skip, limit=limit)


@router.get("/unread-count", response_model=UnreadCount)
async def unread_count(db: SessionDep, current_user: CurrentUser):
    return {"count": count_unread(db, current_user.id)}


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def read_all(db: SessionDep, current_user: CurrentUser):
    mark_all_read(db, current_user.id)
    return None


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def read_one(
    notification_id: UUID, db: SessionDep, current_user: CurrentUser
):
    n = get_notification_by_id(db, notification_id)
    if not n or n.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return mark_read(db, n)
