from app.api.endpoints.life_info import (
    _first_text,
    _format_degree,
    _format_rain,
    _format_utc_update,
    _weather_code_label,
)


def test_weather_code_label_uses_known_korean_labels() -> None:
    assert _weather_code_label(0) == "맑음"
    assert _weather_code_label(63) == "비"
    assert _weather_code_label(999) == "예보"


def test_format_helpers_handle_numbers_and_missing_values() -> None:
    assert _format_degree(12.34) == "12°"
    assert _format_degree(None) == "-"
    assert _format_rain(0) == "0%"
    assert _format_rain(None) == "-"


def test_first_text_returns_first_available_key() -> None:
    row = {"A": "", "B": None, "C": " 서울역 "}

    assert _first_text(row, "A", "B", "C") == "서울역"
    assert _first_text(row, "D") == ""


def test_format_utc_update_returns_korean_kst_text() -> None:
    assert _format_utc_update("Sun, 10 May 2026 00:02:31 +0000") == (
        "2026년 5월 10일 09:02"
    )
