import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.db.models.newsletter import Newsletter, UserNewsletterMatch
from app.db.models.user import User
from app.db.session import ensure_user_profile_columns
from app.schemas.newsletter import FeedItem, FeedRefreshResponse, UserFeedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import ai_service

logger = logging.getLogger(__name__)

router = APIRouter()

_KST = ZoneInfo("Asia/Seoul")
_REFRESH_LOOKBACK_DAYS = 7
_MAX_MATCH_BATCH = 50


def _get_active_user_or_404(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    ensure_user_profile_columns()
    user = User(
        email=body.email,
        age=body.age,
        districts=body.districts,
        has_children=body.has_children,
        children_count=body.children_count,
        employment_status=body.employment_status,
        interests=body.interests,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return _get_active_user_or_404(user_id, db)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db)):
    ensure_user_profile_columns()
    user = _get_active_user_or_404(user_id, db)
    updated_fields = body.model_fields_set

    if "age" in updated_fields:
        user.age = body.age
    if "districts" in updated_fields:
        user.districts = body.districts
    if "has_children" in updated_fields:
        user.has_children = body.has_children
        if not body.has_children:
            user.children_count = None
    if "children_count" in updated_fields:
        user.children_count = body.children_count
    if "employment_status" in updated_fields:
        user.employment_status = body.employment_status
    if "interests" in updated_fields:
        user.interests = body.interests
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = _get_active_user_or_404(user_id, db)
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()


@router.get("/{user_id}/feed", response_model=UserFeedResponse)
def get_user_feed(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, description="읽지 않은 항목만 조회"),
    db: Session = Depends(get_db),
):
    _get_active_user_or_404(user_id, db)

    query = (
        db.query(UserNewsletterMatch)
        .options(joinedload(UserNewsletterMatch.newsletter))
        .filter(UserNewsletterMatch.user_id == user_id)
        .order_by(UserNewsletterMatch.match_score.desc())
    )
    if unread_only:
        query = query.filter(UserNewsletterMatch.is_read == False)

    total = query.count()
    matches = query.offset(skip).limit(limit).all()

    items = [
        FeedItem(
            newsletter=match.newsletter,
            match_score=match.match_score,
            is_read=match.is_read,
        )
        for match in matches
    ]
    return UserFeedResponse(total=total, items=items)


@router.patch(
    "/{user_id}/feed/{newsletter_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
)
def mark_as_read(user_id: int, newsletter_id: int, db: Session = Depends(get_db)):
    _get_active_user_or_404(user_id, db)
    match = (
        db.query(UserNewsletterMatch)
        .filter(
            UserNewsletterMatch.user_id == user_id,
            UserNewsletterMatch.newsletter_id == newsletter_id,
        )
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="해당 뉴스레터 매칭 정보가 없습니다.")
    match.is_read = True
    db.commit()


@router.post("/{user_id}/feed/refresh", response_model=FeedRefreshResponse)
async def refresh_feed(user_id: int, db: Session = Depends(get_db)):
    user = _get_active_user_or_404(user_id, db)

    existing_ids = {
        row.newsletter_id
        for row in db.query(UserNewsletterMatch.newsletter_id)
        .filter(UserNewsletterMatch.user_id == user_id)
        .all()
    }

    lookback = datetime.now(_KST) - timedelta(days=_REFRESH_LOOKBACK_DAYS)
    unmatched_query = (
        db.query(Newsletter)
        .filter(
            Newsletter.id.notin_(existing_ids),
            Newsletter.publish_date >= lookback,
        )
        .order_by(Newsletter.publish_date.desc())
    )

    if user.districts:
        unmatched_query = unmatched_query.filter(
            Newsletter.ai_briefing["district"].astext.in_(user.districts)
        )

    unmatched = unmatched_query.limit(_MAX_MATCH_BATCH).all()

    if not unmatched:
        return FeedRefreshResponse(matched=0, message="새로 매칭할 뉴스레터가 없습니다.")

    async def _score(newsletter: Newsletter) -> tuple[int, int]:
        score = await ai_service.score_user_match(
            user_interests=user.interests or [],
            newsletter_tags=newsletter.tags or [],
        )
        return newsletter.id, score

    scores = await asyncio.gather(*[_score(n) for n in unmatched])

    try:
        for newsletter_id, score in scores:
            db.add(
                UserNewsletterMatch(
                    user_id=user_id,
                    newsletter_id=newsletter_id,
                    match_score=score,
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="매칭 점수 저장 중 오류가 발생했습니다.")

    return FeedRefreshResponse(
        matched=len(scores),
        message=f"{len(scores)}개 뉴스레터의 매칭 점수를 계산했습니다.",
    )
