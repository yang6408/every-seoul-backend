import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.db.models.bookmark import UserBookmark
from app.db.models.newsletter import Newsletter, UserNewsletterMatch
from app.db.models.user import User
from app.db.session import ensure_user_profile_columns
from app.schemas.bookmark import BookmarkCreate, BookmarkListResponse, BookmarkResponse
from app.schemas.newsletter import FeedItem, FeedRefreshResponse, UserFeedResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services import ai_service
from app.services.push_service import send_user_push

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


def _require_same_user(user_id: int, current_user: User) -> None:
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="다른 사용자의 정보에 접근할 수 없습니다.")


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
    return _get_active_user_or_404(user_id, db)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
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
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
    user = _get_active_user_or_404(user_id, db)
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()


@router.get("/{user_id}/bookmarks", response_model=BookmarkListResponse)
def list_bookmarks(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
    _get_active_user_or_404(user_id, db)
    bookmarks = (
        db.query(UserBookmark)
        .filter(UserBookmark.user_id == user_id)
        .order_by(UserBookmark.created_at.desc())
        .all()
    )
    return BookmarkListResponse(items=[_to_bookmark_response(item) for item in bookmarks])


@router.post("/{user_id}/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
def add_bookmark(
    user_id: int,
    body: BookmarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
    _get_active_user_or_404(user_id, db)
    existing = (
        db.query(UserBookmark)
        .filter(
            UserBookmark.user_id == user_id,
            UserBookmark.item_type == body.item_type,
            UserBookmark.item_id == body.item_id,
        )
        .first()
    )
    if existing:
        return _to_bookmark_response(existing)

    bookmark = UserBookmark(user_id=user_id, item_type=body.item_type, item_id=body.item_id)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return _to_bookmark_response(bookmark)


@router.delete(
    "/{user_id}/bookmarks/{item_type}/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_bookmark(
    user_id: int,
    item_type: str,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
    _get_active_user_or_404(user_id, db)
    bookmark = (
        db.query(UserBookmark)
        .filter(
            UserBookmark.user_id == user_id,
            UserBookmark.item_type == item_type,
            UserBookmark.item_id == item_id,
        )
        .first()
    )
    if bookmark:
        db.delete(bookmark)
        db.commit()


def _to_bookmark_response(bookmark: UserBookmark) -> BookmarkResponse:
    return BookmarkResponse(
        id=bookmark.id,
        user_id=bookmark.user_id,
        item_type=bookmark.item_type,
        item_id=bookmark.item_id,
        created_at=bookmark.created_at,
    )


@router.get("/{user_id}/feed", response_model=UserFeedResponse)
def get_user_feed(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, description="읽지 않은 항목만 조회"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
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
def mark_as_read(
    user_id: int,
    newsletter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
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
async def refresh_feed(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
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

    send_user_push(
        db,
        user_id,
        {
            "title": "새 맞춤 브리핑이 도착했습니다",
            "body": f"{len(scores)}개 뉴스레터의 맞춤 점수를 계산했습니다.",
            "url": "/",
        },
    )

    return FeedRefreshResponse(
        matched=len(scores),
        message=f"{len(scores)}개 뉴스레터의 매칭 점수를 계산했습니다.",
    )
