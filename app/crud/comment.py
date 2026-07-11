from sqlalchemy.orm import Session, selectinload

from app.models.comment import Comment
from app.schemas.comment import CommentCreate


def get_comment_by_id(db: Session, comment_id: int) -> Comment | None:
    return db.query(Comment).filter(Comment.id == comment_id).first()


def get_comments_by_task(db: Session, task_id: int) -> list[Comment]:
    return (
        db.query(Comment)
        .filter(Comment.task_id == task_id)
        .options(selectinload(Comment.author))
        .order_by(Comment.created_at.asc())
        .all()
    )


def create_comment(
    db: Session, task_id: int, author_id: int, data: CommentCreate
) -> Comment:
    comment = Comment(task_id=task_id, author_id=author_id, body=data.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment: Comment) -> None:
    db.delete(comment)
    db.commit()
