import uuid

from sqlalchemy import String, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, TYPE_CHECKING

from app.core.database import Base
from app.core.ids import uuid7

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task
    from app.models.workspace_member import WorkspaceMember
    from app.models.invitation import Invitation


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="owned_workspaces", foreign_keys=[owner_id])
    tasks: Mapped[List["Task"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    members: Mapped[List["WorkspaceMember"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    invites: Mapped[List["Invitation"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
