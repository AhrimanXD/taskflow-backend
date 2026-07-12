import uuid
from sqlalchemy.orm import Session

from app.crud.activity import create_activity
from app.models.activity import Activity
from app.schemas.activity import ActivityResponse
from app.websocket.manager import manager


async def record_and_broadcast(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str,
    object_type: str,
    object_id: uuid.UUID | None,
    summary: str,
) -> Activity:
    """Persist one activity row and push it to the workspace's live feed.

    Called after the primary mutation has already committed, so a failure here
    never rolls back the real change. `summary` is the actor-less phrase; the
    actor is joined for display.
    """
    activity = create_activity(
        db,
        workspace_id=workspace_id,
        actor_id=actor_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        summary=summary,
    )
    await manager.broadcast(
        {
            "type": "activity.created",
            "workspace_id": workspace_id,
            "activity": ActivityResponse.model_validate(activity).model_dump(
                mode="json"
            ),
        },
        workspace_id,
    )
    return activity
