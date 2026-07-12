import uuid
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Enum, Index, text, Uuid
from datetime import datetime, timezone
from app.core.database import Base
from app.core.ids import uuid7
from enum import Enum as PyEnum

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class Status(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REVOKED = "revoked"

class InviteRole(str, PyEnum):
    ADMIN = 'admin'
    MEMBER = 'member'


class Invitation(Base):
    __tablename__ = "invitations"

    __table_args__ = (
            Index("unique_pending_invite", "workspace_id", "invitee_id", unique=True, postgresql_where = text("status = 'pending'")),
            )
    
    id : Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    workspace_id : Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"))
    inviter_id : Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    invitee_id : Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    role : Mapped[InviteRole] = mapped_column(Enum(InviteRole, name = "invite_role_enum", values_callable = lambda x: [i.value for i in x]), default = InviteRole.MEMBER)
    status : Mapped[Status] = mapped_column(Enum(Status, name = "invite_status_enum", values_callable = lambda x: [i.value for i in x]), default=Status.PENDING)
    created_at : Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    workspace : Mapped['Workspace'] = relationship(back_populates='invites')
    inviter: Mapped['User'] = relationship(back_populates='invites_sent', foreign_keys=[inviter_id])
    invitee: Mapped['User'] = relationship(back_populates='invites_received', foreign_keys=[invitee_id])
