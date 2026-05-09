import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.logic import process_daily_newsletters

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


async def _run_pipeline() -> None:
    logger.info("스케줄러: 일일 뉴스레터 파이프라인 트리거")
    try:
        await process_daily_newsletters()
    except Exception as e:
        logger.error(f"스케줄러 파이프라인 실패: {e}")


def start_scheduler() -> None:
    scheduler.add_job(
        _run_pipeline,
        trigger=CronTrigger(hour=4, minute=0),
        id="daily_newsletter",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    logger.info("APScheduler 시작 — 매일 04:00 KST 뉴스레터 파이프라인 예약됨")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler 종료")
