from datetime import datetime

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.models.activity import Activity
from app.models.task import Task
from app.models.workspace_member import WorkspaceMember

_STATUSES = ["pending", "ongoing", "completed"]
_PRIORITIES = ["low", "medium", "high"]


def get_overview(db: Session, user_id: int) -> dict:
    """Personal overview for the home dashboard. 'My tasks' = tasks I own
    (personal) or am assigned (in any workspace)."""
    mine = or_(Task.owner_id == user_id, Task.assignee_id == user_id)

    status_counts = dict(
        db.query(Task.status, func.count()).filter(mine).group_by(Task.status).all()
    )
    priority_counts = dict(
        db.query(Task.priority, func.count()).filter(mine).group_by(Task.priority).all()
    )
    total = sum(status_counts.values())

    assigned_to_me = (
        db.query(func.count()).select_from(Task).filter(Task.assignee_id == user_id).scalar()
    )
    overdue = (
        db.query(func.count())
        .select_from(Task)
        .filter(
            mine,
            Task.due_date.isnot(None),
            Task.due_date < datetime.utcnow(),
            Task.status != "completed",
        )
        .scalar()
    )

    ws_ids = [
        wid
        for (wid,) in db.query(WorkspaceMember.workspace_id)
        .filter(WorkspaceMember.user_id == user_id)
        .all()
    ]
    recent = []
    if ws_ids:
        recent = (
            db.query(Activity)
            .filter(Activity.workspace_id.in_(ws_ids))
            .options(selectinload(Activity.actor))
            .order_by(Activity.created_at.desc(), Activity.id.desc())
            .limit(8)
            .all()
        )

    return {
        "total": total,
        "by_status": {s: status_counts.get(s, 0) for s in _STATUSES},
        "by_priority": {p: priority_counts.get(p, 0) for p in _PRIORITIES},
        "overdue": overdue or 0,
        "assigned_to_me": assigned_to_me or 0,
        "workspace_count": len(ws_ids),
        "recent_activity": recent,
    }
