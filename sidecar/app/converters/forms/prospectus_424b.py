"""edgar `Prospectus424B` (424B family) -> `Prospectus424BData`, explicit field-by-field.

The cover page, pricing grid, offering terms, structured-note key terms, and XBRL filing-fee exhibit
are 424B-specific and built here; the selling-stockholders / underwriting / dilution / capitalization
legs delegate to the shared `offering.py` converter (same edgar BaseModels). All as-filed cells pass
through `to_str` (strip + ""->null); `additional_terms` keys/values are both extractor cell-text.
`offering_type` is the edgar OfferingType enum's `.value`. Convenience scalars (registration_number,
ticker, variant, offering_amount, offering_price, is_atm, is_preliminary, is_supplement) map from
the edgar object directly. Cross-entity lifecycle properties (lifecycle, shelf_registration,
related_filings, related_8k) are set to None -- they require cross-filing SEC fetches.
"""

from __future__ import annotations

from typing import Any

from edgar.offerings.prospectus import Prospectus424B

from app.converters.forms.offering import (
    capitalization,
    dilution,
    selling_stockholders,
    underwriting,
)
from app.models.forms.prospectus_424b import (
    Prospectus424BCoverPage,
    Prospectus424BData,
    Prospectus424BFilingFeeRow,
    Prospectus424BFilingFees,
    Prospectus424BOfferingTerms,
    Prospectus424BPricing,
    Prospectus424BPricingColumn,
    Prospectus424BStructuredNote,
)
from app.serialize import to_date, to_int, to_str


def _date_str(value: Any) -> str | None:
    if isinstance(value, str):
        return to_str(value)
    parsed = to_date(value)
    return parsed.isoformat() if parsed is not None else None


def _terms_dict(raw: dict[Any, Any] | None) -> dict[str, str | None]:
    # extractor keys/values are both cell-text strings; coerce defensively, drop nothing
    return {str(k): to_str(v) for k, v in (raw or {}).items()}


def _cover_page(cp: Any) -> Prospectus424BCoverPage:
    return Prospectus424BCoverPage(
        company_name=to_str(cp.company_name) or "",  # edgar requires it; never blank in practice
        registration_number=to_str(cp.registration_number),
        is_supplement=bool(cp.is_supplement),
        is_preliminary=bool(cp.is_preliminary),
        is_atm=bool(cp.is_atm),
        rule_number=to_str(cp.rule_number),
        security_description=to_str(cp.security_description),
        offering_amount=to_str(cp.offering_amount),
        offering_price=to_str(cp.offering_price),
        exchange_ticker=to_str(cp.exchange_ticker),
        base_prospectus_date=to_str(cp.base_prospectus_date),
    )


def _pricing_column(col: Any) -> Prospectus424BPricingColumn:
    return Prospectus424BPricingColumn(
        column_label=to_str(col.column_label),
        offering_price=to_str(col.offering_price),
        fee_or_discount=to_str(col.fee_or_discount),
        proceeds=to_str(col.proceeds),
    )


def _pricing(p: Any) -> Prospectus424BPricing | None:
    if p is None:
        return None
    return Prospectus424BPricing(
        columns=[_pricing_column(c) for c in p.columns],
        fee_type=to_str(p.fee_type),
        is_percentage_price=bool(p.is_percentage_price),
        raw_rows=[[to_str(cell) or "" for cell in row] for row in p.raw_rows],
    )


def _offering_terms(t: Any) -> Prospectus424BOfferingTerms | None:
    if t is None:
        return None
    return Prospectus424BOfferingTerms(
        shares_offered=to_str(t.shares_offered),
        pre_funded_warrants_offered=to_str(t.pre_funded_warrants_offered),
        warrants_offered=to_str(t.warrants_offered),
        use_of_proceeds_summary=to_str(t.use_of_proceeds_summary),
        trading_symbol=to_str(t.trading_symbol),
        listing_exchange=to_str(t.listing_exchange),
        additional_terms=_terms_dict(t.additional_terms),
    )


def _structured_note(s: Any) -> Prospectus424BStructuredNote | None:
    if s is None:
        return None
    return Prospectus424BStructuredNote(
        issuer=to_str(s.issuer),
        guarantor=to_str(s.guarantor),
        cusip=to_str(s.cusip),
        pricing_date=to_str(s.pricing_date),
        issue_date=to_str(s.issue_date),
        maturity_date=to_str(s.maturity_date),
        underlying=to_str(s.underlying),
        denominations=to_str(s.denominations),
        term=to_str(s.term),
        principal_amount=to_str(s.principal_amount),
        upside_participation_rate=to_str(s.upside_participation_rate),
        max_return=to_str(s.max_return),
        threshold_value=to_str(s.threshold_value),
        buffer_amount=to_str(s.buffer_amount),
        coupon_rate=to_str(s.coupon_rate),
        coupon_frequency=to_str(s.coupon_frequency),
        additional_terms=_terms_dict(s.additional_terms),
    )


def _filing_fee_row(r: Any) -> Prospectus424BFilingFeeRow:
    return Prospectus424BFilingFeeRow(
        security_type=to_str(r.security_type),
        security_title=to_str(r.security_title),
        max_aggregate_offering_price=to_str(r.max_aggregate_offering_price),
        fee_rate=to_str(r.fee_rate),
        fee_amount=to_str(r.fee_amount),
        fee_rule=to_str(r.fee_rule),
    )


def _filing_fees(ff: Any) -> Prospectus424BFilingFees:
    # edgar always returns a FilingFeesData (empty shell when no exhibit) -- never None
    return Prospectus424BFilingFees(
        has_exhibit=bool(ff.has_exhibit),
        exhibit_url=to_str(ff.exhibit_url),
        form_type=to_str(ff.form_type),
        registration_file_number=to_str(ff.registration_file_number),
        total_offering_amount=to_str(ff.total_offering_amount),
        total_fee_amount=to_str(ff.total_fee_amount),
        offering_rows=[_filing_fee_row(r) for r in ff.offering_rows],
        is_final_prospectus=bool(ff.is_final_prospectus),
    )


def prospectus_424b_data(obj: Prospectus424B) -> Prospectus424BData:
    return Prospectus424BData(
        form=obj.form,
        company=to_str(obj.company),
        filing_date=_date_str(obj.filing_date),
        accession_number=to_str(obj.accession_number),
        is_amendment=bool(obj.is_amendment),
        amendment_number=to_int(obj.amendment_number),
        offering_type=obj.offering_type.value,
        registration_number=to_str(obj.registration_number),
        ticker=to_str(obj.ticker),
        variant=to_str(obj.variant),
        offering_amount=to_str(obj.offering_amount),
        offering_price=to_str(obj.offering_price),
        is_atm=bool(obj.is_atm),
        is_preliminary=bool(obj.is_preliminary),
        is_supplement=bool(obj.is_supplement),
        cover_page=_cover_page(obj.cover_page),
        pricing=_pricing(obj.pricing),
        offering_terms=_offering_terms(obj.offering_terms),
        selling_stockholders=selling_stockholders(obj.selling_stockholders),
        structured_note_terms=_structured_note(obj.structured_note_terms),
        dilution=dilution(obj.dilution),
        capitalization=capitalization(obj.capitalization),
        underwriting=underwriting(obj.underwriting),
        filing_fees=_filing_fees(obj.filing_fees),
        related_filings=None,  # cross-entity fetch, served separately
        related_8k=None,  # cross-entity fetch, served separately
        shelf_registration=None,  # cross-entity fetch, served separately
        lifecycle=None,  # cross-entity fetch, served separately
    )
