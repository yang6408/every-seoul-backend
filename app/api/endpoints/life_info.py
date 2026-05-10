from datetime import datetime
from zoneinfo import ZoneInfo

import asyncio
import httpx
from fastapi import APIRouter, Query

from app.schemas.life_info import (
    AirQualityMetric,
    InfoRow,
    LifeInfoResponse,
    Metric,
    ProductPriceInfo,
    ProductPricePoint,
    ProductStorePrice,
)
from app.tasks.collectors.open_data import collect_sDoTEnv, fetch_range_data

router = APIRouter()

_KST = ZoneInfo("Asia/Seoul")
_HTTP_TIMEOUT = 8

_DISTRICT_COORDS = {
    "강남구": (37.5172, 127.0473),
    "강동구": (37.5301, 127.1238),
    "강북구": (37.6396, 127.0257),
    "강서구": (37.5509, 126.8495),
    "관악구": (37.4784, 126.9516),
    "광진구": (37.5384, 127.0823),
    "구로구": (37.4955, 126.8877),
    "금천구": (37.4569, 126.8955),
    "노원구": (37.6542, 127.0568),
    "도봉구": (37.6688, 127.0471),
    "동대문구": (37.5744, 127.0396),
    "동작구": (37.5124, 126.9393),
    "마포구": (37.5663, 126.9015),
    "서대문구": (37.5791, 126.9368),
    "서초구": (37.4837, 127.0324),
    "성동구": (37.5633, 127.0369),
    "성북구": (37.5894, 127.0167),
    "송파구": (37.5145, 127.1059),
    "양천구": (37.5169, 126.8664),
    "영등포구": (37.5264, 126.8963),
    "용산구": (37.5326, 126.9905),
    "은평구": (37.6027, 126.9291),
    "종로구": (37.5735, 126.9788),
    "중구": (37.5636, 126.9976),
    "중랑구": (37.6063, 127.0927),
}


@router.get("/", response_model=LifeInfoResponse)
async def get_life_info(district: str = Query("강남구", min_length=1)):
    now = datetime.now(_KST)
    generated_at = f"{now.year}년 {now.month}월 {now.day}일 {now:%H:%M} 기준"
    sensor, products, forecast, roads, transit, economy = await asyncio.gather(
        _load_district_sensor(district),
        _load_product_prices(),
        _load_weekly_forecast(district),
        _load_road_info(),
        _load_transit_info(),
        _load_economy_info(),
    )

    return LifeInfoResponse(
        district=district,
        generated_at=generated_at,
        weather_summary=f"서울시 {district} 기준 날씨 정보를 제공합니다",
        temperature=_format_temperature(sensor.AVG_TEMP),
        feels_like=_format_temperature(sensor.AVG_EFFE_TEMP or sensor.AVG_TEMP),
        condition=_condition_from_sensor(sensor),
        weather_metrics=_weather_metrics(sensor),
        air_quality=_air_quality(sensor),
        weekly_forecast=forecast,
        roads=roads,
        transit=transit,
        economy=economy,
        safety_alerts=[],
        product_prices=products,
        notices=[],
    )


async def _load_district_sensor(district: str):
    sensors = await collect_sDoTEnv(1, 1000)
    for sensor in sensors:
        region = f"{sensor.AUTONOMOUS_DISTRICT or ''} {sensor.ADMINISTRATIVE_DISTRICT or ''}"
        if district in region or district[:2] in region:
            return sensor
    return sensors[0] if sensors else _FallbackSensor()


async def _load_product_prices() -> list[ProductPriceInfo]:
    rows = await fetch_range_data("ListNecessariesPricesService", 1, 300)
    products: list[ProductPriceInfo] = []
    seen: set[str] = set()
    for row in rows:
        name = str(row.get("A_NAME") or row.get("P_NAME") or "").strip()
        price = _to_int(row.get("A_PRICE") or row.get("PRICE"))
        market = str(row.get("M_NAME") or row.get("MARKET_NAME") or "서울시").strip()
        if not name or price is None or name in seen:
            continue
        seen.add(name)
        products.append(
            ProductPriceInfo(
                name=name,
                category=str(row.get("P_NAME") or "생활물가"),
                current_price=price,
                previous_price=price,
                unit=str(row.get("A_UNIT") or "1개"),
                change=0,
                trend="up",
                stores=[ProductStorePrice(name=market, price=price, location="서울")],
                graph=[ProductPricePoint(date="현재", price=price)],
            )
        )
        if len(products) >= 6:
            break
    return products


