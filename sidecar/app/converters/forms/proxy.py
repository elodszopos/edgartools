"""edgar `ProxyStatement` (DEF 14A / 14A family) -> `ProxyData`, explicit field-by-field.

Two legs: XBRL pay-vs-performance / governance facts (ecd: + dei: concepts, exposed as scalars
and as the executive_compensation / pay_vs_performance / awards_close_to_mnpi DataFrames) and the
HTML-extracted comp tables (summary comp, director comp, beneficial ownership, voting proposals,
CEO pay ratio, audit fees). The table-valued properties return pandas DataFrames whose columns are
documented + stable; we unpivot each via to_dict("records") and map by column name (the U31
statement precedent). The typed-object properties (voting_proposals, named_executives,
ceo_pay_ratio, audit_fees) are read straight off the frozen edgar dataclasses. `season` is a
cross-entity scan (Company.proxy_season) excluded by the envelope's lazy-property policy.
"""

from __future__ import annotations

from typing import Any

from edgar.proxy import ProxyStatement

from app.models.forms.proxy import (
    ProxyAuditFees,
    ProxyAwardCloseToMnpi,
    ProxyBeneficialOwner,
    ProxyCeoPayRatio,
    ProxyData,
    ProxyDirectorCompRow,
    ProxyExecCompRow,
    ProxyNamedExecutive,
    ProxyPvpRow,
    ProxySummaryCompRow,
    ProxyVotingProposal,
)
from app.serialize import to_date, to_float, to_int, to_str


def _date_str(value: Any) -> str | None:
    # date-ish XBRL cells arrive as ISO strings OR date/Timestamp objects (period_end column);
    # normalize to an ISO string, keeping a faithful passthrough of an already-string value
    if isinstance(value, str):
        return to_str(value)
    parsed = to_date(value)
    return parsed.isoformat() if parsed is not None else None


def _records(df: Any) -> list[dict[str, Any]]:
    # a table property returns a pandas DataFrame (with documented columns) or an empty frame
    if df is None or len(df) == 0:
        return []
    return df.to_dict("records")


def _summary_comp_row(r: dict[str, Any]) -> ProxySummaryCompRow:
    return ProxySummaryCompRow(
        name=to_str(r.get("name")),
        title=to_str(r.get("title")),
        year=to_int(r.get("year")),
        salary=to_float(r.get("salary")),
        bonus=to_float(r.get("bonus")),
        stock_awards=to_float(r.get("stock_awards")),
        option_awards=to_float(r.get("option_awards")),
        non_equity_incentive=to_float(r.get("non_equity_incentive")),
        pension_change=to_float(r.get("pension_change")),
        other_compensation=to_float(r.get("other_compensation")),
        total=to_float(r.get("total")),
    )


def _director_comp_row(r: dict[str, Any]) -> ProxyDirectorCompRow:
    return ProxyDirectorCompRow(
        name=to_str(r.get("name")),
        fees_earned=to_float(r.get("fees_earned")),
        stock_awards=to_float(r.get("stock_awards")),
        option_awards=to_float(r.get("option_awards")),
        non_equity_incentive=to_float(r.get("non_equity_incentive")),
        pension_change=to_float(r.get("pension_change")),
        other_compensation=to_float(r.get("other_compensation")),
        total=to_float(r.get("total")),
    )


def _beneficial_owner(r: dict[str, Any]) -> ProxyBeneficialOwner:
    return ProxyBeneficialOwner(
        holder_name=to_str(r.get("holder_name")),
        holder_type=to_str(r.get("holder_type")),
        shares=to_float(r.get("shares")),
        percent_of_class=to_float(r.get("percent_of_class")),
    )


def _exec_comp_row(r: dict[str, Any]) -> ProxyExecCompRow:
    return ProxyExecCompRow(
        fiscal_year_end=_date_str(r.get("fiscal_year_end")),
        peo_total_comp=to_float(r.get("peo_total_comp")),
        peo_actually_paid_comp=to_float(r.get("peo_actually_paid_comp")),
        neo_avg_total_comp=to_float(r.get("neo_avg_total_comp")),
        neo_avg_actually_paid_comp=to_float(r.get("neo_avg_actually_paid_comp")),
    )


def _pvp_row(r: dict[str, Any]) -> ProxyPvpRow:
    return ProxyPvpRow(
        fiscal_year_end=_date_str(r.get("fiscal_year_end")),
        peo_actually_paid_comp=to_float(r.get("peo_actually_paid_comp")),
        neo_avg_actually_paid_comp=to_float(r.get("neo_avg_actually_paid_comp")),
        total_shareholder_return=to_float(r.get("total_shareholder_return")),
        peer_group_tsr=to_float(r.get("peer_group_tsr")),
        net_income=to_float(r.get("net_income")),
        company_selected_measure_value=to_float(r.get("company_selected_measure_value")),
    )


