"""edgar offerings nested BaseModels -> shared wire models, explicit field-by-field.

These converters back the `RegistrationS1`/`RegistrationS3`/`Prospectus424B` table sections. Each
takes an `edgar.offerings.prospectus` BaseModel (or None when the section is absent from the filing)
and returns the wire mirror (or None). Raw as-filed strings pass through `to_str` (strip + ""->null);
already-numeric fee cells pass through `to_float`. No `vars()`/`getattr` loops.
"""

from __future__ import annotations

from typing import Any

from app.models.forms.offering import (
    OfferingCapitalization,
    OfferingDilution,
    OfferingFeeSecurity,
    OfferingFeeTable,
    OfferingSellingStockholder,
    OfferingSellingStockholders,
    OfferingUnderwriter,
    OfferingUnderwriting,
)
from app.serialize import to_float, to_int, to_str


def fee_security(sec: Any) -> OfferingFeeSecurity:
    return OfferingFeeSecurity(
        security_type=to_str(sec.security_type),
        security_title=to_str(sec.security_title),
        fee_rule=to_str(sec.fee_rule),
        amount_registered=to_str(sec.amount_registered),
        price_per_unit=to_float(sec.price_per_unit),
        max_aggregate_amount=to_float(sec.max_aggregate_amount),
        fee_rate=to_float(sec.fee_rate),
        fee_amount=to_float(sec.fee_amount),
    )


def fee_table(ft: Any) -> OfferingFeeTable | None:
    if ft is None:
        return None
    return OfferingFeeTable(
        total_offering_amount=to_float(ft.total_offering_amount),
        net_fee_due=to_float(ft.net_fee_due),
        total_fees_previously_paid=to_float(ft.total_fees_previously_paid),
        securities=[fee_security(s) for s in ft.securities],
        carry_forwards=[fee_security(s) for s in ft.carry_forwards],
        has_carry_forward=bool(ft.has_carry_forward),
        fee_deferred=bool(ft.fee_deferred),
        exhibit_url=to_str(ft.exhibit_url),
    )


def _selling_stockholder(entry: Any) -> OfferingSellingStockholder:
    return OfferingSellingStockholder(
        name=to_str(entry.name) or "",  # edgar requires name; never blank in practice
        shares_before_offering=to_str(entry.shares_before_offering),
        pct_before_offering=to_str(entry.pct_before_offering),
        shares_offered=to_str(entry.shares_offered),
        shares_after_offering=to_str(entry.shares_after_offering),
        pct_after_offering=to_str(entry.pct_after_offering),
        warrants_or_convertible=to_str(entry.warrants_or_convertible),
    )


def selling_stockholders(ssd: Any) -> OfferingSellingStockholders | None:
    if ssd is None:
        return None
    return OfferingSellingStockholders(
        stockholders=[_selling_stockholder(e) for e in ssd.stockholders],
        total_shares_offered=to_str(ssd.total_shares_offered),
        notes=to_str(ssd.notes),
    )


def _underwriter(entry: Any) -> OfferingUnderwriter:
    return OfferingUnderwriter(
        name=to_str(entry.name) or "",
        shares_allocated=to_str(entry.shares_allocated),
        dollar_amount=to_str(entry.dollar_amount),
    )


def underwriting(uw: Any) -> OfferingUnderwriting | None:
    if uw is None:
        return None
    return OfferingUnderwriting(
        underwriters=[_underwriter(e) for e in uw.underwriters],
        fee_type=to_str(uw.fee_type) or "",
        overallotment_shares=to_str(uw.overallotment_shares),
        overallotment_amount=to_str(uw.overallotment_amount),
        lock_up_days=to_int(uw.lock_up_days),
    )


def dilution(d: Any) -> OfferingDilution | None:
    if d is None:
        return None
    return OfferingDilution(
        public_offering_price=to_str(d.public_offering_price),
        ntbv_before_offering=to_str(d.ntbv_before_offering),
        ntbv_increase=to_str(d.ntbv_increase),
        ntbv_after_offering=to_str(d.ntbv_after_offering),
        dilution_per_share=to_str(d.dilution_per_share),
        dilution_percentage=to_str(d.dilution_percentage),
        shares_outstanding_before=to_str(d.shares_outstanding_before),
        shares_outstanding_after=to_str(d.shares_outstanding_after),
    )


def capitalization(c: Any) -> OfferingCapitalization | None:
    if c is None:
        return None
    return OfferingCapitalization(
        rows=[{k: to_str(v) for k, v in row.items()} for row in c.rows],
        cash_actual=to_str(c.cash_actual),
        cash_as_adjusted=to_str(c.cash_as_adjusted),
        total_stockholders_equity_actual=to_str(c.total_stockholders_equity_actual),
        total_stockholders_equity_as_adjusted=to_str(c.total_stockholders_equity_as_adjusted),
        total_capitalization_actual=to_str(c.total_capitalization_actual),
        total_capitalization_as_adjusted=to_str(c.total_capitalization_as_adjusted),
    )
