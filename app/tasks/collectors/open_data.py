import requests
import asyncio
import logging
from app.core.config import settings
from app.schemas.open_data import CulturalEventRow, SDoTEnvRow

logger = logging.getLogger(__name__)

SEOUL_API_BASE_URL = "http://openapi.seoul.go.kr:8088/{key}/{type}/{service}/{start}/{end}/"

def _fetch_api_sync(service_name: str, start_idx: int, end_idx: int) -> dict:
    """단일 페이지 동기 요청 (공통)"""
    if not settings.SEOUL_OPEN_API_KEY:
        logger.error("SEOUL_OPEN_API_KEY가 설정되지 않았습니다.")
        return None

    url = SEOUL_API_BASE_URL.format(
        key=settings.SEOUL_OPEN_API_KEY,
        type="json",
        service=service_name,
        start=start_idx,
        end=end_idx
    )
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API 통신 에러 ({service_name}: {start_idx}~{end_idx}) - {e}")
        return None

async def fetch_all_data(service_name: str) -> list:
    """특정 서비스의 전체 데이터를 비동기 병렬로 모두 긁어오는 공통 엔진"""
    first_req = await asyncio.to_thread(_fetch_api_sync, service_name, 1, 1)
    
    if not first_req or service_name not in first_req:
        logger.warning(f"{service_name} 응답 실패 또는 데이터 없음")
        return []
        
    total_count = first_req[service_name].get("list_total_count", 0)
    if total_count == 0:
        return []

    tasks = []
    chunk_size = 1000
    for start in range(1, total_count + 1, chunk_size):
        end = min(start + chunk_size - 1, total_count)
        tasks.append(asyncio.to_thread(_fetch_api_sync, service_name, start, end))

    gathered_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_rows = []
    for result in gathered_results:
        if isinstance(result, dict) and service_name in result:
            all_rows.extend(result[service_name].get("row", []))
            
    return all_rows

async def fetch_range_data(service_name: str, start_idx: int, end_idx: int) -> list:
    if start_idx < 1 or end_idx < start_idx:
        logger.error(f"잘못된 구간 요청입니다: {start_idx} ~ {end_idx}")
        return []

    tasks = []
    chunk_size = 1000
    
    for current_start in range(start_idx, end_idx + 1, chunk_size):
        current_end = min(current_start + chunk_size - 1, end_idx)
        tasks.append(asyncio.to_thread(_fetch_api_sync, service_name, current_start, current_end))

    gathered_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_rows = []
    for result in gathered_results:
        if isinstance(result, dict) and service_name in result:
            all_rows.extend(result[service_name].get("row", []))
            
    return all_rows

async def collect_sDoTEnv(start_idx: int, end_idx: int) -> list[SDoTEnvRow]:
    """스마트서울 도시데이터 센서(S-DoT) 환경정보 (실시간) 수집 및 구조화"""
    service_name = "sDoTEnv"
    raw_data = await fetch_range_data(service_name, start_idx, end_idx)

    processed_data = []
    for row in raw_data:
        try:
            sensor_data = SDoTEnvRow(**row)
            processed_data.append(sensor_data)
        except Exception as e:
            logger.warning(f"S-DoT 불량 센서 데이터 스킵 - 사유: {e}")
            continue
            
    return processed_data

async def collect_cultural_event_info(start_idx: int, end_idx: int) -> list[CulturalEventRow]:
    """서울시 문화행사 정보 수집 및 구조화"""
    service_name = "culturalEventInfo"
    raw_data = await fetch_range_data(service_name, start_idx, end_idx)

    processed_data = []
    for row in raw_data:
        try:
            event_data = CulturalEventRow(**row)
            processed_data.append(event_data)
        except Exception as e:
            logger.warning(f"문화행사 정보 불량 - 사유: {e}")
            continue
            
    return processed_data
