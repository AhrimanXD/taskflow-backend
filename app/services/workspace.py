from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud.workspace import get_workspace_by_id
from app.crud.member import (
    get_member,
    get_workspace_members,
    remove_member,
    update_member_role,
)
from app.models.workspace import Workspace
from app.models.workspace_member import RoleEnum, WorkspaceMember


def get_workspace_or_raise(
    db: Session,
    workspace_id: int,
    user_id: int,
    require_owner: bool = False,
) -> Workspace:
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    if require_owner:
        if workspace.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this workspace",
            )
    else:
        is_member = any(m.user_id == user_id for m in workspace.members)
        if workspace.owner_id != user_id and not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this workspace",
            )

    return workspace


def get_member_role_or_raise(
    db: Session,
    workspace_id: int,
    user_id: int,
) -> RoleEnum:
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    member = get_member(db, workspace_id, user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this workspace",
        )
    return member.role


def require_role_or_raise(
    db: Session, workspace_id: int, user_id: int, allowed: set[RoleEnum]
) -> RoleEnum:
    role = get_member_role_or_raise(db, workspace_id, user_id)
    if role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to perform this action",
        )
    return role


def get_workspace_members_service(
    db: Session, workspace_id: int, user_id: int
) -> list[WorkspaceMember]:
    get_member_role_or_raise(db, workspace_id, user_id)
    return get_workspace_members(db, workspace_id)


def _member_or_404(db: Session, workspace_id: int, user_id: int) -> WorkspaceMember:
    member = get_member(db, workspace_id, user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )
    return member


def leave_workspace_service(db: Session, workspace_id: int, user_id: int) -> None:
    """A member removes themselves. The owner can't leave (they'd orphan the
    workspace) — they must delete it or transfer ownership instead -> 409."""
    role = get_member_role_or_raise(db, workspace_id, user_id)
    if role == RoleEnum.OWNER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The owner can't leave. Delete the workspace or transfer ownership first.",
        )
    remove_member(db, _member_or_404(db, workspace_id, user_id))


def remove_member_service(
    db: Session, workspace_id: int, actor_id: int, target_user_id: int
) -> None:
    """Kick a member. Owner/admin only. The owner is never removable; an admin
    may only remove plain members (not the owner or other admins). Removing
    yourself goes through 'leave', not here."""
    actor_role = require_role_or_raise(
        db, workspace_id, actor_id, allowed={RoleEnum.OWNER, RoleEnum.ADMIN}
    )
    if target_user_id == actor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use 'leave workspace' to remove yourself",
        )
    target = _member_or_404(db, workspace_id, target_user_id)
    if target.role == RoleEnum.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The workspace owner can't be removed",
        )
    if actor_role == RoleEnum.ADMIN and target.role == RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can't remove other admins",
        )
    remove_member(db, target)


def update_member_role_service(
    db: Session,
    workspace_id: int,
    actor_id: int,
    target_user_id: int,
    new_role: RoleEnum,
) -> WorkspaceMember:
    """Promote/demote a member between admin and member. Owner only. The owner's
    role can't be changed, and no one can be set to owner via this route."""
    require_role_or_raise(db, workspace_id, actor_id, allowed={RoleEnum.OWNER})
    if new_role == RoleEnum.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can't assign the owner role here",
        )
    target = _member_or_404(db, workspace_id, target_user_id)
    if target.role == RoleEnum.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The owner's role can't be changed",
        )
    return update_member_role(db, target, new_role)
