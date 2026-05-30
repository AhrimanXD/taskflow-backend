from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud.workspace import get_workspace_by_id
from app.models.workspace import Workspace


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
