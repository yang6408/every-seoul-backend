"""
실행: ./venv/Scripts/python test_ai.py
"""
import asyncio
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from app.tasks.collectors.seoul_rss import collect_district_rss
from app.services.ai_service import generate_district_briefing, verify_content
from app.core.constants import SeoulDistrict

TARGET_DISTRICT = SeoulDistrict.GURO  # 테스트할 자치구
DISTRICT_KR = "구로구"


async def main():
    print("\n" + "=" * 50)
    print(f"  EverySeoul AI 브리핑 테스트 - {DISTRICT_KR}")
    print("=" * 50 + "\n")

    # 1. RSS 수집
    print("[1단계] RSS 수집 중...")
    rss_items = await collect_district_rss(TARGET_DISTRICT)
    print(f"   -> {len(rss_items)}건 수집 완료\n")

    if not rss_items:
        print("수집된 RSS 항목이 없습니다. 다른 자치구로 변경해보세요.")
        return

    # 수집된 RSS 미리보기
    print("수집된 RSS 샘플 (최대 3건):")
    for i, item in enumerate(rss_items[:3], 1):
        print(f"  {i}. [{item['category']}] {item['title']}")
    print()

    # 2. AI 브리핑 생성
    print("[2단계] AI 브리핑 생성 중... (OpenRouter / claude-haiku-4-5)")
    briefing = await generate_district_briefing(
        district_name=DISTRICT_KR,
        rss_items=rss_items,
        cultural_events=[],
        weather_sensor=None,
    )

    print("\n" + "-" * 50)
    print("생성된 브리핑 결과:")
    print("-" * 50)
    print(json.dumps(briefing, ensure_ascii=False, indent=2))

    # 3. 첫 번째 항목 진실성 검증
    first = rss_items[0]
    print("\n" + "-" * 50)
    print(f"[3단계] 진실성 검증 - {first['title'][:40]}...")
    print("-" * 50)
    print("  1단계: Claude 스팸 필터 중...")
    print("  2단계: Perplexity Sonar 팩트체크 중...")
    verify_result = await verify_content(first["title"], first["summary"])
    print(json.dumps(verify_result, ensure_ascii=False, indent=2))

    print("\n" + "=" * 50)
    print("  테스트 완료")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
