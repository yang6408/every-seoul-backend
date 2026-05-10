from app.api.endpoints.policy import _events_from_rss, _policies_from_rss


def test_policies_from_rss_filters_and_maps_policy_like_items() -> None:
    items = [
        {
            "title": "청년 월세 지원 모집",
            "summary": "서울시 청년 주거 지원 안내",
            "link": "https://example.com/policy",
            "published": "2026-05-01",
            "category": "notice",
        },
        {"title": "일반 소식", "summary": "날씨 안내", "category": "notice"},
    ]

    policies = _policies_from_rss(items)

    assert len(policies) == 1
    assert policies[0].title == "청년 월세 지원 모집"
    assert policies[0].period == "2026-05-01"
    assert policies[0].category == "정책"


def test_events_from_rss_maps_event_items_without_fake_capacity() -> None:
    items = [
        {
            "title": "서울 문화 행사",
            "summary": "행사 안내",
            "link": "https://example.com/event",
            "published": "2026-05-02",
            "district": "마포구",
            "category": "event",
        },
        {"title": "행사 아닌 공지", "category": "notice"},
    ]

    events = _events_from_rss(items)

    assert len(events) == 1
    assert events[0].title == "서울 문화 행사"
    assert events[0].capacity == 0
    assert events[0].registered == 0
