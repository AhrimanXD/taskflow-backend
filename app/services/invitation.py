import uuid
from fastapi import HTTPException, status
from pydantic import EmailStr
from app.crud.invitation import create_invitation, get_invitation_by_id, update_invitation_status, get_user_invitations, get_workspace_invitations
from app.models.workspace_member import RoleEnum, WorkspaceMember
from app.services.workspace import require_role_or_raise
from app.models.invitation import Invitation, InviteRole, Status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.crud.user import get_user_by_email
from app.crud.member import get_member


def create_invitation_service(db: Session,
                              workspace_id: uuid.UUID,
                              user_id: uuid.UUID,
                              invitee_email: EmailStr,
                              invitee_role: InviteRole):
    require_role_or_raise(db, workspace_id, user_id, allowed = {RoleEnum.ADMIN, RoleEnum.OWNER})
    invitee = get_user_by_email(db, invitee_email)
    if not invitee:
        raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "User not found"
                )
    if get_member(db, workspace_id, invitee.id):
        raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail="User is already a member of the workspace"
                )
    try:
        invitation = create_invitation(db, user_id, workspace_id, invitee.id, invitee_role)
        return invitation
    except IntegrityError:
        raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail = "User already has pending invite request"
                )

def assert_pending(invitation: Invitation):
    if invitation.status != Status.PENDING:
        raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail = "Cannot perform operation on an invite that is not pending"
                )


def get_invitation_or_raise(db: Session, invite_id):
    invitation = get_invitation_by_id(db, invite_id)
    if not invitation:
        raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Invite does not exist"
                )
    return invitation


def decline_invitation_service(db: Session,
                               user_id: uuid.UUID,
                               invite_id: uuid.UUID) -> Invitation:
    invitation = get_invitation_or_raise(db, invite_id)
    if invitation.invitee_id != user_id:
        raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail = "Unauthorized Access, Invitation not for user"
                )
    assert_pending(invitation)
    return update_invitation_status(db, invitation, Status.DECLINED)

def revoke_invitation_service(db: Session,
                              invite_id: uuid.UUID,
                              user_id: uuid.UUID) -> Invitation:
    invitation = get_invitation_or_raise(db, invite_id)
    require_role_or_raise(db, invitation.workspace_id, user_id, allowed={RoleEnum.ADMIN, RoleEnum.OWNER})
    assert_pending(invitation)
    return update_invitation_status(db, invitation, Status.REVOKED)


def accept_invitation_service(db: Session,
                              user_id: uuid.UUID,
                              invite_id: uuid.UUID) -> Invitation:
    invitation = get_invitation_or_raise(db, invite_id)
    if invitation.invitee_id != user_id:
        raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail = "Unauthorized Access, Invitation not for user"
                )
    assert_pending(invitation)
    try:
        invitation.status = Status.ACCEPTED
        member = WorkspaceMember(user_id = user_id, workspace_id = invitation.workspace_id, role = RoleEnum(invitation.role.value))
        db.add(member)
        db.commit()
        db.refresh(invitation)
        return invitation
    except IntegrityError:
        db.rollback()
        raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail = "User is already a member"
                )
    except Exception:
        db.rollback()
        raise

def get_workspace_invitations_service(db, workspace_id, user_id,
                                      status_filter: Status | None = None) -> list[Invitation]:
    require_role_or_raise(db, workspace_id, user_id, allowed={RoleEnum.ADMIN, RoleEnum.OWNER})
    return get_workspace_invitations(db, workspace_id, status_filter)

def get_user_invitations_service(db, user_id,
                                 status_filter: Status | None = None) -> list[Invitation]:
    return get_user_invitations(db, user_id, status_filter)
