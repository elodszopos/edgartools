"""Nested wire models shared across the edgar offerings family (S-1/F-1, S-3 family, 424B family).

The edgar `RegistrationS1`, `RegistrationS3`, and `Prospectus424B` objects reuse one set of
pydantic BaseModels for the registration fee table, selling stockholders, underwriting, dilution,
and capitalization (all defined in `edgar.offerings.prospectus`). The wire mirrors live here once --
one OpenAPI component, one Zod type -- rather than being duplicated per form (the company_report.py
precedent). Form-specific nested models (e.g. the S-1-only `S1CoverPage`) stay in their form module.

Fidelity policy: mirror edgar's STORED fields 1:1 -- raw as-filed strings where edgar stores strings
(amounts with footnote markers, ranges, em-dashes), floats where edgar already parsed a number. The
derived numeric @property accessors on `SellingStockholderEntry` (shares_before/shares/...) are
computed views, not stored data, so they are not mirrored here (the converter exclusions on the
parent object cover the same rule for top-level convenience properties).
"""

from __future__ import annotations

from app.models.common import WireModel


class OfferingFeeSecurity(WireModel):
    """One security line of a registration fee table (Exhibit 107 EX-FILING FEES)."""

    security_type: str | None
    security_title: str | None
    fee_rule: str | None
    amount_registered: str | None  # as-filed string (shares/units, may carry footnote markers)
    price_per_unit: float | None
    max_aggregate_amount: float | None
    fee_rate: float | None
    fee_amount: float | None


class OfferingFeeTable(WireModel):
    """Parsed registration fee table -- total registered offering capacity + per-security breakdown."""

    total_offering_amount: float | None
    net_fee_due: float | None
    total_fees_previously_paid: float | None
    securities: list[OfferingFeeSecurity]
    carry_forwards: list[OfferingFeeSecurity]  # securities carried forward under Rule 415(a)(6)
    has_carry_forward: bool
    fee_deferred: bool  # Rule 456(b)/457(r) deferred-fee shelf (fee paid at takedown)
    exhibit_url: str | None


class OfferingSellingStockholder(WireModel):
    """One row of a selling-stockholders table (resale registrations); values as filed."""

    name: str
    shares_before_offering: str | None
    pct_before_offering: str | None
    shares_offered: str | None
    shares_after_offering: str | None
    pct_after_offering: str | None
    warrants_or_convertible: str | None


class OfferingSellingStockholders(WireModel):
    stockholders: list[OfferingSellingStockholder]
    total_shares_offered: str | None
    notes: str | None


class OfferingUnderwriter(WireModel):
    name: str
    shares_allocated: str | None
    dollar_amount: str | None


class OfferingUnderwriting(WireModel):
    underwriters: list[OfferingUnderwriter]
    fee_type: str  # edgar default "underwriting_discount"
    overallotment_shares: str | None
    overallotment_amount: str | None
    lock_up_days: int | None


class OfferingDilution(WireModel):
    """Per-share dilution disclosure (chiefly IPO S-1s); all values as-filed strings."""

    public_offering_price: str | None
    ntbv_before_offering: str | None  # net tangible book value
    ntbv_increase: str | None
    ntbv_after_offering: str | None
    dilution_per_share: str | None
    dilution_percentage: str | None
    shares_outstanding_before: str | None
    shares_outstanding_after: str | None


class OfferingCapitalization(WireModel):
    """Capitalization table (actual vs as-adjusted); `rows` is the full line-item table as filed."""

    rows: list[dict[str, str | None]]  # each row: {label, actual, as_adjusted?} cell strings
    cash_actual: str | None
    cash_as_adjusted: str | None
    total_stockholders_equity_actual: str | None
    total_stockholders_equity_as_adjusted: str | None
    total_capitalization_actual: str | None
    total_capitalization_as_adjusted: str | None
