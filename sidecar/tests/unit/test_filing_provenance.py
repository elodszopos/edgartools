"""_filing_provenance_list flags every stitched filing parsed/failed from the library's
parse_outcomes (issue #2), correlating by accession so a parse failure stays visible in
filings[] instead of being silently dropped from the stitched coverage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, cast

from edgar.xbrl.stitching.xbrls import ParseOutcome as XBRLParseOutcome

from app.converters.financials import _filing_provenance_list

if TYPE_CHECKING:
    from edgar._filings import Filing


@dataclass
class _Filing:  # minimal stand-in: the helper only reads these four attributes
    accession_no: str
    form: str
    filing_date: date
    period_of_report: date


def test_parse_failure_is_flagged_not_dropped() -> None:
    parsed = _Filing("0000320193-25-000079", "10-K", date(2025, 10, 31), date(2025, 9, 27))
    failed = _Filing("0000320193-24-000123", "10-K", date(2024, 11, 1), date(2024, 9, 28))
    outcomes = [
        XBRLParseOutcome(parsed.accession_no, "10-K", parsed.filing_date, parsed=True, error=None),
        XBRLParseOutcome(failed.accession_no, "10-K", failed.filing_date, parsed=False, error="ValueError: malformed XBRL"),
    ]
    superseded_by: dict[str, str | None] = {parsed.accession_no: None, failed.accession_no: None}

    provenance = _filing_provenance_list(cast("list[Filing]", [parsed, failed]), outcomes, superseded_by)

    # order preserved; both filings present (the failed one is NOT dropped)
    assert [p.accession_number for p in provenance] == [parsed.accession_no, failed.accession_no]
    # the filing that parsed contributed; no error
    assert provenance[0].parsed is True
    assert provenance[0].parse_error is None
    # the failed filing stays in the list, flagged with the library's error string
    assert provenance[1].parsed is False
    assert provenance[1].parse_error == "ValueError: malformed XBRL"


def test_missing_outcome_fails_loud() -> None:
    # from_filings emits one outcome per input filing; a filing with no outcome means the
    # input list and parse_outcomes disagree - surface it loudly, never guess parsed=True
    filing = _Filing("0000320193-25-000079", "10-K", date(2025, 10, 31), date(2025, 9, 27))
    superseded_by: dict[str, str | None] = {filing.accession_no: None}
    try:
        _filing_provenance_list(cast("list[Filing]", [filing]), [], superseded_by)
    except KeyError:
        return
    raise AssertionError("_filing_provenance_list silently tolerated a missing parse outcome")
