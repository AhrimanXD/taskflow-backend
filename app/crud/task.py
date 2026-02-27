from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def get_task_by_id(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[Task]:
    return db.query(Task).filter(Task.owner_id == owner_id).offset(skip).limit(limit).all()


def create_task(db: Session, task_data: TaskCreate, owner_id: int) -> Task:
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        owner_id=owner_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task: Task, task_data: TaskUpdate) -> Task:
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
