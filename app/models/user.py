import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, TYPE_CHECKING

from app.core.database import Base
from app.core.ids import uuid7

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.workspace_member import WorkspaceMember
    from app.models.task import Task
    from app.models.invitation import Invitation


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    owned_workspaces: Mapped[List["Workspace"]] = relationship(
        back_populates="owner",
        foreign_keys="Workspace.owner_id"
    )
    owned_tasks: Mapped[List["Task"]] = relationship(
        back_populates="owner",
        foreign_keys="Task.owner_id"
    )
    assigned_tasks: Mapped[List["Task"]] = relationship(
        back_populates="assignee",
        foreign_keys="Task.assignee_id"
    )
    workspace_memberships: Mapped[List["WorkspaceMember"]] = relationship(back_populates="user")
    invites_sent: Mapped[List["Invitation"]] = relationship(
        back_populates = "inviter",
        foreign_keys="Invitation.inviter_id"
    )
    invites_received: Mapped[List["Invitation"]] = relationship(back_populates = "invitee", foreign_keys="Invitation.invitee_id")
