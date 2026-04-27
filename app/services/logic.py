import asyncio
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.db.models.newsletter import Newsletter
from app.db.session import SessionLocal
from app.schemas.open_data import CulturalEventRow, SDoTEnvRow
from app.services import ai_service
from app.tasks.collectors.open_data import collect_cultural_event_info, collect_sDoTEnv
from app.tasks.collectors.seoul_rss import collect_all_seoul_rss

logger = logging.getLogger(__name__)

DISTRICT_KR: dict[str, str] = {
    "Gangnam": "강남구",
    "Gangdong": "강동구",
    "Gangbuk": "강북구",
    "Gangseo": "강서구",
    "Gwanak": "관악구",
    "Gwangjin": "광진구",
    "Guro": "구로구",
    "Geumcheon": "금천구",
    "Nowon": "노원구",
    "Dobong": "도봉구",
    "Dongdaemun": "동대문구",
    "Dongjak": "동작구",
    "Mapo": "마포구",
    "Seodaemun": "서대문구",
    "Seocho": "서초구",
    "Seongdong": "성동구",
    "Seongbuk": "성북구",
    "Yangcheon": "양천구",
    "Yeongdeungpo": "영등포구",
    "Yongsan": "용산구",
    "Eunpyeong": "은평구",
    "Jongno": "종로구",
    "Jung": "중구",
    "Jungnang": "중랑구",
    "Songpa": "송파구",
}


def _filter_rss_by_district(all_rss: list[dict], district_en: str) -> list[dict]:
    return [item for item in all_rss if item.get("district") == district_en]


def _filter_events_by_district(
    all_events: list[CulturalEventRow], district_kr: str
) -> list[CulturalEventRow]:
    return [e for e in all_events if e.GUNAME == district_kr]


def _pick_district_sensor(sensors: list[SDoTEnvRow], district_kr: str) -> SDoTEnvRow | None:
    for s in sensors:
        region = (s.AUTONOMOUS_DISTRICT or "") + (s.ADMINISTRATIVE_DISTRICT or "")
        if district_kr[:2] in region:
            return s
    return None


def _save_newsletter(db: Session, district_kr: str, briefing: dict, tags: list[str]) -> None:
    today_str = date.today().strftime("%Y년 %m월 %d일")
    newsletter = Newsletter(
        title=f"{today_str} {district_kr} 생활정보 브리핑",
        ai_briefing=briefing,
        tags=tags,
    )
    db.add(newsletter)
    db.commit()
    logger.info(f"{district_kr} 뉴스레터 저장 완료 (id={newsletter.id})")


async def process_daily_newsletters() -> None:
    logger.info("=== 일일 뉴스레터 파이프라인 시작 ===")

    try:
        all_rss, all_events, all_sensors = await asyncio.gather(
            collect_all_seoul_rss(),
            collect_cultural_event_info(1, 1000),
            collect_sDoTEnv(1, 500),
        )
    except Exception as e:
        logger.error(f"데이터 수집 실패: {e}")
        return

    logger.info(
        f"수집 완료 — RSS: {len(all_rss)}건 | 문화행사: {len(all_events)}건 | 센서: {len(all_sensors)}건"
    )

    all_rss = ai_service.deduplicate_by_title(all_rss)
    logger.info(f"해시 중복 제거 후 RSS: {len(all_rss)}건")

    db: Session = SessionLocal()
    try:
        for district_en, district_kr in DISTRICT_KR.items():
            await _process_one_district(
                db, district_en, district_kr, all_rss, all_events, all_sensors
            )
    finally:
        db.close()

    logger.info("=== 일일 뉴스레터 파이프라인 완료 ===")


async def _process_one_district(
    db: Session,
    district_en: str,
    district_kr: str,
    all_rss: list[dict],
    all_events: list[CulturalEventRow],
    all_sensors: list[SDoTEnvRow],
) -> None:
    rss_items = _filter_rss_by_district(all_rss, district_en)
    events = _filter_events_by_district(all_events, district_kr)
    sensor = _pick_district_sensor(all_sensors, district_kr)

    if not rss_items and not events:
        logger.info(f"{district_kr}: 수집된 데이터 없음 — 스킵")
        return

    rss_items = await ai_service.deduplicate_semantic(rss_items)

    try:
        briefing = await ai_service.generate_district_briefing(
            district_name=district_kr,
            rss_items=rss_items,
            cultural_events=events,
            weather_sensor=sensor,
        )
        tags: list[str] = briefing.get("tags", [])
        _save_newsletter(db, district_kr, briefing, tags)
    except Exception as e:
        logger.error(f"{district_kr} 브리핑/저장 실패: {e}")
