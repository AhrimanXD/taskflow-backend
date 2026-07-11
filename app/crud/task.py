from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate

def get_task_by_id(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[Task]:
    return db.query(Task).filter(Task.owner_id == owner_id, Task.workspace_id.is_(None)).offset(skip).limit(limit).all()

def get_tasks_by_workspace(db, workspace_id, skip=0, limit=100) -> list[Task]:
    return (db.query(Task)
            .filter(Task.workspace_id == workspace_id)
            .offset(skip).limit(limit).all())

def create_task(db: Session, task_data: TaskCreate, owner_id: int, workspace_id: int | None = None) -> Task:
    db_task = Task(
        **task_data.model_dump(),
        owner_id = owner_id,
        workspace_id = workspace_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task: Task, task_data: TaskUpdate) -> Task:
    update_data = task_data.model_dump(exclude_unset=True)
    # `version` is a control field, not task data — SQLAlchemy's version_id_col
    # owns the column and bumps it on flush. Never setattr it ourselves.
    update_data.pop("version", None)
    for field, value in update_data.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
