import hashlib
import json
import logging
from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.open_data import CulturalEventRow, SDoTEnvRow

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_CLAUDE = "anthropic/claude-haiku-4.5"
MODEL_PERPLEXITY = "perplexity/sonar"
_BASE_HEADERS = {
    "Content-Type": "application/json",
    "HTTP-Referer": "https://every-seoul.vercel.app",
    "X-Title": "EverySeoul",
}

_http_client: httpx.AsyncClient | None = None


def init_http_client() -> None:
    global _http_client
    _http_client = httpx.AsyncClient(timeout=60.0)


async def close_http_client() -> None:
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def _extract_json(text: str) -> str:
    import re

    # 1순위: 마크다운 코드블록 안의 JSON
    match = re.search(r"```(?:json)?\s*(\{.*?})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)

    # 2순위: 중괄호 깊이를 직접 추적해 가장 바깥 객체를 추출
    # 정규식 대신 직접 파싱해야 내부 }에 속지 않음
    start = text.find("{")
    if start == -1:
        return text

    depth = 0
    in_string = False
    escape_next = False

    for i, ch in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    # 응답이 잘린 경우: 시작 지점부터 끝까지 반환 (파싱 실패 처리는 호출부에서)
    return text[start:]


async def _call_openrouter(
    messages: list[dict],
    model: str = MODEL_CLAUDE,
    max_tokens: int = 2048,
) -> dict:
    headers = {**_BASE_HEADERS, "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    try:
        client = _http_client if _http_client is not None else httpx.AsyncClient(timeout=60.0)
        response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"] or ""
        return {
            "content": content,
            "citations": data.get("citations", []),
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"OpenRouter API 오류 {e.response.status_code}: {e.response.text}")
        raise
    except httpx.RequestError as e:
        logger.error(f"OpenRouter 네트워크 오류: {e}")
        raise


async def _call_ai(messages: list[dict], max_tokens: int = 2048) -> str:
    result = await _call_openrouter(messages=messages, model=MODEL_CLAUDE, max_tokens=max_tokens)
    return result["content"]


def _build_rss_context(rss_items: list[dict]) -> str:
    if not rss_items:
        return "수집된 항목 없음"
    lines = []
    for item in rss_items[:15]:
        category = item.get("category", "")
        title = item.get("title", "")
        summary = (item.get("summary") or "")[:100]
        link = item.get("link", "")
        lines.append(f"[{category}] {title} | {summary} | {link}")
    return "\n".join(lines)


def _build_event_context(events: list[CulturalEventRow]) -> str:
    if not events:
        return "수집된 문화행사 없음"
    lines = []
    for event in events[:15]:
        fee = "무료" if event.IS_FREE == "무료" else (event.USE_FEE or "유료")
        lines.append(
            f"{event.TITLE} | 장소: {event.PLACE or '미정'} | "
            f"날짜: {event.DATE or '미정'} | {fee}"
        )
    return "\n".join(lines)


def _build_weather_text(sensor: SDoTEnvRow | None) -> str:
    if not sensor:
        return "날씨 정보 없음"
    return (
        f"평균기온 {sensor.AVG_TEMP}°C, "
        f"습도 {sensor.AVG_HUMI}%, "
        f"평균풍속 {sensor.AVG_WIND_SPEED}m/s"
    )


async def generate_district_briefing(
    district_name: str,
    rss_items: list[dict],
    cultural_events: list[CulturalEventRow],
    weather_sensor: SDoTEnvRow | None = None,
) -> dict:
    weather_text = _build_weather_text(weather_sensor)
    rss_context = _build_rss_context(rss_items)
    event_context = _build_event_context(cultural_events)

    system_prompt = (
        "당신은 서울시 자치구 생활정보 뉴스레터 편집자입니다. "
        "수집된 공공데이터를 분석하여 주민이 이해하기 쉬운 브리핑을 작성하세요. "
        "반드시 순수 JSON만 반환하고, 마크다운 코드블록을 사용하지 마세요."
    )

    user_prompt = f"""다음 {district_name} 데이터로 오늘의 브리핑을 작성해주세요.

[날씨]
{weather_text}

[공지/보도자료/행사/교육 RSS]
{rss_context}

[문화행사]
{event_context}

아래 JSON 형식으로 반환하세요:
{{
  "district": "{district_name}",
  "summary": "오늘 {district_name}의 주요 소식 2~3문장 요약",
  "sections": [
    {{
      "category": "카테고리명 (공지사항/보도자료/행사/교육 중 해당하는 것)",
      "highlights": [
        {{"title": "제목", "summary": "1~2문장 요약", "link": "원문URL"}}
      ]
    }}
  ],
  "cultural_events": [
    {{"title": "행사명", "place": "장소", "date": "날짜", "fee": "무료 또는 요금"}}
  ],
  "weather": "{weather_text}",
  "tags": ["관련태그1", "관련태그2", "관련태그3"]
}}"""

    try:
        raw = await _call_ai(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=4096,
        )
        result = json.loads(_extract_json(raw))
        result["generated_at"] = datetime.now().isoformat()
        return result
    except json.JSONDecodeError as e:
        logger.error(f"{district_name} 브리핑 JSON 파싱 실패: {e}")
        return _fallback_briefing(district_name, weather_text, str(e))
    except Exception as e:
        logger.error(f"{district_name} 브리핑 생성 실패: {e}")
        return _fallback_briefing(district_name, weather_text, str(e))


def _fallback_briefing(district_name: str, weather_text: str, error: str) -> dict:
    return {
        "district": district_name,
        "summary": "브리핑 생성 중 오류가 발생했습니다.",
        "sections": [],
        "cultural_events": [],
        "weather": weather_text,
        "tags": [],
        "generated_at": datetime.now().isoformat(),
        "error": error,
    }


def deduplicate_by_title(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        title_hash = hashlib.md5(item.get("title", "").strip().encode()).hexdigest()
        if title_hash not in seen:
            seen.add(title_hash)
            unique.append(item)
    return unique


async def deduplicate_semantic(items: list[dict]) -> list[dict]:
    if len(items) <= 1:
        return items

    titles_text = "\n".join(f"{i}. {item.get('title', '')}" for i, item in enumerate(items))

    prompt = f"""다음 뉴스 제목 목록에서 같은 사건을 다루는 중복 항목을 찾아주세요.
중복 그룹에서 가장 먼저 나온 항목(낮은 인덱스)만 남기고 나머지는 제거합니다.

제목 목록:
{titles_text}

형식: {{"remove_indices": [제거할 인덱스 배열]}}
중복이 없으면: {{"remove_indices": []}}"""

    try:
        raw = await _call_ai(messages=[{"role": "user", "content": prompt}], max_tokens=512)
        result = json.loads(_extract_json(raw))
        remove_set = set(result.get("remove_indices", []))
        return [item for i, item in enumerate(items) if i not in remove_set]
    except Exception as e:
        logger.warning(f"의미론적 중복 제거 실패 — 원본 반환: {e}")
        return items


async def score_user_match(user_interests: list[str], newsletter_tags: list[str]) -> int:
    if not user_interests or not newsletter_tags:
        return 0

    prompt = f"""사용자 관심사와 뉴스레터 태그의 연관성을 0~100 점수로 평가하세요.

사용자 관심사: {", ".join(user_interests)}
뉴스레터 태그: {", ".join(newsletter_tags)}

형식: {{"score": 정수, "reason": "한 문장 이유"}}"""

    try:
        raw = await _call_ai(messages=[{"role": "user", "content": prompt}], max_tokens=128)
        result = json.loads(_extract_json(raw))
        return max(0, min(100, int(result.get("score", 0))))
    except Exception as e:
        logger.warning(f"매칭 점수 계산 실패: {e}")
        return 0


async def _stage1_spam_check(title: str, summary: str) -> dict:
    prompt = f"""다음 공공기관 뉴스가 스팸, 광고, 또는 공공정보답지 않은 이상한 내용인지 확인하세요.

제목: {title}
내용: {summary[:500]}

형식: {{
  "pass": true 또는 false,
  "flags": ["의심 사유 (없으면 빈 배열)"]
}}"""
    try:
        raw = await _call_ai(messages=[{"role": "user", "content": prompt}], max_tokens=256)
        return json.loads(_extract_json(raw))
    except Exception as e:
        logger.warning(f"1단계 스팸 검사 실패: {e}")
        return {"pass": True, "flags": []}


async def _stage2_factcheck(title: str, summary: str) -> dict:
    prompt = f"""당신은 서울시 공공기관 뉴스의 팩트체크 전문가입니다.
아래 뉴스는 서울시 자치구청의 공식 RSS에서 수집된 공공정보입니다.
실시간 웹 검색으로 해당 기관의 발표·정책과 일치하는지 확인하고,
사실과 명백히 다르거나 의심스러운 경우에만 "오류 의심"으로 표시하세요.
웹에 아직 인덱싱되지 않은 최신 공문은 "확인 불가"로 표시하세요.

제목: {title}
내용: {summary[:500]}

다음 형식으로 한국어로 답변하세요:
- 사실 여부: (확인됨 / 확인 불가 / 오류 의심)
- 검토 의견: 한 문장"""

    try:
        result = await _call_openrouter(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_PERPLEXITY,
            max_tokens=512,
        )
        content: str = result["content"]
        citations: list = result["citations"]

        if "오류 의심" in content:
            is_reliable, confidence = False, 20
        elif "확인됨" in content:
            is_reliable, confidence = True, 90 if citations else 75
        else:
            is_reliable, confidence = True, 60

        return {"is_reliable": is_reliable, "confidence": confidence, "review": content, "citations": citations}
    except Exception as e:
        logger.warning(f"2단계 팩트체크 실패 — 기본값 반환: {e}")
        return {"is_reliable": True, "confidence": 60, "review": "", "citations": []}


async def verify_content(title: str, summary: str) -> dict:
    spam_result = await _stage1_spam_check(title, summary)
    if not spam_result.get("pass", True):
        logger.info(f"1단계 스팸 탐지 — 제목: {title[:50]}")
        return {
            "is_reliable": False,
            "confidence": 0,
            "stage": "spam_filter",
            "flags": spam_result.get("flags", []),
            "citations": [],
        }

    fact_result = await _stage2_factcheck(title, summary)
    return {
        "is_reliable": fact_result["is_reliable"],
        "confidence": fact_result["confidence"],
        "stage": "factcheck",
        "flags": spam_result.get("flags", []),
        "review": fact_result.get("review", ""),
        "citations": fact_result.get("citations", []),
    }
