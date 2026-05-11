from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.db.models.push_subscription import PushSubscription
from app.db.models.user import User
from app.schemas.notification import (
    PushPublicKeyResponse,
    PushSendResponse,
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    PushTestRequest,
)
from app.services.push_service import send_user_push

router = APIRouter()


@router.get("/push/public-key", response_model=PushPublicKeyResponse)
def get_push_public_key():
    return PushPublicKeyResponse(public_key=settings.VAPID_PUBLIC_KEY)


@router.post(
    "/push/subscriptions",
    response_model=PushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def upsert_push_subscription(
    body: PushSubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_agent: str | None = Header(default=None),
):
    raw = body.raw or {
        "endpoint": body.endpoint,
        "expirationTime": body.expiration_time,
        "keys": body.keys.model_dump(),
    }
    subscription = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == body.endpoint)
        .first()
    )

    if subscription:
        subscription.user_id = current_user.id
        subscription.p256dh = body.keys.p256dh
        subscription.auth = body.keys.auth
        subscription.user_agent = user_agent
        subscription.subscription_json = raw
        subscription.is_active = True
        subscription.updated_at = datetime.utcnow()
    else:
        subscription = PushSubscription(
            user_id=current_user.id,
            endpoint=body.endpoint,
            p256dh=body.keys.p256dh,
            auth=body.keys.auth,
            user_agent=user_agent,
            subscription_json=raw,
            is_active=True,
        )
        db.add(subscription)

    db.commit()
    db.refresh(subscription)
    return subscription


@router.delete("/push/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def delete_push_subscription(
    endpoint: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subscription = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.user_id == current_user.id,
            PushSubscription.endpoint == endpoint,
        )
        .first()
    )
    if subscription:
        subscription.is_active = False
        subscription.updated_at = datetime.utcnow()
        db.commit()


@router.post("/push/test", response_model=PushSendResponse)
def send_test_push(
    body: PushTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Web Push VAPID 키가 설정되지 않았습니다.",
        )

    sent, failed = send_user_push(
        db,
        current_user.id,
        {
            "title": body.title,
            "body": body.body,
            "url": body.url,
        },
    )
    return PushSendResponse(sent=sent, failed=failed)
