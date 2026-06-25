"""U57b wire models: N-CEN (+/A) annual fund census over one `FundCensus` -> kind=ncen.

N-CEN is the yearly operational census for registered investment companies: registrant identity +
governance (directors, CCO, accountant, underwriter), then a per-series tree of service providers
(advisers/custodians/transfer agents/admins/pricing/shareholder-servicing), broker-dealers + brokers,
principal transactions, securities-lending agents, a line of credit, liquidity classification
services, and -- for exchange-traded series -- ETF mechanics with authorized participants.

Full-fidelity mirror of edgar.funds.ncen.FundCensus's five stored structures (report_date,
is_period_lt_12_months, registrant, series[], signature_info). The DataFrame-view methods
(series_data / service_providers / broker_data / director_data / etf_data) and the derived scalars
(name / cik / lei / series_id(s) / num_series / total_series / classification_type / is_etf_company)
are NOT wire fields -- their data IS these typed records; see the parity gate.

Value policy: every Decimal -> float|None; total_series -> int|None; all dates/ids/names as-filed text.
Always-present "Y"/"N" flags are non-nullable bool; is_diversified is genuine tri-state (bool|None,
null when the diversification flag is absent). A line of credit carries a LIST of facilities (a fund
routinely files a committed plus an uncommitted facility); per-facility `is_committed` is as-filed
text (str), NOT a bool, despite the name. Share classes (id/name/ticker) come from the SGML header's
class-contract block, joined per series.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import WireModel

# --- governance / people ----------------------------------------------------


class NcenDirector(WireModel):
    name: str | None
    crd_number: str | None
    is_interested_person: bool


class NcenAccountant(WireModel):
    name: str | None
    pcaob_number: str | None
    lei: str | None


# --- per-series service providers -------------------------------------------


class NcenServiceProvider(WireModel):
    name: str | None
    role: str | None  # fixed role label (adviser/custodian/transfer agent/...)
    lei: str | None
    file_number: str | None
    crd_number: str | None
    is_affiliated: bool


class NcenBrokerDealer(WireModel):
    name: str | None
    file_number: str | None
    crd_number: str | None
    lei: str | None
    commission: float | None


class NcenPrincipalTransaction(WireModel):
    name: str | None
    file_number: str | None
    crd_number: str | None
    total_purchase_sale: float | None


class NcenSecuritiesLending(WireModel):
    agent_name: str | None
    agent_lei: str | None
    is_affiliated: bool
    is_indemnified: bool


class NcenLineOfCreditFacility(WireModel):
    is_committed: str | None  # as-filed text (isCreditLineCommitted), NOT a bool
    size: float | None
    institution_names: list[str]


class NcenLineOfCredit(WireModel):
    has_line_of_credit: bool
    facilities: list[NcenLineOfCreditFacility]  # a fund can file several (committed + uncommitted)


class NcenLiquidityProvider(WireModel):
    name: str | None
    lei: str | None
    is_affiliated: bool
    asset_classes: list[str]


# --- ETF mechanics ----------------------------------------------------------


class NcenAuthorizedParticipant(WireModel):
    name: str | None
    lei: str | None
    file_number: str | None
    crd_number: str | None
    purchase_value: float | None
    redeem_value: float | None


class NcenETFInfo(WireModel):
    series_id: str | None
    fund_name: str | None
    exchange: str | None
    ticker: str | None
    creation_unit_size: float | None
    avg_pct_purchased_in_kind: float | None
    avg_pct_redeemed_in_kind: float | None
    std_dev_purchased_in_kind: float | None
    std_dev_redeemed_in_kind: float | None
    is_in_kind: bool
    authorized_participants: list[NcenAuthorizedParticipant]


# --- per-series census ------------------------------------------------------


class NcenShareClass(WireModel):
    """Identity of one share class (from the SGML header's class-contract block)."""

    class_id: str | None
    class_name: str | None
    class_ticker: str | None


class NcenFundSeriesInfo(WireModel):
    name: str | None
    series_id: str | None
    lei: str | None
    fund_type: str | None
    is_diversified: bool | None  # tri-state: null when the diversification flag is absent
    avg_net_assets: float | None
    aggregate_commission: float | None
    is_securities_lending: bool
    advisers: list[NcenServiceProvider]
    custodians: list[NcenServiceProvider]
    transfer_agents: list[NcenServiceProvider]
    admins: list[NcenServiceProvider]
    pricing_services: list[NcenServiceProvider]
    shareholder_servicing_agents: list[NcenServiceProvider]
    broker_dealers: list[NcenBrokerDealer]
    brokers: list[NcenBrokerDealer]
    principal_transactions: list[NcenPrincipalTransaction]
    securities_lending: list[NcenSecuritiesLending]
    line_of_credit: NcenLineOfCredit | None
    liquidity_providers: list[NcenLiquidityProvider]
    etf_info: NcenETFInfo | None
    share_classes: list[NcenShareClass]


# --- registrant + signature -------------------------------------------------


class NcenRegistrantInfo(WireModel):
    name: str | None
    cik: str | None
    lei: str | None
    file_number: str | None
    street1: str | None
    street2: str | None
    city: str | None
    state: str | None
    country: str | None
    zip_code: str | None
    phone: str | None
    classification_type: str | None
    total_series: int | None
    directors: list[NcenDirector]
    cco_name: str | None
    cco_crd: str | None
    accountant: NcenAccountant | None
    underwriter_name: str | None


class NcenSignatureInfo(WireModel):
    registrant_name: str | None
    signed_date: str | None
    signer: str | None
    title: str | None


class NcenData(WireModel):
    kind: Literal["ncen"] = "ncen"
    form: str | None
    cik: str | None
    name: str | None
    series_id: str | None
    lei: str | None
    classification_type: str | None
    is_etf_company: bool
    num_series: int
    series_ids: list[str]
    total_series: int | None
    report_date: str | None  # as-filed text (reportEndingPeriod attribute)
    is_period_lt_12_months: bool
    registrant: NcenRegistrantInfo | None
    series: list[NcenFundSeriesInfo]
    signature_info: NcenSignatureInfo | None
