import logging

from fastapi import APIRouter, BackgroundTasks

from app.schemas.newsletter import PipelineTriggerResponse
from app.services.logic import process_daily_newsletters

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/pipeline/trigger", response_model=PipelineTriggerResponse)
async def trigger_pipeline(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_daily_newsletters)
    logger.info("관리자 요청: 뉴스레터 파이프라인 수동 실행 시작")
    return PipelineTriggerResponse(
        status="accepted",
        message="파이프라인이 백그라운드에서 실행됩니다.",
    )
