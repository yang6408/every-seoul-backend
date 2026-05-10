import logging
import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status

from app.core.config import settings
from app.schemas.newsletter import PipelineTriggerResponse
from app.services.logic import process_daily_newsletters

logger = logging.getLogger(__name__)

router = APIRouter()


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    if not settings.ADMIN_API_KEY:
        if settings.ENVIRONMENT.lower() == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="관리자 API 키가 설정되지 않았습니다.",
            )
        return

    if not x_admin_token or not secrets.compare_digest(
        x_admin_token, settings.ADMIN_API_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="관리자 인증에 실패했습니다.",
        )


@router.post("/pipeline/trigger", response_model=PipelineTriggerResponse)
async def trigger_pipeline(
    background_tasks: BackgroundTasks,
    _: None = Depends(require_admin_token),
):
    background_tasks.add_task(process_daily_newsletters)
    logger.info("관리자 요청: 뉴스레터 파이프라인 수동 실행 시작")
    return PipelineTriggerResponse(
        status="accepted",
        message="파이프라인이 백그라운드에서 실행됩니다.",
    )
