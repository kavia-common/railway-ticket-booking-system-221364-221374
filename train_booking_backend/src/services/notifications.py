from typing import List

from sqlalchemy.orm import Session

from src.db.models import Notification, NotificationType


# PUBLIC_INTERFACE
def create_notification(db: Session, user_id: int, title: str, message: str, type_: NotificationType = NotificationType.info) -> Notification:
    """Create a new notification for a user."""
    notif = Notification(user_id=user_id, title=title, message=message, type=type_)
    db.add(notif)
    db.flush()
    return notif


# PUBLIC_INTERFACE
def list_notifications(db: Session, user_id: int) -> List[Notification]:
    """List notifications for a specific user."""
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()


# PUBLIC_INTERFACE
def mark_notifications_read(db: Session, user_id: int, ids: list[int] | None = None) -> int:
    """Mark notifications as read. If ids is None or empty, mark all."""
    q = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read.is_(False))
    if ids:
        q = q.filter(Notification.id.in_(ids))
    count = 0
    for n in q.all():
        n.is_read = True
        count += 1
    db.flush()
    return count
