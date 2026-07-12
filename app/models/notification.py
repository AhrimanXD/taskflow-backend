import uuid

from sqlalchemy import String, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import TYPE_CHECKING

from app.core.database import Base
from app.core.ids import uuid7

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base):
    """A per-user inbox item: something that concerns one specific user
    (assigned a task, someone commented on their task, role changed, removed).
    `message` is pre-rendered including the actor's name."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(String(500))
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(default=False, server_default="false", index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    actor: Mapped["User"] = relationship(foreign_keys=[actor_id])
