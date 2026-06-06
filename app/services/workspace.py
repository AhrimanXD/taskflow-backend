from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud.workspace import get_workspace_by_id
from app.crud.member import get_member
from app.models.workspace import Workspace
from app.models.workspace_member import RoleEnum


def get_workspace_or_raise(
    db: Session,
    workspace_id: int,
    user_id: int,
    require_owner: bool = False,
) -> Workspace:
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    if require_owner:
        if workspace.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this workspace")
    else:
        is_member = any(m.user_id == user_id for m in workspace.members)
        if workspace.owner_id != user_id and not is_member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this workspace")

    return workspace

def get_member_role_or_raise(db: Session,
    workspace_id: int,
    user_id: int,
) -> RoleEnum:
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    member = get_member(db, workspace_id, user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this workspace")
    return member.role

def require_role_or_raise(db: Session,
    workspace_id: int,
    user_id: int,
    allowed: set[RoleEnum]
) -> RoleEnum:
    role = get_member_role_or_raise(db, workspace_id, user_id)
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have permission to perform this action")
    return role
