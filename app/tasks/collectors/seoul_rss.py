import asyncio
import html
import logging
import re

import feedparser
from bs4 import BeautifulSoup

from app.core.constants import DISTRICT_RSS_URLS, SeoulDistrict

logger = logging.getLogger(__name__)


def clean_html_text(raw_text: str) -> str:
    if not raw_text:
        return ""

    decoded_text = re.sub(
        r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), raw_text
    )
    decoded_text = html.unescape(decoded_text)

    soup = BeautifulSoup(decoded_text, "html.parser")
    pure_text = soup.get_text(separator=" ", strip=True)

    pure_text = pure_text.replace("\xa0", " ")
    pure_text = re.sub(r"\s+", " ", pure_text)

    return pure_text.strip()


def fix_broken_encoding(text: str) -> str:
    if not text:
        return ""

    if "ë" in text or "ê" in text or "ì" in text:
        try:
            return text.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text

    return text


def fetch_rss_sync(url: str) -> list:
    try:
        parsed_data = feedparser.parse(url)
        if getattr(parsed_data, "bozo", 0) == 1:
            bozo_exc = str(parsed_data.bozo_exception)
            # content-type 불일치(text/plain 등)는 경고만 하고 계속 진행
            # feedparser는 content-type 무관하게 XML 파싱을 시도하므로 entries가 존재할 수 있음
            if "media type" in bozo_exc.lower() or "not an xml" in bozo_exc.lower():
                logger.warning(f"RSS content-type 불일치 (파싱 계속 진행) URL: {url} 원인: {bozo_exc}")
            else:
                logger.error(f"RSS 파싱 에러 URL: {url} 원인: {bozo_exc}")
                return []
        return parsed_data.entries
    except Exception as e:
        logger.error(f"RSS 외부 통신 예외 발생 URL: {url} 에러: {e}")
        return []


async def collect_district_rss(district: SeoulDistrict) -> list:
    """개별 자치구의 모든 카테고리 RSS 데이터를 비동기적으로 가져오는 함수"""
    urls_dict = DISTRICT_RSS_URLS.get(district)

    if not urls_dict:
        return []

    tasks = []
    categories = []

    for category, url in urls_dict.items():
        if url:
            tasks.append(asyncio.to_thread(fetch_rss_sync, url))
            categories.append(category)

    gathered_entries = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for category, entries in zip(categories, gathered_entries):
        if isinstance(entries, Exception):
            logger.error(f"{district.value} - {category.value} 수집 실패: {entries}")
            continue

        for entry in entries:
            try:
                fixed_title = fix_broken_encoding(entry.get("title", ""))
                fixed_summary = fix_broken_encoding(entry.get("summary", ""))

                # 2. HTML 찌꺼기 및 띄어쓰기 정제
                clean_title = clean_html_text(fixed_title)
                clean_summary = clean_html_text(fixed_summary)
                results.append(
                    {
                        "district": district.value,
                        "category": category.value,
                        "title": clean_title,
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "summary": clean_summary,
                    }
                )
            except Exception as e:
                logger.error(f"{district.value} 개별 항목 가공 중 에러: {e}")
                continue

    return results


async def collect_all_seoul_rss() -> list:
    tasks = [collect_district_rss(district) for district in SeoulDistrict]
    gathered_results = await asyncio.gather(*tasks, return_exceptions=True)

    final_data = []
    for result in gathered_results:
        if not isinstance(result, Exception) and result:
            final_data.extend(result)

    return final_data
