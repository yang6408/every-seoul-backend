from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    expiration_time: float | None = None
    keys: PushKeys
    raw: dict[str, Any] = Field(default_factory=dict)


class PushSubscriptionResponse(BaseModel):
    id: int
    endpoint: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PushPublicKeyResponse(BaseModel):
    public_key: str | None


class PushTestRequest(BaseModel):
    title: str = "Every Seoul 알림 테스트"
    body: str = "브라우저 푸시 알림이 정상적으로 연결되었습니다."
    url: str = "/"


class PushSendResponse(BaseModel):
    sent: int
    failed: int
