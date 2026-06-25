"""Form C typed envelope data (U51): a Regulation Crowdfunding offering filing under Section 4(a)(6).
One `FormC` object backs every variant (C, C/A, C-U, C-U/A, C-AR, C-AR/A, C-TR) -> one kind (`formc`);
`form` is the variant. The structure varies by variant: the offering block and funding portal are
present for the offering forms (C / C/A / C-U) and null for the annual report (C-AR) and termination
(C-TR); the annual-report disclosure is present for the offering forms AND C-AR, null for C-TR.

`data` is the as-filed crowdfunding record: the filer/issuer identity, the funding portal, the offering
terms (compensation, security, target/maximum amounts, deadline, over-subscription), the annual-report
financials (two fiscal years of assets / cash / debt / revenue / net income plus headcount and the
offering jurisdictions), and the signature block. Offering amounts arrive as floats (edgar coerces a
blank to 0.0, so a missing target reads 0.0, not null); other amounts/counts are as-filed strings.

The filer block carries the filer identity, the CCC submission credential (the SEC masks it to
"XXXXXXXX" in every public filing), the LIVE/TEST submission flag, the confirming/return/override
copy-routing flags, and the report period (present on the annual report C-AR, else null).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field

from app.models.common import CIK_PATTERN, Address, WireModel


class FormCFilerInfo(WireModel):
    """headerData/filerInfo: the filer identity + CCC submission credential + routing flags + period."""

    cik: str | None = Field(pattern=CIK_PATTERN)
    ccc: str | None  # CCC submission credential; SEC masks it to "XXXXXXXX" in public filings
    live_or_test: bool  # True = LIVE submission, False = TEST
    confirming_copy_flag: bool
    return_copy_flag: bool
    override_internet_flag: bool
    period: date | None  # report period; present for the annual report (C-AR), else null


class FormCFundingPortal(WireModel):
    """The intermediary (registered funding portal / broker) hosting the raise. Null for C-AR/C-TR."""

    name: str | None
    cik: str | None = Field(pattern=CIK_PATTERN)
    crd: str | None
    file_number: str | None  # the PORTAL's commission file number (e.g. "007-00033"), not the offering's


class FormCIssuer(WireModel):
    """issuerInformation: the company raising capital."""

    name: str | None
    legal_status: str | None  # e.g. "Corporation", "Limited Liability Company"
    jurisdiction: str | None  # state/country of organization, e.g. "DE", "CA"
    date_of_incorporation: date | None
    website: str | None
    co_issuer: bool
    address: Address | None
    funding_portal: FormCFundingPortal | None


class FormCOffering(WireModel):
    """offeringInformation: the terms of the crowdfunding offering. Null for C-AR and C-TR.

    `offering_amount` / `maximum_offering_amount` are floats: edgar coerces a blank to 0.0, so a
    missing target reads 0.0 (not null). The remaining amounts/counts are kept as-filed strings."""

    compensation_amount: str | None
    financial_interest: str | None
    security_offered_type: str | None  # e.g. "Common Stock", "Preferred Stock", "Other"
    security_offered_other_desc: str | None  # free-text when security_offered_type is "Other"
    no_of_security_offered: str | None  # as-filed count string
    price: str | None  # as-filed per-security price string
    price_determination_method: str | None
    offering_amount: float | None  # target raise; 0.0 when filed blank (edgar coerces)
    over_subscription_accepted: str | None  # "Y" / "N"
    over_subscription_allocation_type: str | None
    desc_over_subscription: str | None
    maximum_offering_amount: float | None  # maximum raise; 0.0 when filed blank (edgar coerces)
    deadline_date: date | None


class FormCAnnualReport(WireModel):
    """annualReportDisclosureRequirements: headcount + two fiscal years of financials + jurisdictions.
    Present for the offering forms and C-AR; null for C-TR. edgar coerces blank financials to 0.0.

    Field names mirror edgar's exactly (1:1 with the converter) - the `_most_recent_fiscal_year` /
    `_prior_fiscal_year` pairs are the current and previous fiscal year as filed."""

    current_employees: int
    total_asset_most_recent_fiscal_year: float
    total_asset_prior_fiscal_year: float
    cash_equi_most_recent_fiscal_year: float
    cash_equi_prior_fiscal_year: float
    act_received_most_recent_fiscal_year: float
    act_received_prior_fiscal_year: float
    short_term_debt_most_recent_fiscal_year: float
    short_term_debt_prior_fiscal_year: float
    long_term_debt_most_recent_fiscal_year: float
    long_term_debt_prior_fiscal_year: float
    revenue_most_recent_fiscal_year: float
    revenue_prior_fiscal_year: float
    cost_goods_sold_most_recent_fiscal_year: float
    cost_goods_sold_prior_fiscal_year: float
    tax_paid_most_recent_fiscal_year: float
    tax_paid_prior_fiscal_year: float
    net_income_most_recent_fiscal_year: float
    net_income_prior_fiscal_year: float
    offering_jurisdictions: list[str]  # state codes the securities are offered in


class FormCPersonSignature(WireModel):
    """One person signature line (signaturePersons)."""

    signature: str | None
    title: str | None
    date: date | None


class FormCIssuerSignature(WireModel):
    """The issuer's signature block (issuerSignature)."""

    issuer: str | None
    title: str | None
    signature: str | None


class FormCSignatureInfo(WireModel):
    """signatureInfo: the issuer signature plus the individual signer lines.

    edgar's derived `signers` (dedup of names -> their titles) is not on the wire; it is recomputable
    from `signatures` + `issuer_signature`."""

    issuer_signature: FormCIssuerSignature
    signatures: list[FormCPersonSignature]


class FormCData(WireModel):
    kind: Literal["formc"] = "formc"
    form: str  # the variant: C | C/A | C-U | C-U/A | C-AR | C-AR/A | C-TR (FormC exposes `form` directly)
    filer: FormCFilerInfo
    issuer: FormCIssuer
    offering: FormCOffering | None  # null for C-AR and C-TR
    annual_report: FormCAnnualReport | None  # null for C-TR
    signatures: FormCSignatureInfo
    # convenience accessors (delegate to nested filer/issuer/offering objects)
    issuer_cik: str | None = Field(default=None, pattern=CIK_PATTERN)
    issuer_name: str | None = None
    portal_cik: str | None = Field(default=None, pattern=CIK_PATTERN)
    portal_name: str | None = None
    portal_file_number: str | None = None
    description: str | None = None
    campaign_status: str | None = None
    days_to_deadline: int | None = None
    is_expired: bool | None = None
