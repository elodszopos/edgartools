"""Form D typed envelope data (U50): a Regulation D / Section 4(a)(5) notice of an EXEMPT offering
of securities (private placement). One `FormD` object backs D and D/A -> one kind (`formd`);
`submission_type` is the variant ("D" | "D/A").

`data` is the as-filed notice: the primary issuer's identity, the related persons (executives /
promoters / control persons), the full offering block (industry, exemptions, security type, amounts,
investors, sales compensation, use of proceeds), and the signature block. Dollar amounts and investor
counts are kept as filed (free-text strings, e.g. "Indefinite" for an open-ended offering), NOT
coerced -- Form D permits non-numeric placeholders. Dates are kept as filed (the form's dates are ISO
YYYY-MM-DD but may carry placeholders).

A sales-compensation recipient carries the recipient identity (name + CRD), the associated
broker-dealer (name + CRD; name is null when filed empty), the address, the foreignSolicitation flag
(null when absent), and the states of solicitation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.models.common import CIK_PATTERN, Address, WireModel


class FormDIssuer(WireModel):
    """The entity raising capital (primaryIssuer). Distinct from the SGML cover header."""

    cik: str | None = Field(pattern=CIK_PATTERN)
    entity_name: str | None
    entity_type: str | None  # e.g. "Limited Liability Company", "Corporation"
    primary_address: Address | None
    phone_number: str | None
    jurisdiction: str | None  # jurisdictionOfInc, e.g. "DELAWARE"
    issuer_previous_names: list[str]
    edgar_previous_names: list[str]
    year_of_incorporation: str | None  # as-filed (yearOfInc/value); may be "Over Five Years Ago"
    incorporated_within_5_years: bool | None  # null when the yearOfInc block is absent


class FormDPerson(WireModel):
    """One relatedPersonInfo: an executive officer, director, or promoter of the issuer."""

    first_name: str | None
    middle_name: str | None
    last_name: str | None
    address: Address | None
    relationships: list[str]  # roles held: "Executive Officer" / "Director" / "Promoter" (a person can hold several)
    relationship_clarification: str | None  # free-text clarification of the role; null when filed empty


class FormDInvestmentFundInfo(WireModel):
    investment_fund_type: str | None
    is_40_act: bool  # registered under the Investment Company Act of 1940


class FormDIndustryGroup(WireModel):
    industry_group_type: str | None  # e.g. "Pooled Investment Fund", "Technology"
    investment_fund_info: FormDInvestmentFundInfo | None  # present only for fund issuers


class FormDBusinessCombination(WireModel):
    is_business_combination: bool
    clarification_of_response: str | None


class FormDOfferingSalesAmounts(WireModel):
    # dollar amounts as filed; "Indefinite" is a valid totalOfferingAmount for open-ended offerings
    total_offering_amount: str | None
    total_amount_sold: str | None
    total_remaining: str | None
    clarification_of_response: str | None


class FormDInvestors(WireModel):
    has_non_accredited_investors: bool
    total_already_invested: str | None  # count of investors already participating, as filed


class FormDSalesCommissionFindersFees(WireModel):
    sales_commission: str | None  # dollar amount as filed
    finders_fees: str | None  # dollar amount as filed
    clarification_of_response: str | None


class FormDUseOfProceeds(WireModel):
    gross_proceeds_used: str | None  # dollar amount paid to executives/directors/promoters, as filed
    clarification_of_response: str | None


class FormDSalesCompensationRecipient(WireModel):
    """One salesCompensationList/recipient: a broker-dealer or person paid to solicit the offering."""

    name: str | None
    crd: str | None  # recipient CRD number
    associated_bd_name: str | None  # associated broker-dealer name; null when filed empty
    associated_bd_crd: str | None  # associated broker-dealer CRD
    address: Address | None
    foreign_solicitation: bool | None  # solicited foreign investors; null when the flag is absent
    states_of_solicitation: list[str]  # state codes; may include free-text values like "All States"


class FormDSignature(WireModel):
    issuer_name: str | None
    signature_name: str | None
    name_of_signer: str | None
    title: str | None
    date: str | None  # as-filed signatureDate


class FormDSignatureBlock(WireModel):
    authorized_representative: bool
    signatures: list[FormDSignature]


class FormDOffering(WireModel):
    """The offeringData block: everything about the exempt offering itself."""

    industry_group: FormDIndustryGroup | None
    revenue_range: str | None  # issuerSize/revenueRange bucket, as filed
    federal_exemptions: list[str]  # claimed Reg D rules, e.g. ["06b", "3C.1"]
    # edgar's OfferingData.is_new attribute holds the <isAmendment> XML flag (its name is INVERTED);
    # captured here under its true meaning. null when the newOrAmendment block is absent.
    is_amendment: bool | None
    date_of_first_sale: str | None  # as-filed (ISO date or "Yet to Occur" placeholder)
    more_than_one_year: bool | None  # offering intended to last over a year; null when block absent
    is_equity: bool
    is_pooled_investment: bool
    business_combination: FormDBusinessCombination | None
    minimum_investment: str | None  # minimum outside-investor acceptance amount, as filed
    sales_compensation_recipients: list[FormDSalesCompensationRecipient]
    offering_sales_amounts: FormDOfferingSalesAmounts | None
    investors: FormDInvestors | None
    sales_commission_finders_fees: FormDSalesCommissionFindersFees | None
    use_of_proceeds: FormDUseOfProceeds | None


class FormDData(WireModel):
    kind: Literal["formd"] = "formd"
    submission_type: str  # "D" | "D/A" (the form variant; FormD exposes no separate `form`)
    is_live: bool  # testOrLive == "LIVE" (a TEST filing is a non-production submission)
    primary_issuer: FormDIssuer | None
    # co-issuers from issuerList; [] for a single-issuer offering. A multi-issuer offering carries
    # every co-issuer here -- never collapsed into primary_issuer.
    additional_issuers: list[FormDIssuer]
    related_persons: list[FormDPerson]
    offering: FormDOffering
    signatures: FormDSignatureBlock | None
    is_new: bool  # True when not an amendment (proxies offering_data.is_new)
