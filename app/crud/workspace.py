import uuid
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.schemas.workspace import WorkspaceCreate


def get_workspace_by_id(db: Session, workspace_id: uuid.UUID) -> Workspace | None:
    return db.query(Workspace).filter(Workspace.id == workspace_id).first()


def get_workspaces_by_user(
    db: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> list[Workspace]:
    return (
        db.query(Workspace)
        .outerjoin(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .filter(
            or_(
                Workspace.owner_id == user_id,
                WorkspaceMember.user_id == user_id
            )
        )
        .distinct()
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_workspace(db: Session, workspace_data: WorkspaceCreate, owner_id: uuid.UUID) -> Workspace:
    db_workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        owner_id=owner_id,
    )
    try:
        db.add(db_workspace)
        db.flush()

        owner_membership = WorkspaceMember(
            user_id=owner_id,
            workspace_id=db_workspace.id,
            role="owner",
        )
        db.add(owner_membership)
        db.commit()
        db.refresh(db_workspace)
        return db_workspace
    except Exception:
        db.rollback()
        raise


def update_workspace(db: Session, workspace: Workspace, update_data: dict) -> Workspace:
    for field, value in update_data.items():
        setattr(workspace, field, value)
    db.commit()
    db.refresh(workspace)
    return workspace


def delete_workspace(db: Session, workspace: Workspace) -> None:
    db.delete(workspace)
    db.commit()
