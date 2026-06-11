"""Unit tests for the JSON scalar policy (pure functions only)."""

from datetime import date, datetime
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from app.serialize import to_bool, to_date, to_float, to_int, to_str


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
