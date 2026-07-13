import uuid
from sqlalchemy.orm import Session

from app.crud.notification import create_notification
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from app.websocket.manager import manager


async def notify(
    db: Session,
    *,
    recipient_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    type: str,
    message: str,
    workspace_id: uuid.UUID | None = None,
) -> Notification | None:
    """Create a notification for one user and push it to their live channel.
    No-op when the recipient is the actor (don't notify yourself)."""
    if recipient_id == actor_id:
        return None
    notification = create_notification(
        db,
        recipient_id=recipient_id,
        actor_id=actor_id,
        type=type,
        message=message,
        workspace_id=workspace_id,
    )
    await manager.send_to_user(
        {
            "type": "notification.created",
            "notification": NotificationResponse.model_validate(notification).model_dump(
                mode="json"
            ),
        },
        recipient_id,
    )
    return notification
