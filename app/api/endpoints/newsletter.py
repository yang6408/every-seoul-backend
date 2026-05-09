import logging
from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.newsletter import Newsletter
from app.schemas.newsletter import NewsletterDetail, NewsletterListResponse, NewsletterSummary

logger = logging.getLogger(__name__)

router = APIRouter()

_KST = ZoneInfo("Asia/Seoul")


def _to_summary(n: Newsletter) -> NewsletterSummary:
    briefing = n.ai_briefing or {}
    return NewsletterSummary(
        id=n.id,
        title=n.title,
        publish_date=n.publish_date,
        tags=n.tags or [],
        district=briefing.get("district"),
        summary=briefing.get("summary"),
    )


def _day_range(d: date) -> tuple[datetime, datetime]:
    start = datetime(d.year, d.month, d.day)
    end = start + timedelta(days=1)
    return start, end


@router.get("/", response_model=NewsletterListResponse)
def list_newsletters(
    district: Optional[str] = Query(None, description="자치구 이름 (예: 강남구)"),
    target_date: Optional[date] = Query(None, alias="date", description="조회 날짜 (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Newsletter)

    if district:
        query = query.filter(Newsletter.ai_briefing["district"].astext == district)

    if target_date:
        start, end = _day_range(target_date)
        query = query.filter(Newsletter.publish_date >= start, Newsletter.publish_date < end)

    query = query.order_by(Newsletter.publish_date.desc())

    total = query.count()
    newsletters = query.offset(skip).limit(limit).all()

    return NewsletterListResponse(total=total, items=[_to_summary(n) for n in newsletters])


@router.get("/today", response_model=NewsletterListResponse)
def list_today_newsletters(
    district: Optional[str] = Query(None, description="자치구 이름 (예: 강남구)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    today = datetime.now(_KST).date()
    start, end = _day_range(today)

    query = db.query(Newsletter).filter(
        Newsletter.publish_date >= start,
        Newsletter.publish_date < end,
    )

    if district:
        query = query.filter(Newsletter.ai_briefing["district"].astext == district)

    query = query.order_by(Newsletter.publish_date.desc())

    total = query.count()
    newsletters = query.offset(skip).limit(limit).all()

    return NewsletterListResponse(total=total, items=[_to_summary(n) for n in newsletters])


@router.get("/{newsletter_id}", response_model=NewsletterDetail)
def get_newsletter(newsletter_id: int, db: Session = Depends(get_db)):
    newsletter = db.query(Newsletter).filter(Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="뉴스레터를 찾을 수 없습니다.")
    return newsletter
