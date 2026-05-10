import zlib

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.newsletter import Newsletter
from app.schemas.policy import EventDetail, PolicyListResponse, PolicyResponse
from app.tasks.collectors.seoul_rss import collect_all_seoul_rss

router = APIRouter()


@router.get("/", response_model=PolicyListResponse)
async def list_policies(
    age: int | None = Query(None, ge=0, le=130),
    has_children: bool = Query(False),
    employment_status: str = Query(""),
    interests: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    source = _policies_from_newsletters(db)
    events = _events_from_newsletters(db)
    if not source:
        rss_items = await collect_all_seoul_rss()
        source = _policies_from_rss(rss_items)
        events = events or _events_from_rss(rss_items)
    policies = [_with_relevance(policy, age, has_children, employment_status, interests) for policy in source]
    policies.sort(key=lambda item: item.relevance, reverse=True)
    return PolicyListResponse(items=policies, events=events)


def _policies_from_newsletters(db: Session) -> list[PolicyResponse]:
    newsletters = db.query(Newsletter).order_by(Newsletter.publish_date.desc()).limit(50).all()
    policies: list[PolicyResponse] = []
    keywords = ("정책", "지원", "모집", "신청", "수당", "대출", "복지", "청년")
    for newsletter in newsletters:
        briefing = newsletter.ai_briefing or {}
        for section in briefing.get("sections", []):
            for index, highlight in enumerate(section.get("highlights", [])):
                title = str(highlight.get("title") or "").strip()
                summary = str(highlight.get("summary") or "").strip()
                if not title or not any(keyword in f"{title} {summary}" for keyword in keywords):
                    continue
                policies.append(
                    PolicyResponse(
                        id=newsletter.id * 100 + index,
                        title=title,
                        description=summary or "서울시 및 자치구 공지에서 확인된 정책 안내입니다.",
                        deadline="공고 확인 필요",
                        period="공고문 기준",
                        category=str(section.get("category") or "정책"),
                        status="확인필요",
                        status_color="blue",
                        views=0,
                        support_detail=summary or "상세 내용은 원문 공고를 확인해 주세요.",
                        application_steps=["원문 공고 확인", "자격 요건 확인", "담당 기관 안내에 따라 진행"],
                    )
                )
                if len(policies) >= 20:
                    return policies
    return policies


def _events_from_newsletters(db: Session) -> list[EventDetail]:
    newsletters = db.query(Newsletter).order_by(Newsletter.publish_date.desc()).limit(20).all()
    events: list[EventDetail] = []
    for newsletter in newsletters:
        for event in (newsletter.ai_briefing or {}).get("cultural_events", []):
            title = str(event.get("title") or "").strip()
            if not title:
                continue
            events.append(
                EventDetail(
                    title=title,
                    date=str(event.get("date") or "일정 확인 필요"),
                    time=str(event.get("time") or "시간 확인 필요"),
                    location=str(event.get("place") or "장소 확인 필요"),
                    location_detail=str(event.get("place") or "장소 확인 필요"),
                    capacity=0,
                    registered=0,
                    description=str(event.get("summary") or "지역 소식입니다."),
                    program=[],
                    benefits=[],
                    requirements=[],
                    contact=str(event.get("contact") or "공식 안내 확인"),
                )
            )
            if len(events) >= 10:
                return events
    return events


def _policies_from_rss(items: list[dict]) -> list[PolicyResponse]:
    policies: list[PolicyResponse] = []
    keywords = ("정책", "지원", "모집", "신청", "수당", "대출", "복지", "청년", "교육", "일자리")
    for item in items:
        title = str(item.get("title") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if not title or not any(keyword in f"{title} {summary}" for keyword in keywords):
            continue
        policies.append(
            PolicyResponse(
                id=_stable_id(item.get("link") or title),
                title=title,
                description=summary or "서울시 및 자치구 RSS에서 확인된 정책 공지입니다.",
                deadline="공고 확인 필요",
                period=_rss_period(item),
                category=_policy_category(item),
                status="공고",
                status_color="blue",
                views=0,
                support_detail=summary or "상세 내용은 원문 공고를 확인해 주세요.",
                application_steps=["원문 공고 확인", "자격 요건 확인", "담당 기관 안내에 따라 진행"],
            )
        )
        if len(policies) >= 20:
            break
    return policies


def _events_from_rss(items: list[dict]) -> list[EventDetail]:
    events: list[EventDetail] = []
    for item in items:
        if item.get("category") != "event":
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        events.append(
            EventDetail(
                title=title,
                date=str(item.get("published") or "일정 확인 필요"),
                time="시간 확인 필요",
                location=str(item.get("district") or "서울"),
                location_detail=str(item.get("link") or "원문 공지 확인"),
                capacity=0,
                registered=0,
                description=str(item.get("summary") or "자치구 소식입니다."),
                program=[],
                benefits=[],
                requirements=[],
                contact="원문 공지 확인",
            )
        )
        if len(events) >= 10:
            break
    return events


def _stable_id(value: str) -> int:
    return zlib.crc32(value.encode("utf-8")) % 2_000_000_000


def _rss_period(item: dict) -> str:
    published = str(item.get("published") or "").strip()
    return published or "공고문 기준"


def _policy_category(item: dict) -> str:
    category = str(item.get("category") or "").strip()
    return "정책" if category in {"notice", "press"} else category or "정책"


def _with_relevance(
    policy: PolicyResponse,
    age: int | None,
    has_children: bool,
    employment_status: str,
    interests: list[str],
) -> PolicyResponse:
    relevance = 0
    if age is not None and 19 <= age <= 39 and ("청년" in policy.title or policy.category == "구직"):
        relevance += 10
    if has_children and policy.category in ["육아", "교육"]:
        relevance += 10
    if employment_status == "job-seeking" and (policy.category == "구직" or "수당" in policy.title):
        relevance += 10
    if "housing" in interests and policy.category == "주거":
        relevance += 5

    return policy.model_copy(update={"relevance": relevance})
