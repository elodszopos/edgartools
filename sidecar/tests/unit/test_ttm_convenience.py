"""_ttm_convenience maps each TTM failure to a distinct wire reason (issue #21),
and the wire reason literal stays a superset of the library's classification."""

from __future__ import annotations

from datetime import date
from typing import get_args

from edgar.ttm import (
    TTMConceptNotFoundError,
    TTMInsufficientDataError,
    TTMUnavailableReason,
)
from edgar.ttm.calculator import TTMMetric

from app.models.financials import TTMUnavailable
from app.routers.financials import _ttm_convenience


def _raise(exc: Exception):
    def compute():
        raise exc

    return compute


def test_concept_absent_is_distinct_from_insufficient() -> None:
    # the two failures that used to both collapse to a bare null must now differ
    absent = _ttm_convenience(_raise(TTMConceptNotFoundError("no revenue concept")))
    assert absent.metric is None
    assert absent.unavailable_reason == "concept_absent"

    insufficient = _ttm_convenience(_raise(TTMInsufficientDataError("found 2 quarters, need 4")))
    assert insufficient.metric is None
    assert insufficient.unavailable_reason == "insufficient_quarters"

    assert absent.unavailable_reason != insufficient.unavailable_reason


def test_malformed_metric_is_classified_not_raised() -> None:
    # a non-finite value would make ttm_metric_model raise TypeError; the convenience
    # pair must classify it (issue #50: no 500), unlike the explicit ?concept= path
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
    result = _ttm_convenience(lambda: malformed)
    assert result.metric is None
    assert result.unavailable_reason == "malformed"


def test_unexpected_error_is_not_swallowed() -> None:
    # a bare error (library contract break) must surface, not masquerade as a reason
    class BoomError(RuntimeError):
        pass

    try:
        _ttm_convenience(_raise(BoomError("unexpected")))
    except BoomError:
        return
    raise AssertionError("_ttm_convenience swallowed an unexpected error")


def test_library_reasons_are_wire_representable() -> None:
    # if the library adds a reason the wire literal can't express, response construction
    # would 500 at runtime; fail loudly here instead
    library_values = {reason.value for reason in TTMUnavailableReason}
    wire_values = set(get_args(TTMUnavailable))
    assert library_values <= wire_values, f"unrepresentable library TTM reasons: {library_values - wire_values}"
