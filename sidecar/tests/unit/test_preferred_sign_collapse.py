"""Unit: sidecar preferred-sign collapse for stitched records.

Edgar's core no longer raises on per-period sign variance (that crashed /financials/multi).
The sidecar collapses a concept's per-period preferred_signs to one display sign and, when
periods/filings disagree, surfaces it as ambiguous (sign null) instead of crashing or
silently keeping an arbitrary first-seen pick.
"""

from __future__ import annotations

from app.converters.financials import _resolve_preferred_sign


def test_uniform_signs_collapse_to_single_value():
    assert _resolve_preferred_sign({"p1": -1.0, "p2": -1.0}) == (-1.0, False)


def test_single_period_returns_its_sign():
    assert _resolve_preferred_sign({"p1": 1.0}) == (1.0, False)


def test_empty_signs_is_none_not_ambiguous():
    assert _resolve_preferred_sign({}) == (None, False)


def test_none_period_values_are_ignored():
    assert _resolve_preferred_sign({"p1": None, "p2": -1.0}) == (-1.0, False)


def test_disagreeing_signs_are_ambiguous_and_sign_nulled():
    # the exact per-period variance the removed edgar guard raised on - now graceful
    assert _resolve_preferred_sign({"p1": 1.0, "p2": -1.0}) == (None, True)


def test_int_and_float_same_sign_not_ambiguous():
    # -1 and -1.0 are the same display sign; must not register as disagreement
    assert _resolve_preferred_sign({"p1": -1, "p2": -1.0}) == (-1.0, False)
