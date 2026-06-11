"""Integration: VCR harness proof against the real SEC source /tickers (U12) will wrap.

First run records the cassette (1 interaction, within budget); record_mode=once keeps
every later run offline.
"""

import pytest
from edgar.reference.tickers import get_company_ticker_name_exchange


@pytest.mark.vcr
def test_company_tickers_exchange_cassette():
    data = get_company_ticker_name_exchange()
    assert list(data.columns) == ["cik", "name", "ticker", "exchange"]
    apple = data[data["ticker"] == "AAPL"].iloc[0]
    assert int(apple["cik"]) == 320193
    assert "Apple" in str(apple["name"])
    assert str(apple["exchange"]) == "Nasdaq"
    assert len(data) > 5000  # full company ticker map, not a truncated payload
