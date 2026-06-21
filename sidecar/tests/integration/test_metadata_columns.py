"""Drift guard: _METADATA_COLUMNS must cover all non-period DataFrame columns."""

from app.converters.financials import _METADATA_COLUMNS, _build_period_columns


def test_metadata_columns_covers_all_non_period_columns() -> None:
    """If the library adds a structural column, this fails loudly instead of silently
    misaligning period mapping in _build_period_columns."""
    from edgar import Company
    from edgar.financials import Financials
    from edgar.xbrl.presentation import StatementView

    company = Company("AAPL")
    financials = company.get_financials()
    assert financials is not None
    stmt = financials.income_statement()
    assert stmt is not None
    df = stmt.to_dataframe(standard=True, view=StatementView.SUMMARY, include_unit=True, include_point_in_time=True, presentation=False)
    period_columns = _build_period_columns(stmt, df)
    all_columns = set(df.columns)
    data_and_meta = set(period_columns.keys()) | _METADATA_COLUMNS
    unexpected = all_columns - data_and_meta
    assert unexpected == set(), f"columns not in _METADATA_COLUMNS or period map: {unexpected}"
