from fastapi import HTTPException, status
from pydantic import EmailStr
from app.crud.invitation import create_invitation
from app.models.workspace_member import RoleEnum
from app.services.workspace import require_role_or_raise
from app.models.invitation import InviteRole
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.crud.user import get_user_by_email
from app.crud.member import get_member


def create_invitation_service(db: Session,
                              workspace_id: int,
                              user_id: int,
                              invitee_email: EmailStr,
                              invitee_role: InviteRole):
    require_role_or_raise(db, workspace_id, user_id, allowed = {RoleEnum.ADMIN, RoleEnum.OWNER})
    invitee = get_user_by_email(db, invitee_email)
    if not invitee:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail = "User not found"
                )
    if get_member(db, workspace_id, invitee.id):
        raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of the workspace"
                )
    try:
        invitation = create_invitation(db, user_id, workspace_id, invitee.id, invitee_role)
        return invitation
    except IntegrityError:
        raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail = "User already has pending invite request"
                )

    

