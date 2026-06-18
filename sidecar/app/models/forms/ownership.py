"""Typed `data` for the SEC ownership forms (3/4/5).

`filing.obj()` returns the one edgar `Ownership` object for all three forms (Form3/4/5 are
thin subclasses), so they share this single model; the specific form is the `form` field.
Full fidelity: issuer, every reporting owner, the non-derivative/derivative holdings AND
transactions as typed rows, footnotes, signatures, remarks. The object's DataFrame-view
helpers (market_trades, derivative_trades, ...) are NOT mirrored - their rows are exactly
the typed records below.
"""

from __future__ import annotations

from typing import Literal

from app.models.common import Address, WireModel

# numeric cells are float when the whole column parsed numeric (convert_to_numeric), else the
# raw as-filed string (e.g. a footnote-only price), else null - mirrored faithfully, not forced
Amount = float | str | None


class OwnershipIssuer(WireModel):
    cik: str | None  # issuer CIK as filed (not zero-padded by edgar) -> no CIK_PATTERN
    name: str | None
    ticker: str | None


class ReportingOwner(WireModel):
    cik: str | None  # owner CIK as filed
    is_company: bool
    name: str  # display name: individuals reversed to "First Last"
    name_unreversed: str  # the as-filed conformed (LAST FIRST) name
    address: Address | None
    is_director: bool
    is_officer: bool
    is_other: bool
    is_ten_pct_owner: bool
    officer_title: str | None
    position: str  # derived display title, e.g. "Director, 10% Owner"


class NonDerivativeHolding(WireModel):
    security: str | None
    shares: Amount
    direct: bool | None  # directOrIndirectOwnership == "D"
    nature_of_ownership: str | None


class NonDerivativeTransaction(WireModel):
    security: str | None
    date: str | None
    shares: Amount
    remaining: Amount  # shares owned following the transaction
    price: Amount
    acquired_disposed: str | None  # "A" acquired / "D" disposed
    direct_indirect: str | None  # "D" direct / "I" indirect
    form: str | None  # transaction form type
    transaction_code: str | None  # SEC code: P, S, A, F, M, G, ...
    transaction_type: str | None  # human label resolved from the code
    equity_swap: bool | None
    footnote_ids: list[str]  # footnote ids this row cites; resolve against OwnershipData.footnotes


class DerivativeHolding(WireModel):
    security: str | None
    underlying: str | None
    underlying_shares: Amount
    exercise_price: Amount
    exercise_date: str | None
    expiration_date: str | None
    direct_indirect: str | None
    nature_of_ownership: str | None


class DerivativeTransaction(WireModel):
    security: str | None
    underlying: str | None
    underlying_shares: Amount
    exercise_price: Amount
    exercise_date: str | None
    expiration_date: str | None
    shares: Amount
    direct_indirect: str | None
    price: Amount
    acquired_disposed: str | None
    date: str | None
    remaining: Amount
    form: str | None
    transaction_code: str | None
    equity_swap: bool | None
    footnote_ids: list[str]


class OwnerSignature(WireModel):
    signature: str
    date: str


class OwnershipData(WireModel):
    """filing.obj() for Forms 3/4/5 - the edgar Ownership object, full fidelity."""

    kind: Literal["ownership"] = "ownership"
    form: str  # documentType: "3" | "4" | "5", or the "/A" amendment variant ("4/A")
    issuer: OwnershipIssuer
    reporting_owners: list[ReportingOwner]
    non_derivative_holdings: list[NonDerivativeHolding]
    non_derivative_transactions: list[NonDerivativeTransaction]
    derivative_holdings: list[DerivativeHolding]
    derivative_transactions: list[DerivativeTransaction]
    footnotes: dict[str, str]  # footnote id -> text
    signatures: list[OwnerSignature]
    reporting_period: str | None
    remarks: str | None
    no_securities: bool  # Form 3 "no securities beneficially owned" flag
    aff_10b5_one: bool | None  # document-level Rule 10b5-1 trading-plan affirmation; null when absent
    insider_name: str | None  # display join of reporting owner names
    position: str | None  # display join of reporting owner positions
    shares_traded: int | None  # aggregate shares across non-derivative market trades
