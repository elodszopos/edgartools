"""JSON scalar policy for everything that crosses the wire.

Policy (plan "Wire conventions"): numpy -> int/float, Decimal -> float, dates ->
datetime.date (pydantic renders ISO), NaN/NaT/inf -> None, DataFrames -> typed records
built by explicit field-by-field converters ONLY - no attribute walking, no generic
to_dict() dumps. Coercers are strict: unexpected types raise instead of guessing.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal

import numpy as np
import pandas as pd
from pandas.api.typing import NaTType

_TRUE_STRINGS = ("1", "true", "yes")
_FALSE_STRINGS = ("0", "false", "no")


def _is_missing(value: object) -> bool:
    if value is None or value is pd.NaT:
        return True
    if isinstance(value, (float, np.floating)) and math.isnan(float(value)):
        return True
    if isinstance(value, Decimal) and value.is_nan():
        return True
    if isinstance(value, np.datetime64) and bool(np.isnat(value)):
        return True
    return False


def to_int(value: object) -> int | None:
    if _is_missing(value):
        return None
    if isinstance(value, bool):
        raise TypeError(f"refusing bool -> int coercion: {value!r}")
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        as_float = float(value)
        if math.isinf(as_float):
            return None
        if as_float.is_integer():
            return int(as_float)
        raise TypeError(f"non-integral float cannot become int: {value!r}")
    if isinstance(value, Decimal):
        if value.is_infinite():
            return None
        if value == value.to_integral_value():
            return int(value)
        raise TypeError(f"non-integral Decimal cannot become int: {value!r}")
    raise TypeError(f"cannot coerce {type(value).__name__} to int: {value!r}")


def to_float(value: object) -> float | None:
    if _is_missing(value):
        return None
    if isinstance(value, bool):
        raise TypeError(f"refusing bool -> float coercion: {value!r}")
    if isinstance(value, (int, np.integer)):
        return float(value)
    if isinstance(value, (float, np.floating, Decimal)):
        as_float = float(value)
        return None if math.isinf(as_float) else as_float
    raise TypeError(f"cannot coerce {type(value).__name__} to float: {value!r}")


def to_str(value: object) -> str | None:
    if _is_missing(value):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    raise TypeError(f"cannot coerce {type(value).__name__} to str: {value!r}")


def to_bool(value: object) -> bool | None:
    if _is_missing(value):
        return None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        if int(value) in (0, 1):
            return bool(value)
        raise TypeError(f"cannot coerce int to bool: {value!r}")
    if isinstance(value, str):
        lowered = value.strip().lower()
        if not lowered:
            return None
        if lowered in _TRUE_STRINGS:
            return True
        if lowered in _FALSE_STRINGS:
            return False
        raise TypeError(f"cannot coerce str to bool: {value!r}")
    raise TypeError(f"cannot coerce {type(value).__name__} to bool: {value!r}")


def to_date(value: object) -> date | None:
    if _is_missing(value):
        return None
    # order matters: pd.Timestamp subclasses datetime, datetime subclasses date
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, np.datetime64):
        converted = pd.Timestamp(value)
        return None if isinstance(converted, NaTType) else converted.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return date.fromisoformat(stripped)
        except ValueError:
            return datetime.fromisoformat(stripped).date()
    raise TypeError(f"cannot coerce {type(value).__name__} to date: {value!r}")
