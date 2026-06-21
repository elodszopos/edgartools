"""Unit tests for the JSON scalar policy (pure functions only)."""

from datetime import date, datetime
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from app.serialize import (
    eastern_naive_to_utc,
    to_bool,
    to_date,
    to_float,
    to_int,
    to_iso_str,
    to_str,
    to_utc_datetime,
    utc_naive_to_utc,
)


def test_to_int_numpy_int():
    assert to_int(np.int64(42)) == 42


def test_to_int_integral_numpy_float():
    assert to_int(np.float64(7.0)) == 7


def test_to_int_integral_decimal():
    assert to_int(Decimal("12")) == 12


def test_to_int_none_and_nan():
    assert to_int(None) is None
    assert to_int(float("nan")) is None
    assert to_int(np.float64("nan")) is None


def test_to_int_inf_is_null():
    assert to_int(float("inf")) is None
    assert to_int(float("-inf")) is None


def test_to_int_fractional_float_raises():
    with pytest.raises(TypeError):
        to_int(7.5)


def test_to_int_fractional_decimal_raises():
    with pytest.raises(TypeError):
        to_int(Decimal("7.5"))


def test_to_int_bool_raises():
    with pytest.raises(TypeError):
        to_int(True)


def test_to_int_str_raises():
    with pytest.raises(TypeError):
        to_int("5")


def test_to_float_decimal():
    assert to_float(Decimal("3.14")) == 3.14


def test_to_float_decimal_nan_is_null():
    assert to_float(Decimal("NaN")) is None


def test_to_float_numpy():
    assert to_float(np.float32(1.5)) == 1.5
    assert to_float(np.int32(5)) == 5.0


def test_to_float_nan_and_inf_are_null():
    assert to_float(float("nan")) is None
    assert to_float(float("inf")) is None
    assert to_float(Decimal("Infinity")) is None


def test_to_float_bool_raises():
    with pytest.raises(TypeError):
        to_float(False)


def test_to_float_str_raises():
    with pytest.raises(TypeError):
        to_float("3.14")


def test_to_iso_str_passthrough():
    assert to_iso_str("2024-05-01") == "2024-05-01"


def test_to_iso_str_strips():
    assert to_iso_str("  2024-05-01  ") == "2024-05-01"


def test_to_iso_str_date():
    assert to_iso_str(date(2024, 5, 1)) == "2024-05-01"


def test_to_iso_str_datetime():
    assert to_iso_str(datetime(2024, 5, 1, 12, 30)) == "2024-05-01"


def test_to_iso_str_none_and_nan():
    assert to_iso_str(None) is None
    assert to_iso_str(float("nan")) is None
    assert to_iso_str(pd.NaT) is None


def test_to_iso_str_empty_is_null():
    assert to_iso_str("") is None
    assert to_iso_str("   ") is None


def test_to_iso_str_int_raises():
    with pytest.raises(TypeError, match="cannot coerce int to ISO str"):
        to_iso_str(42)


def test_to_str_strips():
    assert to_str(" Apple Inc. ") == "Apple Inc."


def test_to_str_empty_is_null():
    assert to_str("") is None
    assert to_str("   ") is None
    assert to_str(None) is None


def test_to_str_non_str_raises():
    with pytest.raises(TypeError):
        to_str(5)


def test_to_bool_native_and_numpy():
    assert to_bool(True) is True
    assert to_bool(np.bool_(False)) is False


def test_to_bool_zero_one_ints():
    assert to_bool(1) is True
    assert to_bool(0) is False


def test_to_bool_other_int_raises():
    with pytest.raises(TypeError):
        to_bool(2)


def test_to_bool_strings():
    assert to_bool("1") is True
    assert to_bool("true") is True
    assert to_bool("YES") is True
    assert to_bool("0") is False
    assert to_bool("False") is False
    assert to_bool("no") is False


def test_to_bool_empty_string_is_null():
    assert to_bool("") is None
    assert to_bool("  ") is None


def test_to_bool_unknown_string_raises():
    with pytest.raises(TypeError):
        to_bool("maybe")


def test_to_bool_float_raises():
    with pytest.raises(TypeError):
        to_bool(1.0)


def test_to_date_pandas_timestamp():
    assert to_date(pd.Timestamp("2024-05-01 10:30")) == date(2024, 5, 1)


def test_to_date_nat_is_null():
    assert to_date(pd.NaT) is None
    assert to_date(np.datetime64("NaT")) is None
    assert to_date(float("nan")) is None


def test_to_date_numpy_datetime64():
    assert to_date(np.datetime64("2024-05-01")) == date(2024, 5, 1)


def test_to_date_datetime_and_date():
    assert to_date(datetime(2024, 5, 1, 9, 15)) == date(2024, 5, 1)
    assert to_date(date(2024, 5, 1)) == date(2024, 5, 1)


def test_to_date_iso_strings():
    assert to_date("2024-05-01") == date(2024, 5, 1)
    assert to_date(" 2024-05-01T12:30:00 ") == date(2024, 5, 1)


