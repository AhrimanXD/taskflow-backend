from sqlalchemy.orm import Session
from app.models import WorkspaceMember

def get_member(db: Session, workspace_id: int, user_id: int) -> WorkspaceMember | None:
    return db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
    ).first()
