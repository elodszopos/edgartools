"""Unit tests for ticker_ref_from_row (pure converter function)."""

import pytest

from app.converters.tickers import ticker_ref_from_row


def test_exchange_null_for_empty_string():
    row = {"cik": 320193, "ticker": "TEST", "name": "Test Inc", "exchange": ""}
    ref = ticker_ref_from_row(row)
    assert ref.exchange is None


def test_exchange_preserved_when_present():
    row = {"cik": 320193, "ticker": "AAPL", "name": "Apple Inc.", "exchange": "Nasdaq"}
    ref = ticker_ref_from_row(row)
    assert ref.exchange == "Nasdaq"


def test_cik_zero_padded():
    row = {"cik": 42, "ticker": "X", "name": "N", "exchange": "NYSE"}
    ref = ticker_ref_from_row(row)
    assert ref.cik == "0000000042"


def test_missing_ticker_raises():
    row = {"cik": 1, "ticker": "", "name": "N", "exchange": ""}
    with pytest.raises(ValueError, match="no ticker"):
        ticker_ref_from_row(row)
