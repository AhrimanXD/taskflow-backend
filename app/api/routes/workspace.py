from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, SessionDep
from app.crud.workspace import (
    create_workspace,
    delete_workspace,
    get_workspaces_by_user,
    update_workspace,
)
from app.crud.activity import get_workspace_activity
from app.crud.user import get_user_by_id
from app.schemas.activity import ActivityResponse
from app.services.activity import record_and_broadcast
from app.services.notification import notify
from app.schemas.workspace import (
    MemberRoleUpdate,
    WorkspaceCreate,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace import (
    get_member_role_or_raise,
    get_workspace_members_service,
    get_workspace_or_raise,
    leave_workspace_service,
    remove_member_service,
    update_member_role_service,
)

router = APIRouter()


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    return get_workspaces_by_user(db, user_id=current_user.id, skip=skip, limit=limit)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_new_workspace(
    workspace_data: WorkspaceCreate,
    db: SessionDep,
    current_user: CurrentUser,
):
    return create_workspace(db, workspace_data, owner_id=current_user.id)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    return get_workspace_or_raise(db, workspace_id, user_id=current_user.id)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_existing_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    db: SessionDep,
    current_user: CurrentUser,
):
    workspace = get_workspace_or_raise(
        db, workspace_id, user_id=current_user.id, require_owner=True
    )
    return update_workspace(
        db, workspace, workspace_data.model_dump(exclude_unset=True)
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_workspace(
    workspace_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    workspace = get_workspace_or_raise(
        db, workspace_id, user_id=current_user.id, require_owner=True
    )
    delete_workspace(db, workspace)
    return None


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: int, db: SessionDep, current_user: CurrentUser
):
    return get_workspace_members_service(db, workspace_id, current_user.id)


# NOTE: `/members/me` is declared before `/members/{user_id}` so it isn't
# swallowed by the int path param.
@router.delete("/{workspace_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
async def leave_workspace(
    workspace_id: int, db: SessionDep, current_user: CurrentUser
):
    """Leave a workspace. The owner can't leave (409)."""
    leave_workspace_service(db, workspace_id, current_user.id)
    await record_and_broadcast(
        db,
        workspace_id=workspace_id,
        actor_id=current_user.id,
        action="member.left",
        object_type="member",
        object_id=current_user.id,
        summary="left the workspace",
    )
    return None


@router.delete(
    "/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_workspace_member(
    workspace_id: int, user_id: int, db: SessionDep, current_user: CurrentUser
):
    """Remove (kick) a member. Owner/admin only; owner is protected and admins
    can't remove other admins."""
    target = get_user_by_id(db, user_id)
    remove_member_service(db, workspace_id, current_user.id, user_id)
    await record_and_broadcast(
        db,
        workspace_id=workspace_id,
        actor_id=current_user.id,
        action="member.removed",
        object_type="member",
        object_id=user_id,
        summary=f"removed {target.username if target else 'a member'}",
    )
    await notify(
        db,
        recipient_id=user_id,
        actor_id=current_user.id,
        type="member.removed",
        message=f"{current_user.username} removed you from a workspace",
        workspace_id=None,
    )
    return None


@router.patch(
    "/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse
)
async def change_member_role(
    workspace_id: int,
    user_id: int,
    body: MemberRoleUpdate,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Promote/demote a member between admin and member. Owner only."""
    member = update_member_role_service(
        db, workspace_id, current_user.id, user_id, body.role
    )
    await record_and_broadcast(
        db,
        workspace_id=workspace_id,
        actor_id=current_user.id,
        action="member.role_changed",
        object_type="member",
        object_id=user_id,
        summary=f"changed {member.user.username}'s role to {body.role.value}",
    )
    await notify(
        db,
        recipient_id=user_id,
        actor_id=current_user.id,
        type="member.role_changed",
        message=f"{current_user.username} changed your role to {body.role.value}",
        workspace_id=workspace_id,
    )
    return member


@router.get("/{workspace_id}/activity", response_model=list[ActivityResponse])
async def list_workspace_activity(
    workspace_id: int,
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
):
    """Recent activity in a workspace (newest first). Any member."""
    get_member_role_or_raise(db, workspace_id, current_user.id)
    return get_workspace_activity(db, workspace_id, skip=skip, limit=limit)