def test_to_date_empty_string_is_null():
    assert to_date("") is None


def test_to_date_non_iso_string_raises():
    with pytest.raises(ValueError):
        to_date("05/01/2024")


def test_to_date_number_raises():
    with pytest.raises(TypeError):
        to_date(20240501)


def test_to_utc_datetime_converts_offset_to_utc():
    eastern = datetime.fromisoformat("2026-06-11T21:59:17-04:00")
    converted = to_utc_datetime(eastern)
    assert converted is not None
    assert converted.isoformat() == "2026-06-12T01:59:17+00:00"


def test_to_utc_datetime_pandas_timestamp():
    ts = pd.Timestamp("2026-06-11T21:59:17-04:00")
    converted = to_utc_datetime(ts)
    assert converted is not None
    assert converted.isoformat() == "2026-06-12T01:59:17+00:00"


def test_to_utc_datetime_none_and_nat_are_null():
    assert to_utc_datetime(None) is None
    assert to_utc_datetime(pd.NaT) is None


def test_to_utc_datetime_naive_raises():
    with pytest.raises(ValueError, match="naive datetime"):
        to_utc_datetime(datetime(2026, 6, 11, 21, 59, 17))


def test_to_utc_datetime_date_raises():
    with pytest.raises(TypeError):
        to_utc_datetime(date(2026, 6, 11))


def test_eastern_naive_to_utc_winter_is_est():
    converted = eastern_naive_to_utc(datetime(2025, 1, 10, 7, 15, 33))
    assert converted is not None
    assert converted.isoformat() == "2025-01-10T12:15:33+00:00"


def test_eastern_naive_to_utc_summer_is_edt():
    converted = eastern_naive_to_utc(datetime(2025, 7, 10, 7, 15, 33))
    assert converted is not None
    assert converted.isoformat() == "2025-07-10T11:15:33+00:00"


def test_eastern_naive_to_utc_none_is_null():
    assert eastern_naive_to_utc(None) is None


def test_eastern_naive_to_utc_aware_raises():
    with pytest.raises(ValueError, match="aware datetime"):
        eastern_naive_to_utc(datetime.fromisoformat("2025-01-10T07:15:33-05:00"))


def test_eastern_naive_to_utc_date_raises():
    with pytest.raises(TypeError):
        eastern_naive_to_utc(date(2025, 1, 10))


def test_utc_naive_to_utc_attaches_utc():
    converted = utc_naive_to_utc(datetime(2025, 1, 8, 18, 4, 6))
    assert converted is not None
    assert converted.isoformat() == "2025-01-08T18:04:06+00:00"


def test_utc_naive_to_utc_normalizes_aware():
    converted = utc_naive_to_utc(datetime.fromisoformat("2025-01-08T13:04:06-05:00"))
    assert converted is not None
    assert converted.isoformat() == "2025-01-08T18:04:06+00:00"


def test_utc_naive_to_utc_none_is_null():
    assert utc_naive_to_utc(None) is None


def test_utc_naive_to_utc_date_raises():
    with pytest.raises(TypeError):
        utc_naive_to_utc(date(2025, 1, 8))


# date/datetime coercers must fail LOUDLY on garbage -- never a silent None, never an opaque crash.


def test_to_date_iso_shaped_but_invalid_calendar_raises():
    with pytest.raises(ValueError, match="month must be in 1..12"):
        to_date("2024-13-01")
    with pytest.raises(ValueError, match="day is out of range"):
        to_date("2024-02-30")


def test_to_date_bytes_raises_typed():
    with pytest.raises(TypeError, match="cannot coerce bytes to date"):
        to_date(b"2024-05-01")


def test_to_date_collection_raises_typed():
    with pytest.raises(TypeError, match="cannot coerce list to date"):
        to_date(["2024-05-01"])
    with pytest.raises(TypeError, match="cannot coerce dict to date"):
        to_date({"date": "2024-05-01"})


def test_to_date_bool_raises_typed():
    with pytest.raises(TypeError, match="cannot coerce bool to date"):
        to_date(True)


def test_to_utc_datetime_string_raises_typed():
    # the coercer parses datetimes, not strings; a date-shaped string is a caller error, not None
    with pytest.raises(TypeError, match="cannot coerce str to UTC datetime"):
        to_utc_datetime("2026-06-12T00:00:00Z")


def test_to_utc_datetime_epoch_int_raises_typed():
    with pytest.raises(TypeError, match="cannot coerce int to UTC datetime"):
        to_utc_datetime(1700000000)


def test_eastern_naive_to_utc_string_raises_typed():
    with pytest.raises(TypeError, match="cannot coerce str to UTC datetime"):
        eastern_naive_to_utc("2025-01-10T07:15:33")


def test_utc_naive_to_utc_garbage_raises_typed():
    with pytest.raises(TypeError, match="cannot coerce str to UTC datetime"):
        utc_naive_to_utc("2025-01-08T18:04:06")
    with pytest.raises(TypeError, match="cannot coerce bytes to UTC datetime"):
        utc_naive_to_utc(b"x")
