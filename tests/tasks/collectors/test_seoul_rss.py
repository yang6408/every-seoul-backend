import pytest

from app.core.constants import RssCategory, SeoulDistrict
from app.tasks.collectors.seoul_rss import clean_html_text, collect_district_rss


def test_clean_html_text_preserves_block_breaks() -> None:
    raw = "<p>첫 문단</p><p>둘째 문단</p><br>※ 참고 사항"

    assert clean_html_text(raw) == "첫 문단\n둘째 문단\n※ 참고 사항"


def test_clean_html_text_breaks_numbered_notice_items() -> None:
    raw = (
        "안내문 1. 신청기간: 2026. 5. 6.(수) ~ 9. 10.(목) "
        "2. 신청대상: 공동주택 ※ 참고 붙임 1. 공고문"
    )

    assert clean_html_text(raw) == (
        "안내문\n"
        "1. 신청기간: 2026. 5. 6.(수) ~ 9. 10.(목)\n"
        "2. 신청대상: 공동주택\n"
        "※ 참고\n"
        "붙임 1. 공고문"
    )


@pytest.mark.asyncio
async def test_collect_district_rss_uses_korean_district_name(monkeypatch) -> None:
    async def fake_to_thread(function, url):
        return [
            {
                "title": "행사 안내",
                "summary": "행사 요약",
                "link": "https://example.com",
                "published": "2026-05-07",
            }
        ]

    monkeypatch.setattr("app.tasks.collectors.seoul_rss.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr(
        "app.tasks.collectors.seoul_rss.DISTRICT_RSS_URLS",
        {SeoulDistrict.GANGNAM: {RssCategory.EVENT: "https://example.com/rss"}},
    )

    result = await collect_district_rss(SeoulDistrict.GANGNAM)

    assert result[0]["district"] == "강남구"
