from datetime import datetime
from pydantic import BaseModel, Field


class NotificationOut(BaseModel):
    id: int = Field(...)
    type: str = Field(...)
    title: str = Field(...)
    message: str = Field(...)
    is_read: bool = Field(...)
    created_at: datetime = Field(...)


class MarkReadRequest(BaseModel):
    notification_ids: list[int] = Field(default_factory=list, description="IDs to mark as read; empty means all")
