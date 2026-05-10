from app.api.endpoints.life_info import _first_text, _format_degree, _format_rain, _weather_code_label


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
