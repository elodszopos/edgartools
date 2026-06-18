"""Unit tests for CIK helpers (pure functions only)."""

import pytest

from app.cik import pad_cik, parse_entity_id


def test_pad_cik_int():
    assert pad_cik(320193) == "0000320193"


def test_pad_cik_str():
    assert pad_cik("320193") == "0000320193"


def test_pad_cik_already_padded():
    assert pad_cik("0000320193") == "0000320193"


def test_pad_cik_consolidation_points_resolve_identically():
    # every call site routes its CIK through pad_cik: Company.cik (int), index rows (int/str),
    # EFTS result.cik (str), already-padded strings. The same logical CIK must collapse to one
    # canonical wire value no matter which representation a converter hands the helper.
    forms = [320193, "320193", "0000320193", " 320193 "]
    assert {pad_cik(form) for form in forms} == {"0000320193"}


def test_pad_cik_strips_whitespace():
    assert pad_cik(" 320193 ") == "0000320193"


def test_pad_cik_zero_rejected():
    with pytest.raises(ValueError):
        pad_cik(0)
    with pytest.raises(ValueError):
        pad_cik("0000000000")


def test_pad_cik_negative_rejected():
    with pytest.raises(ValueError):
        pad_cik(-5)


def test_pad_cik_too_long_rejected():
    with pytest.raises(ValueError):
        pad_cik(12_345_678_901)


def test_pad_cik_non_digit_rejected():
    with pytest.raises(ValueError):
        pad_cik("12a4")


def test_pad_cik_non_ascii_digits_rejected():
    with pytest.raises(ValueError):
        pad_cik("¹12345")  # superscript digit passes str.isdigit but is not a CIK


def test_pad_cik_bool_rejected():
    with pytest.raises(TypeError):
        pad_cik(True)


def test_pad_cik_other_type_rejected():
    with pytest.raises(TypeError):
        pad_cik(320193.0)  # type: ignore[arg-type]


def test_parse_entity_id_numeric_becomes_cik_int():
    assert parse_entity_id("320193") == 320193
    assert parse_entity_id(" 0000320193 ") == 320193


def test_parse_entity_id_ticker_passes_through():
    assert parse_entity_id("AAPL") == "AAPL"
    assert parse_entity_id(" brk.a ") == "brk.a"


def test_parse_entity_id_empty_rejected():
    with pytest.raises(ValueError):
        parse_entity_id("")
    with pytest.raises(ValueError):
        parse_entity_id("   ")


def test_parse_entity_id_out_of_range_cik_rejected():
    with pytest.raises(ValueError):
        parse_entity_id("99999999999")
