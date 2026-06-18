"""U57c wire models: N-CSR / N-CSRS (+/A) certified fund shareholder report -> kind=ncsr.

N-CSR (annual) and N-CSRS (semi-annual) are the certified shareholder reports filed by registered
investment companies. UNLIKE the other fund forms (NPORT / N-MFP / N-CEN, all lxml zero-XBRL), N-CSR
carries Inline XBRL in the Open-End-Fund (`oef:`) taxonomy -- edgar's FundShareholderReport builds
itself from `filing.xbrl()` via the FactQuery API. Only OPEN-END funds (mutual funds / ETFs) carry
this taxonomy; closed-end funds / BDCs file N-CSR with no oef XBRL -> from_filing returns None -> the
envelope serves data=null.

A single N-CSR routinely covers a WHOLE TRUST -- several funds (SEC "series"), each with its own net
assets, turnover, advisory fee and share classes. edgar groups the XBRL facts under each series via the
SGML header (the XBRL carries only an oef:ClassAxis, no series dimension), so this mirror is per-fund:
`funds[]` (one NcsrFund per series), each with the fund-level figures and its `share_classes[]`. The
DataFrame views (fund_data / performance_data / expense_data / holdings_data) and derived scalars
(is_annual / num_funds / num_share_classes / cik) are NOT wire fields -- their data IS these typed
records; see the parity gate.

Value policy: every Decimal -> float|None; holdings_count -> int|None; all ids / names / tickers as-filed
text from the SGML class registry. Identity (series_id / fund_name / class_id / class_name / class_ticker)
is authoritative SGML; the figures are the grouped oef facts. holdings[] is typically empty
(oef:HoldingPctOfNav absent) while holdings_count is populated; each annual_returns[] entry is one
(horizon, sales-load) cell -- period_start carries the horizon, without_sales_load the load treatment.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import WireModel


class NcsrAnnualReturn(WireModel):
    # one (horizon, sales-load) cell. period_start distinguishes the horizon (1yr/5yr/10yr); a load
    # class reports each horizon twice -- standardized max-load and supplemental without-load -- so
    # neither the [start, end] span nor the load flag alone is unique.
    period_start: str | None  # horizon start (as-filed); 1yr/5yr/10yr differ only here
    period_end: str | None  # period end (the report/fiscal date)
    return_pct: float | None
    without_sales_load: bool  # True = oef:WithoutSalesLoadMember; False = standardized max-load return


class NcsrHolding(WireModel):
    name: str | None
    pct_of_nav: float | None
    pct_of_total_inv: float | None  # edgar Decimal field the oef parser never fills -> typically null


class NcsrShareClass(WireModel):
    class_id: str | None  # SEC class-contract id (C000...) from the SGML class registry
    class_name: str | None
    class_ticker: str | None
    expense_ratio_pct: float | None
    expenses_paid_amt: float | None
    annual_returns: list[NcsrAnnualReturn]


class NcsrFund(WireModel):
    series_id: str | None  # SEC series id (S000...) from the SGML class registry
    fund_name: str | None
    net_assets: float | None
    portfolio_turnover: float | None
    advisory_fees_paid: float | None  # fund-level (the oef taxonomy repeats it on each class)
    holdings_count: int | None
    holdings: list[NcsrHolding]
    share_classes: list[NcsrShareClass]


class NcsrData(WireModel):
    kind: Literal["ncsr"] = "ncsr"
    form: str | None
    cik: str | None
    fund_name: str | None
    series_id: str | None
    net_assets: float | None
    portfolio_turnover: float | None
    report_type: str | None  # "Annual" (N-CSR) | "Semi-Annual" (N-CSRS)
    is_annual: bool  # report_type == "Annual"
    num_share_classes: int  # total share classes across all funds
    funds: list[NcsrFund]
    share_classes: list[NcsrShareClass]
