import uuid
from sqlalchemy.orm import Session, selectinload

from app.models.activity import Activity


def create_activity(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str,
    object_type: str,
    object_id: uuid.UUID | None,
    summary: str,
) -> Activity:
    activity = Activity(
        workspace_id=workspace_id,
        actor_id=actor_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        summary=summary,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_workspace_activity(
    db: Session, workspace_id: uuid.UUID, skip: int = 0, limit: int = 50
) -> list[Activity]:
    return (
        db.query(Activity)
        .filter(Activity.workspace_id == workspace_id)
        .options(selectinload(Activity.actor))
        .order_by(Activity.created_at.desc(), Activity.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
