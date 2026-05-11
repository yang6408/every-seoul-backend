import json
import logging
from typing import Any

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


def send_web_push(subscription: PushSubscription, payload: dict[str, Any]) -> bool:
    if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
        logger.warning("VAPID 키가 없어 Web Push 발송을 건너뜁니다.")
        return False

    try:
        webpush(
            subscription_info=subscription.subscription_json,
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=settings.VAPID_PRIVATE_KEY.replace("\\n", "\n"),
            vapid_claims={"sub": settings.VAPID_CLAIM_EMAIL},
        )
        return True
    except WebPushException as exc:
        logger.warning("Web Push 발송 실패: %s", exc)
        return False


def send_user_push(db: Session, user_id: int, payload: dict[str, Any]) -> tuple[int, int]:
    subscriptions = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active == True,
        )
        .all()
    )

    sent = 0
    failed = 0
    for subscription in subscriptions:
        if send_web_push(subscription, payload):
            sent += 1
        else:
            failed += 1

    return sent, failed
