from uuid import UUID
from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUser, SessionDep
from app.models.invitation import Status as InviteStatus
from app.schemas.invitation import (
    InvitationCreate,
    InvitationForWorkspace,
    InvitationReceived,
)
from app.services.invitation import (
    accept_invitation_service,
    create_invitation_service,
    decline_invitation_service,
    get_user_invitations_service,
    get_workspace_invitations_service,
    revoke_invitation_service,
)

router = APIRouter(tags=["invitations"])


# --- Workspace-scoped (owner/admin) ---

@router.post(
    "/workspaces/{workspace_id}/invitations",
    response_model=InvitationForWorkspace,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    workspace_id: UUID,
    payload: InvitationCreate,
    db: SessionDep,
    current_user: CurrentUser,
):
    return create_invitation_service(
        db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        invitee_email=payload.invitee_email,
        invitee_role=payload.role,
    )


@router.get(
    "/workspaces/{workspace_id}/invitations",
    response_model=list[InvitationForWorkspace],
)
async def list_workspace_invitations(
    workspace_id: UUID,
    db: SessionDep,
    current_user: CurrentUser,
    status_filter: InviteStatus | None = Query(default=None, alias="status"),
):
    return get_workspace_invitations_service(
        db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        status_filter=status_filter,
    )


@router.post(
    "/invitations/{invite_id}/revoke",
    response_model=InvitationForWorkspace,
)
async def revoke_invitation(
    invite_id: UUID,
    db: SessionDep,
    current_user: CurrentUser,
):
    return revoke_invitation_service(db, invite_id=invite_id, user_id=current_user.id)


# --- Invitee-scoped (the current user's own invitations) ---

@router.get("/invitations", response_model=list[InvitationReceived])
async def list_my_invitations(
    db: SessionDep,
    current_user: CurrentUser,
    status_filter: InviteStatus | None = Query(default=None, alias="status"),
):
    return get_user_invitations_service(
        db, user_id=current_user.id, status_filter=status_filter
    )


@router.post("/invitations/{invite_id}/accept", response_model=InvitationReceived)
async def accept_invitation(
    invite_id: UUID,
    db: SessionDep,
    current_user: CurrentUser,
):
    return accept_invitation_service(db, user_id=current_user.id, invite_id=invite_id)


@router.post("/invitations/{invite_id}/decline", response_model=InvitationReceived)
async def decline_invitation(
    invite_id: UUID,
    db: SessionDep,
    current_user: CurrentUser,
):
    return decline_invitation_service(db, user_id=current_user.id, invite_id=invite_id)
