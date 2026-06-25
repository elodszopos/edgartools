"""edgar `Ownership` (Forms 3/4/5) -> `OwnershipData`, explicit field-by-field.

`filing.obj()` returns ONE `Ownership` object for all three forms. The typed rows come from the
`NonDerivativeTable`/`DerivativeTable` `DataHolder` collections: integer-indexing a collection
yields a frozen dataclass for that row. Numeric cells are float when edgar's `convert_to_numeric`
parsed the whole column, else the raw as-filed string (e.g. a footnote-reference price) - mirrored
faithfully, never coerced. edgar's objects are pandas-backed and untyped, so the edgar side is
`Any`; the wire side is fully typed.
"""

from __future__ import annotations

from typing import Any

from edgar.ownership import Ownership

from app.models.common import Address as WireAddress
from app.models.forms.ownership import (
    DerivativeHolding,
    DerivativeTransaction,
    NonDerivativeHolding,
    NonDerivativeTransaction,
    OwnershipData,
    OwnershipIssuer,
    OwnerSignature,
    ReportingOwner,
)
from app.serialize import to_bool, to_float, to_str


def _records(holder: Any) -> list[Any]:
    # a DataHolder yields a frozen dataclass per row via integer indexing; empty -> no rows
    return [holder[i] for i in range(len(holder))]


def _amount(value: Any) -> float | str | None:
    # float when the column parsed numeric, else the raw as-filed string, else null;
    # never coerce str->float (a footnote-reference price must stay the literal string)
    if isinstance(value, str):
        return to_str(value)
    return to_float(value)


def _footnote_ids(value: Any) -> list[str]:
    # edgar newline-joins a row's cited footnote ids (get_footnotes) - split to a clean list
    if not isinstance(value, str):
        return []
    return [fid for fid in (part.strip() for part in value.split("\n")) if fid]


def _footnotes(footnotes: Any) -> dict[str, str]:
    if footnotes is None or len(footnotes) == 0:
        return {}
    return {str(k): str(v) for k, v in footnotes.items()}


def _address(address: Any) -> WireAddress | None:
    if address is None:
        return None
    # unlike the SGML-header address, the ownership owner address carries the state description
    return WireAddress(
        street1=to_str(address.street1),
        street2=to_str(address.street2),
        city=to_str(address.city),
        state_or_country=to_str(address.state_or_country),
        state_or_country_description=to_str(address.state_or_country_description),
        zipcode=to_str(address.zipcode),
    )


def _owner(owner: Any) -> ReportingOwner:
    return ReportingOwner(
        cik=to_str(owner.cik),
        is_company=bool(owner.is_company),
        name=owner.name,  # display name (individuals reversed to "First Last") - required, kept raw
        name_unreversed=owner.name_unreversed,
        address=_address(owner.address),
        is_director=bool(owner.is_director),
        is_officer=bool(owner.is_officer),
        is_other=bool(owner.is_other),
        is_ten_pct_owner=bool(owner.is_ten_pct_owner),
        officer_title=to_str(owner.officer_title),
        position=owner.position,  # derived display title, may be ""
    )


def _non_derivative_holding(rec: Any) -> NonDerivativeHolding:
    return NonDerivativeHolding(
        security=to_str(rec.security),
        shares=_amount(rec.shares),
        direct=to_bool(rec.direct),  # edgar stores "Yes"/"No" here, not "D"/"I"
        nature_of_ownership=to_str(rec.nature_of_ownership),
    )


def _non_derivative_transaction(rec: Any) -> NonDerivativeTransaction:
    return NonDerivativeTransaction(
        security=to_str(rec.security),
        date=to_str(rec.date),
        shares=_amount(rec.shares),
        remaining=_amount(rec.remaining),
        price=_amount(rec.price),
        acquired_disposed=to_str(rec.acquired_disposed),
        direct_indirect=to_str(rec.direct_indirect),
        form=to_str(rec.form),
        transaction_code=to_str(rec.transaction_code),
        transaction_type=to_str(rec.transaction_type),
        equity_swap=to_bool(rec.equity_swap),
        footnote_ids=_footnote_ids(rec.footnotes),
    )


def _derivative_holding(rec: Any) -> DerivativeHolding:
    return DerivativeHolding(
        security=to_str(rec.security),
        underlying=to_str(rec.underlying),
        underlying_shares=_amount(rec.underlying_shares),
        exercise_price=_amount(rec.exercise_price),
        exercise_date=to_str(rec.exercise_date),
        expiration_date=to_str(rec.expiration_date),
        direct_indirect=to_str(rec.direct_indirect),
        nature_of_ownership=to_str(rec.nature_of_ownership),
    )


def _derivative_transaction(rec: Any) -> DerivativeTransaction:
    return DerivativeTransaction(
        security=to_str(rec.security),
        underlying=to_str(rec.underlying),
        underlying_shares=_amount(rec.underlying_shares),
        exercise_price=_amount(rec.exercise_price),
        exercise_date=to_str(rec.exercise_date),
        expiration_date=to_str(rec.expiration_date),
        shares=_amount(rec.shares),
        direct_indirect=to_str(rec.direct_indirect),
        price=_amount(rec.price),
        acquired_disposed=to_str(rec.acquired_disposed),
        date=to_str(rec.date),
        remaining=_amount(rec.remaining),
        form=to_str(rec.form),
        transaction_code=to_str(rec.transaction_code),
        equity_swap=to_bool(rec.equity_swap),
        footnote_ids=_footnote_ids(rec.footnotes),
    )


def _signature(sig: Any) -> OwnerSignature:
    return OwnerSignature(signature=sig.signature, date=sig.date)


def ownership_data(obj: Ownership) -> OwnershipData:
    non_deriv = obj.non_derivative_table
    deriv = obj.derivative_table
    return OwnershipData(
        form=to_str(obj.form) or "",
        issuer=OwnershipIssuer(
            cik=to_str(obj.issuer.cik),
            name=to_str(obj.issuer.name),
            ticker=to_str(obj.issuer.ticker),
        ),
        reporting_owners=[_owner(o) for o in obj.reporting_owners.owners],
        non_derivative_holdings=[_non_derivative_holding(r) for r in _records(non_deriv.holdings)],
        non_derivative_transactions=[_non_derivative_transaction(r) for r in _records(non_deriv.transactions)],
        derivative_holdings=[_derivative_holding(r) for r in _records(deriv.holdings)],
        derivative_transactions=[_derivative_transaction(r) for r in _records(deriv.transactions)],
        footnotes=_footnotes(obj.footnotes),
        signatures=[_signature(s) for s in obj.signatures.signatures],
        reporting_period=to_str(obj.reporting_period),
        remarks=to_str(obj.remarks),
        no_securities=bool(obj.no_securities),
        aff_10b5_one=obj.aff_10b5_one,
        insider_name=to_str(obj.insider_name),
        position=to_str(obj.position),
        shares_traded=int(obj.shares_traded) if obj.shares_traded is not None else None,
    )
