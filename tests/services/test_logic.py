from app.services.logic import _filter_rss_by_district


def test_filter_rss_by_district_accepts_english_and_korean_names() -> None:
    items = [
        {"district": "Gangnam", "title": "legacy"},
        {"district": "강남구", "title": "current"},
        {"district": "강북구", "title": "other"},
    ]

    result = _filter_rss_by_district(items, "Gangnam")

    assert [item["title"] for item in result] == ["legacy", "current"]
