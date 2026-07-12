import uuid
from sqlalchemy import func, update
from sqlalchemy.orm import Session, selectinload

from app.models.notification import Notification


def create_notification(
    db: Session,
    *,
    recipient_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    type: str,
    message: str,
    workspace_id: uuid.UUID | None,
) -> Notification:
    notification = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        type=type,
        message=message,
        workspace_id=workspace_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notifications_for_user(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 30
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.recipient_id == user_id)
        .options(selectinload(Notification.actor))
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_unread(db: Session, user_id: uuid.UUID) -> int:
    return (
        db.query(func.count())
        .select_from(Notification)
        .filter(Notification.recipient_id == user_id, Notification.is_read.is_(False))
        .scalar()
        or 0
    )


def get_notification_by_id(db: Session, notification_id: uuid.UUID) -> Notification | None:
    return db.query(Notification).filter(Notification.id == notification_id).first()


def mark_read(db: Session, notification: Notification) -> Notification:
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: uuid.UUID) -> None:
    db.execute(
        update(Notification)
        .where(Notification.recipient_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
