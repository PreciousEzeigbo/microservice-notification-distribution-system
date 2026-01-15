from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, HttpUrl


class NotificationType(str, Enum):
    email = "email"
    push = "push"


class UserData(BaseModel):
    name: str
    link: HttpUrl
    meta: Optional[Dict[str, Any]] = None


class NotificationRequest(BaseModel):
    notification_type: NotificationType
    user_id: str
    template_code: str
    variables: UserData
    request_id: str
    priority: int = Field(default=1)
    metadata: Optional[Dict[str, Any]] = None