async def _load_weekly_forecast(district: str) -> list[list[str]]:
    latitude, longitude = _DISTRICT_COORDS.get(district, _DISTRICT_COORDS["강남구"])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "Asia/Seoul",
        "forecast_days": 7,
    }
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            daily = response.json().get("daily", {})
    except Exception:
        return []

    dates = daily.get("time", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    rains = daily.get("precipitation_probability_max", [])
    codes = daily.get("weather_code", [])

    forecast = []
    for index, date_text in enumerate(dates[:7]):
        day = "오늘" if index == 0 else _format_weekday(date_text)
        forecast.append(
            [
                day,
                _weather_code_label(codes[index] if index < len(codes) else None),
                _format_degree(highs[index] if index < len(highs) else None),
                _format_degree(lows[index] if index < len(lows) else None),
                _format_rain(rains[index] if index < len(rains) else None),
            ]
        )
    return forecast


async def _load_road_info() -> list[InfoRow]:
    rows = await _first_open_data_rows(["TrafficInfo", "RealtimeRoadTraffic", "ListRoadInfo"], 1, 50)
    road_rows: list[InfoRow] = []
    for row in rows:
        name = _first_text(row, "ROAD_NAME", "roadName", "LINK_ID", "NAME")
        speed = _first_text(row, "SPD", "SPEED", "speed")
        status = _first_text(row, "TRAFFIC_STATE", "TRAFFICSTATUS", "STATE", "GRADE")
        if not name:
            continue
        road_rows.append(
            InfoRow(
                label=name,
                value=status or "교통 정보",
                meta=f"평균 {speed}km/h" if speed else None,
            )
        )
        if len(road_rows) >= 3:
            break
    return road_rows


async def _load_transit_info() -> list[InfoRow]:
    rows = await _first_open_data_rows(["SearchSTNBySubwayLineInfo", "CardSubwayStatsNew"], 1, 30)
    transit_rows: list[InfoRow] = []
    for row in rows:
        line = _first_text(row, "LINE_NUM", "LINE_NUM_NM", "SUBWAY_ID", "USE_MON")
        station = _first_text(row, "STATION_NM", "SUB_STA_NM", "SBWY_STNS_NM")
        if not line and not station:
            continue
        transit_rows.append(
            InfoRow(
                label=line or "지하철",
                value=station or "역 정보",
                meta="서울 열린데이터 기준",
            )
        )
        if len(transit_rows) >= 3:
            break
    return transit_rows


async def _load_economy_info() -> list[InfoRow]:
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            response = await client.get("https://open.er-api.com/v6/latest/USD")
            response.raise_for_status()
            data = response.json()
    except Exception:
        return []

    krw = data.get("rates", {}).get("KRW")
    updated = data.get("time_last_update_utc")
    if not isinstance(krw, (int, float)):
        return []
    return [
        InfoRow(
            label="USD/KRW",
            value=f"{krw:,.2f}원",
            meta=f"갱신 {updated}" if updated else "환율 API 기준",
        )
    ]


async def _first_open_data_rows(
    service_names: list[str],
    start_idx: int,
    end_idx: int,
) -> list[dict]:
    for service_name in service_names:
        rows = await fetch_range_data(service_name, start_idx, end_idx)
        if rows:
            return rows
    return []


class _FallbackSensor:
    AVG_TEMP = None
    AVG_EFFE_TEMP = None
    AVG_HUMI = None
    AVG_WIND_SPEED = None
    AVG_O3 = None
    AVG_NO2 = None
    AVG_CO = None
    AVG_SO2 = None


def _format_temperature(value: float | None) -> str:
    return f"{value:.1f}°C" if value is not None else "정보 없음"


def _condition_from_sensor(sensor) -> str:
    if sensor.AVG_TEMP is None:
        return "관측 정보 없음"
    if sensor.AVG_HUMI and sensor.AVG_HUMI >= 80:
        return "습함"
    return "관측 중"


def _weather_metrics(sensor) -> list[Metric]:
    return [
        Metric(label="습도", value=_format_percent(sensor.AVG_HUMI)),
        Metric(label="바람", value=_format_speed(sensor.AVG_WIND_SPEED)),
        Metric(label="강수확률", value="제공 안 됨"),
        Metric(label="기압", value="제공 안 됨"),
        Metric(label="가시거리", value="제공 안 됨"),
        Metric(label="자외선지수", value="제공 안 됨"),
    ]


def _air_quality(sensor) -> list[AirQualityMetric]:
    return [
        AirQualityMetric(label="오존 (O₃)", status=_air_status(sensor.AVG_O3), value=_format_ppm(sensor.AVG_O3), tone="blue"),
        AirQualityMetric(label="이산화질소 (NO₂)", status=_air_status(sensor.AVG_NO2), value=_format_ppm(sensor.AVG_NO2), tone="green"),
        AirQualityMetric(label="일산화탄소 (CO)", status=_air_status(sensor.AVG_CO), value=_format_ppm(sensor.AVG_CO), tone="green"),
        AirQualityMetric(label="이산화황 (SO₂)", status=_air_status(sensor.AVG_SO2), value=_format_ppm(sensor.AVG_SO2), tone="green"),
    ]


def _format_percent(value: float | None) -> str:
    return f"{value:.0f}%" if value is not None else "정보 없음"


def _format_speed(value: float | None) -> str:
    return f"{value:.1f}m/s" if value is not None else "정보 없음"


def _format_ppm(value: float | None) -> str:
    return f"{value:.3f}ppm" if value is not None else "정보 없음"


def _air_status(value: float | None) -> str:
    if value is None:
        return "정보 없음"
    return "좋음" if value < 0.05 else "보통"


def _to_int(value) -> int | None:
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return None


def _format_weekday(date_text: str) -> str:
    try:
        date = datetime.fromisoformat(date_text)
    except ValueError:
        return date_text
    return ["월", "화", "수", "목", "금", "토", "일"][date.weekday()]


def _weather_code_label(code: int | None) -> str:
    if code is None:
        return "예보"
    if code == 0:
        return "맑음"
    if code in {1, 2, 3}:
        return "구름"
    if code in {45, 48}:
        return "안개"
    if code in {51, 53, 55, 61, 63, 65, 80, 81, 82}:
        return "비"
    if code in {71, 73, 75, 77, 85, 86}:
        return "눈"
    if code in {95, 96, 99}:
        return "뇌우"
    return "예보"


def _format_degree(value) -> str:
    return f"{float(value):.0f}°" if isinstance(value, (int, float)) else "-"


def _format_rain(value) -> str:
    return f"{float(value):.0f}%" if isinstance(value, (int, float)) else "-"


def _first_text(row: dict, *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""