def _award_close_to_mnpi(r: dict[str, Any]) -> ProxyAwardCloseToMnpi:
    return ProxyAwardCloseToMnpi(
        grant_date=_date_str(r.get("grant_date")),
        executive=to_str(r.get("executive")),
        award_type=to_str(r.get("award_type")),
        exercise_price=to_float(r.get("exercise_price")),
        grant_date_fair_value=to_float(r.get("grant_date_fair_value")),
        underlying_securities=to_float(r.get("underlying_securities")),
        market_price_change_pct=to_float(r.get("market_price_change_pct")),
    )


def _named_executive(ne: Any) -> ProxyNamedExecutive:
    return ProxyNamedExecutive(
        name=to_str(ne.name),
        member_id=to_str(ne.member_id),
        role=to_str(ne.role),
        total_comp=to_float(ne.total_comp),
        actually_paid_comp=to_float(ne.actually_paid_comp),
        fiscal_year_end=_date_str(ne.fiscal_year_end),
    )


def _voting_proposal(vp: Any) -> ProxyVotingProposal:
    return ProxyVotingProposal(
        number=int(vp.number),
        description=vp.description,
        board_recommendation=to_str(vp.board_recommendation),
        proposal_type=str(vp.proposal_type),
    )


def _ceo_pay_ratio(cpr: Any) -> ProxyCeoPayRatio | None:
    if cpr is None:
        return None
    return ProxyCeoPayRatio(
        ceo_compensation=to_float(cpr.ceo_compensation),
        median_employee_compensation=to_float(cpr.median_employee_compensation),
        ratio=to_int(cpr.ratio),
    )


def _audit_fees(af: Any) -> ProxyAuditFees | None:
    if af is None:
        return None
    return ProxyAuditFees(
        auditor_name=to_str(af.auditor_name),
        current_year=to_int(af.current_year),
        prior_year=to_int(af.prior_year),
        audit_fees_current=to_float(af.audit_fees_current),
        audit_fees_prior=to_float(af.audit_fees_prior),
        audit_related_current=to_float(af.audit_related_current),
        audit_related_prior=to_float(af.audit_related_prior),
        tax_fees_current=to_float(af.tax_fees_current),
        tax_fees_prior=to_float(af.tax_fees_prior),
        other_fees_current=to_float(af.other_fees_current),
        other_fees_prior=to_float(af.other_fees_prior),
        total_current=to_float(af.total_current),
        total_prior=to_float(af.total_prior),
    )


def proxy_data(obj: ProxyStatement) -> ProxyData:
    return ProxyData(
        form=obj.form,
        filing_date=_date_str(obj.filing_date),
        company_name=to_str(obj.company_name),
        cik=to_str(obj.cik),
        accession_number=to_str(obj.accession_number),
        has_xbrl=bool(obj.has_xbrl),
        fiscal_year_end=_date_str(obj.fiscal_year_end),
        peo_name=to_str(obj.peo_name),
        peo_total_comp=to_float(obj.peo_total_comp),
        peo_actually_paid_comp=to_float(obj.peo_actually_paid_comp),
        neo_avg_total_comp=to_float(obj.neo_avg_total_comp),
        neo_avg_actually_paid_comp=to_float(obj.neo_avg_actually_paid_comp),
        total_shareholder_return=to_float(obj.total_shareholder_return),
        peer_group_tsr=to_float(obj.peer_group_tsr),
        net_income=to_float(obj.net_income),
        company_selected_measure=to_str(obj.company_selected_measure),
        company_selected_measure_value=to_float(obj.company_selected_measure_value),
        performance_measures=[s for s in (to_str(m) for m in obj.performance_measures) if s],
        insider_trading_policy_adopted=obj.insider_trading_policy_adopted,
        award_timing_mnpi_considered=obj.award_timing_mnpi_considered,
        award_dates_predetermined=obj.award_dates_predetermined,
        mnpi_disclosure_timed_for_comp_value=obj.mnpi_disclosure_timed_for_comp_value,
        has_individual_executive_data=bool(obj.has_individual_executive_data),
        executive_compensation=[_exec_comp_row(r) for r in _records(obj.executive_compensation)],
        pay_vs_performance=[_pvp_row(r) for r in _records(obj.pay_vs_performance)],
        awards_close_to_mnpi=[_award_close_to_mnpi(r) for r in _records(obj.awards_close_to_mnpi)],
        named_executives=[_named_executive(ne) for ne in obj.named_executives],
        summary_compensation_table=[_summary_comp_row(r) for r in _records(obj.summary_compensation_table)],
        director_compensation_table=[_director_comp_row(r) for r in _records(obj.director_compensation_table)],
        beneficial_ownership=[_beneficial_owner(r) for r in _records(obj.beneficial_ownership)],
        voting_proposals=[_voting_proposal(vp) for vp in obj.voting_proposals],
        ceo_pay_ratio=_ceo_pay_ratio(obj.ceo_pay_ratio),
        audit_fees=_audit_fees(obj.audit_fees),
        season=None,  # cross-entity fetch, served separately
    )
