"""Regression test: XBRLS.from_filings surfaces per-filing parse failures.

Previously from_filings wrapped each XBRL.from_filing in ``except Exception: pass``,
so a filing whose XBRL failed to parse was silently dropped from the stitched set
with no record. XBRLS now records one XBRLParseOutcome per input filing (newest
first) and exposes them as ``xbrls.parse_outcomes``; the failed filing is still
dropped from xbrl_list but is no longer invisible.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date
from unittest.mock import MagicMock

import pytest

from edgar.xbrl.stitching import XBRLS, XBRLParseOutcome


def _mock_filing(*, form: str, filing_date: date, accession_no: str):
    """Filing-like mock that XBRLS.from_filings consumes (form/date/accession)."""
    f = MagicMock()
    f.form = form
    f.filing_date = filing_date
    f.accession_no = accession_no
    return f


@pytest.mark.fast
def test_parse_outcomes_record_failure_instead_of_swallowing(monkeypatch):
    """A filing whose XBRL fails to parse is recorded, not silently dropped."""
    good_recent = _mock_filing(form="10-K", filing_date=date(2024, 2, 1),
                               accession_no="0000000001-24-000001")
    bad_middle = _mock_filing(form="10-K", filing_date=date(2023, 2, 1),
                              accession_no="0000000002-23-000002")
    good_old = _mock_filing(form="10-K", filing_date=date(2022, 2, 1),
                            accession_no="0000000003-22-000003")

    def fake_from_filing(filing):
        if filing.accession_no == "0000000002-23-000002":
            raise ValueError("malformed XBRL payload")
        return MagicMock()

    monkeypatch.setattr("edgar.xbrl.xbrl.XBRL.from_filing", fake_from_filing)

    # Pass unsorted; from_filings sorts newest-first internally.
    xbrls = XBRLS.from_filings([good_old, good_recent, bad_middle])

    outcomes = xbrls.parse_outcomes
    # One outcome per input filing, newest first.
    assert [o.accession_number for o in outcomes] == [
        "0000000001-24-000001",
        "0000000002-23-000002",
        "0000000003-22-000003",
    ]
    assert [o.parsed for o in outcomes] == [True, False, True]
    # The failure carries the exception type + message, not a swallowed None.
    assert outcomes[1].error == "ValueError: malformed XBRL payload"
    assert outcomes[0].error is None
    assert outcomes[2].error is None
    # Failed filing dropped from the stitched set; the two good ones remain.
    assert len(xbrls.xbrl_list) == 2


@pytest.mark.fast
def test_parse_outcomes_all_success(monkeypatch):
    """Every filing parses -> one parsed=True outcome each, none dropped."""
    filings = [
        _mock_filing(form="10-K", filing_date=date(2024, 2, 1),
                     accession_no="0000000001-24-000001"),
        _mock_filing(form="10-K", filing_date=date(2023, 2, 1),
                     accession_no="0000000002-23-000002"),
    ]
    monkeypatch.setattr("edgar.xbrl.xbrl.XBRL.from_filing",
                        lambda filing: MagicMock())

    xbrls = XBRLS.from_filings(filings)

    assert len(xbrls.parse_outcomes) == 2
    assert all(o.parsed for o in xbrls.parse_outcomes)
    assert all(o.error is None for o in xbrls.parse_outcomes)
    assert len(xbrls.xbrl_list) == 2


@pytest.mark.fast
def test_parse_outcome_is_frozen():
    """XBRLParseOutcome is immutable so recorded results can't be mutated."""
    outcome = XBRLParseOutcome(
        accession_number="0000000001-24-000001",
        form="10-K",
        filing_date=date(2024, 2, 1),
        parsed=True,
        error=None,
    )
    with pytest.raises(FrozenInstanceError):
        outcome.parsed = False  # type: ignore[misc]


@pytest.mark.fast
def test_from_xbrl_objects_has_empty_parse_outcomes():
    """Object-built XBRLS has no filing-level parse step -> empty outcomes."""
    xbrls = XBRLS.from_xbrl_objects([MagicMock()])
    assert xbrls.parse_outcomes == []
