from pydantic import BaseModel
from typing import Optional


class PushTokenRegister(BaseModel):
    token: str
    platform: Optional[str] = None  # 'ios' | 'android'


class NotificationPreferencesUpdate(BaseModel):
    notifications_enabled: Optional[bool] = None
    deadline_reminders_enabled: Optional[bool] = None
    result_notifications_enabled: Optional[bool] = None


class NotificationPreferencesResponse(BaseModel):
    notifications_enabled: bool
    deadline_reminders_enabled: bool
    result_notifications_enabled: bool

    class Config:
        from_attributes = True
