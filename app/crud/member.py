from sqlalchemy.orm import Session, selectinload
from app.models import WorkspaceMember


def get_member(db: Session, workspace_id: int, user_id: int) -> WorkspaceMember | None:
    return (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )


def get_workspace_members(db: Session, workspace_id: int) -> list[WorkspaceMember]:
    return (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .options(selectinload(WorkspaceMember.user))
    ).all()


def remove_member(db: Session, member: WorkspaceMember) -> None:
    db.delete(member)
    db.commit()


def update_member_role(db: Session, member: WorkspaceMember, role) -> WorkspaceMember:
    member.role = role
    db.commit()
    db.refresh(member)
    return member
