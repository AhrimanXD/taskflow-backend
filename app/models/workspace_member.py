import uuid

from sqlalchemy import ForeignKey, UniqueConstraint, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import TYPE_CHECKING
from enum import Enum as PyEnum
from app.core.database import Base
from app.core.ids import uuid7

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class RoleEnum(str, PyEnum):
    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("user_id", "workspace_id", name="unique_user_workspace"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"))
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum, name = "member_role_enum", values_callable = lambda x: [i.value for i in x]), default=RoleEnum.MEMBER)
    joined_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="workspace_memberships")
    workspace: Mapped["Workspace"] = relationship(back_populates="members")
