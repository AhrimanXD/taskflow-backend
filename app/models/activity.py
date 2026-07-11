from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Activity(Base):
    """An audit-log / feed row: <actor> did <action> to <object> at <time>.

    `summary` is the pre-rendered human phrase without the actor (e.g.
    'moved "Draft emails" to completed'); the actor is joined for display.
    """

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column(String(50))
    object_type: Mapped[str] = mapped_column(String(50))
    object_id: Mapped[int | None] = mapped_column(nullable=True)
    summary: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    actor: Mapped["User"] = relationship()
