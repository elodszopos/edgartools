"""ttm_convenience maps each TTM failure to a distinct wire reason,
and the wire reason literal stays a superset of the sidecar's classification."""

from __future__ import annotations

from datetime import date
from typing import get_args

from edgar.ttm.calculator import TTMMetric

from app.models.financials import TTMUnavailable
from app.ttm import TTMUnavailableReason, ttm_convenience


def _raise(exc: Exception):
    def compute():
        raise exc

    return compute


def test_concept_absent_is_distinct_from_insufficient() -> None:
    absent = ttm_convenience(_raise(KeyError("no revenue concept")))
    assert absent.metric is None
    assert absent.unavailable_reason == "concept_absent"

    insufficient = ttm_convenience(_raise(ValueError("found 2 quarters, need 4")))
    assert insufficient.metric is None
    assert insufficient.unavailable_reason == "insufficient_quarters"

    assert absent.unavailable_reason != insufficient.unavailable_reason


def test_malformed_metric_is_classified_not_raised() -> None:
    # non-finite value makes ttm_metric_model raise TypeError; convenience pair
    # must classify it, not propagate as a 500
    malformed = TTMMetric(
        concept="us-gaap:Revenue",
        label="Revenue",
        value=float("nan"),
        unit="USD",
        as_of_date=date(2025, 3, 31),
        periods=[],
        period_facts=[],
        has_gaps=False,
    )
    result = ttm_convenience(lambda: malformed)
    assert result.metric is None
    assert result.unavailable_reason == "malformed"


def test_unexpected_error_is_not_swallowed() -> None:
    class BoomError(RuntimeError):
        pass

    try:
        ttm_convenience(_raise(BoomError("unexpected")))
    except BoomError:
        return
    raise AssertionError("ttm_convenience swallowed an unexpected error")


def test_library_reasons_are_wire_representable() -> None:
    # if a reason is added that the wire literal can't express, responses would 500
    library_values = {reason.value for reason in TTMUnavailableReason}
    wire_values = set(get_args(TTMUnavailable))
    assert library_values <= wire_values, f"unrepresentable TTM reasons: {library_values - wire_values}"
