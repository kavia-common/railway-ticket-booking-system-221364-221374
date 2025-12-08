from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.db.models import Notification
from src.db.session import get_db
from src.schemas.notification import MarkReadRequest, NotificationOut
from src.schemas.common import Message
from src.db.models import User
from src.services.notifications import list_notifications, mark_notifications_read

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", summary="List notifications", response_model=List[NotificationOut])
def get_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> List[NotificationOut]:
    """Return notifications for current user."""
    notifs: list[Notification] = list_notifications(db, user.id)
    return [
        NotificationOut(
            id=n.id, type=n.type.value, title=n.title, message=n.message, is_read=n.is_read, created_at=n.created_at
        )
        for n in notifs
    ]


@router.post("/mark-read", summary="Mark notifications as read", response_model=Message)
def mark_read(payload: MarkReadRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Message:
    """Mark notifications as read; if list is empty, mark all."""
    count = mark_notifications_read(db, user.id, payload.notification_ids or None)
    return Message(message=f"Marked {count} notification(s) as read")
