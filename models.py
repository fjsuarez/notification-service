from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any

class Notification(BaseModel):
    notificationId: str = Field(..., alias="notification_id")
    userId: str = Field(..., alias="user_id")
    type: str
    data: Dict[str, Any]
    isRead: bool = Field(..., alias="is_read")
    createdAt: datetime = Field(..., alias="created_at")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }