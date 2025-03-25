from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

class Notification(BaseModel):
    notificationId: str = Field(default_factory=lambda: f"notification_{uuid4().hex}")
    userId: str
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    isRead: bool = False
    createdAt: datetime = Field(default_factory=datetime.now)

class TokenRegistration(BaseModel):
    userId: str
    token: str