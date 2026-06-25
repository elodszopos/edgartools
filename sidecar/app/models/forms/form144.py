"""Form 144 typed envelope data (U49): a Rule 144 notice of PROPOSED sale of restricted/control
securities. One `Form144` object backs 144 and 144/A -> one kind (`form144`); `form` is the variant.

`data` is the AS-FILED notice: the issuer identity, the person selling + their relationship to the
issuer, and the three XML tables -- securities information (what's being sold), how those securities
were acquired, and any sales in the past 3 months -- plus the notice signature (10b5-1 plan adoption
dates). edgartools' analytical layer (totals, percentages, holding-period math, 10b5-1 inference,
anomaly flags) is included alongside the raw rows -- useful computed metrics from the parsed data.
Date fields are kept as filed (MM/DD/YYYY free-text strings, including the form's 1933 placeholder
dates), NOT ISO-coerced -- the form permits partial/placeholder dates and edgar stores them raw.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.models.common import CIK_PATTERN, Address, WireModel


class Form144Filer(WireModel):
    """Filer credentials from the form's own headerData (distinct from the SGML cover header)."""

    cik: str | None = Field(pattern=CIK_PATTERN)
    name: str | None
    file_number: str | None


class Form144Contact(WireModel):
    name: str | None
    phone: str | None
    email: str | None


class Form144SecurityInfo(WireModel):
    """One <securitiesInformation> row: a class of securities proposed for sale + its broker/venue."""

    security_class: str | None
    units_to_be_sold: int | None
    market_value: float | None  # aggregateMarketValue; null when the filer left it blank
    units_outstanding: int | None
    approx_sale_date: str | None  # as-filed MM/DD/YYYY (free-text), not ISO
    exchange_name: str | None
    broker_name: str | None
    broker_address: Address | None  # broker-of-record address


class Form144AcquisitionDetail(WireModel):
    """One <securitiesToBeSold> row: how the to-be-sold securities were originally acquired."""

    security_class: str | None
    acquired_date: str | None  # as-filed MM/DD/YYYY; '01/01/1933' is the form's placeholder default
    amount_acquired: int | None
    nature_of_acquisition: str | None
    acquired_from: str | None
    nature_of_payment: str | None
    is_gift: str | None  # 'Y'/'N' as filed
    donor_acquired_date: str | None  # as-filed MM/DD/YYYY (edgar tag is misspelled 'donar')
    payment_date: str | None  # as-filed MM/DD/YYYY


class Form144PriorSale(WireModel):
    """One <securitiesSoldInPast3Months> row: a prior Rule 144 sale by the same seller."""

    security_class: str | None
    seller_name: str | None
    sale_date: str | None  # as-filed MM/DD/YYYY
    amount_sold: int | None
    gross_proceeds: float | None
    seller_address: Address | None  # the prior seller's address


class Form144Signature(WireModel):
    notice_date: str | None  # as-filed MM/DD/YYYY
    plan_adoption_dates: list[str]  # 10b5-1 plan adoption dates as filed; '..1933' entries are placeholders
    signature: str | None


class Form144Data(WireModel):
    kind: Literal["form144"] = "form144"
    form: str  # "144" | "144/A"
    is_amendment: bool
    filing_date: str | None
    # issuer of the securities (the company whose stock is being sold) -- distinct from the filer
    issuer_cik: str | None = Field(pattern=CIK_PATTERN)
    issuer_name: str | None
    sec_file_number: str | None
    issuer_contact_phone: str | None
    issuer_address: Address | None
    # the person/account for whom the securities are to be sold + their tie to the issuer
    person_selling: str | None
    relationships: list[str]  # e.g. ["Officer", "Director"]
    # filer credentials + filing contact from the form's headerData
    filer: Form144Filer | None
    contact: Form144Contact | None
    # the three as-filed tables (rows kept disaggregated)
    securities_information: list[Form144SecurityInfo]
    securities_to_be_sold: list[Form144AcquisitionDetail]
    securities_sold_past_3_months: list[Form144PriorSale]
    nothing_to_report: bool  # true when the filer flagged no sales in the past 3 months
    remarks: str | None
    notice_signature: Form144Signature | None
    # aggregation scalars from edgar's analytical layer
    num_securities: int | None
    is_multi_security: bool
    total_units_to_be_sold: int | None
    total_market_value: float | None
    total_amount_acquired: int | None
    total_amount_sold_past_3_months: int | None
    total_gross_proceeds_past_3_months: float | None
    avg_price_per_unit: float | None
    percent_of_holdings: float | None
    # single-security convenience accessors (first row when multi-security)
    units_to_be_sold: int | None
    market_value: float | None
    approx_sale_date: str | None  # as-filed MM/DD/YYYY from first security row
    security_class: str | None
    broker_name: str | None
    exchange_name: str | None
    # holding-period analytics
    holding_period_days: int | None
    holding_period_years: float | None
    # 10b5-1 plan and compliance
    is_10b5_1_plan: bool
    has_multiple_plans: bool
    days_since_plan_adoption: int | None
    cooling_off_compliant: bool | None
    # anomaly detection
    is_short_hold: bool
    is_large_liquidation: bool
    anomaly_flags: list[str]
