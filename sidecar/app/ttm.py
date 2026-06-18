"""Convenience TTM failure -> wire reason classification (sidecar-owned).

edgar's get_ttm* raise native KeyError (no matching concept in the company facts) and
ValueError (fewer than 4 consecutive quarters). This module owns the sidecar's reason
enum and maps those native errors to a typed wire reason, so the convenience
revenue/net_income pair degrades to a reason instead of failing the whole response.
The explicit ?concept= path in the router fails loudly (404/502) instead.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING

from app.converters.financials import ttm_metric_model
from app.models.financials import TTMConvenienceMetric

if TYPE_CHECKING:
    from edgar.ttm.calculator import TTMMetric


class TTMUnavailableReason(str, Enum):
    """Why a convenience TTM is unavailable. The wire literal TTMUnavailable must stay a
    superset of these values; a unit test guards that."""

    CONCEPT_ABSENT = "concept_absent"  # no matching concept in company facts
    INSUFFICIENT_QUARTERS = "insufficient_quarters"  # fewer than 4 consecutive quarters
    MALFORMED = "malformed"  # non-finite value / unitless metric


def ttm_convenience(compute: Callable[[], TTMMetric]) -> TTMConvenienceMetric:
    """Convenience TTM (revenue/net_income): never fatal. A missing concept, insufficient
    quarters, or a metric the library returns malformed becomes a typed unavailable_reason
    rather than nulling out the reason or failing the whole response. An unexpected error
    (library contract break) is NOT swallowed - it propagates."""
    try:
        return TTMConvenienceMetric(metric=ttm_metric_model(compute()), unavailable_reason=None)
    except KeyError:  # native: concept absent from the company facts
        return TTMConvenienceMetric(metric=None, unavailable_reason=TTMUnavailableReason.CONCEPT_ABSENT.value)
    except ValueError:  # native: fewer than 4 consecutive quarters after quarterization
        return TTMConvenienceMetric(metric=None, unavailable_reason=TTMUnavailableReason.INSUFFICIENT_QUARTERS.value)
    except TypeError:  # non-finite/unitless metric -> classify as malformed, never 500
        return TTMConvenienceMetric(metric=None, unavailable_reason=TTMUnavailableReason.MALFORMED.value)
