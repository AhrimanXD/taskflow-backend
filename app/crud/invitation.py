from sqlalchemy.orm import Session, joinedload
from app.models.invitation import Invitation, InviteRole, Status


def get_invitation_by_id(db: Session, invite_id: int) -> Invitation | None:
    return db.get(Invitation, invite_id)

def get_workspace_invitations(db, workspace_id, status_filter: Status | None = None):
    query = (db.query(Invitation)
             .options(joinedload(Invitation.invitee), joinedload(Invitation.inviter))
             .filter(Invitation.workspace_id == workspace_id))
    if status_filter is not None:
        query = query.filter(Invitation.status == status_filter)
    return query.all()


def get_user_invitations(db: Session, user_id: int, status_filter: Status | None = None) -> list[Invitation]:
    query = (db.query(Invitation)
             .options(joinedload(Invitation.workspace), joinedload(Invitation.inviter))
             .filter(Invitation.invitee_id == user_id))
    if status_filter is not None:
        query = query.filter(Invitation.status == status_filter)
    return query.all()


def create_invitation(db: Session, inviter_id: int, workspace_id: int, invitee_id: int, role: InviteRole) -> Invitation:
    invite = Invitation(workspace_id = workspace_id, inviter_id = inviter_id, invitee_id = invitee_id, role = role)
    try:
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return invite
    except Exception:
        db.rollback()
        raise

def update_invitation_status(
        db: Session,
        invitation: Invitation,
        new_status: Status) -> Invitation:
    invitation.status = new_status
    db.commit()
    db.refresh(invitation)
    return invitation

