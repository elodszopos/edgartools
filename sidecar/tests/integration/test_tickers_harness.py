"""Integration: harness proof that the SEC ticker source /tickers (U12) wraps replays
from the URL-keyed fixture store, fully offline."""

from edgar.reference.tickers import get_company_ticker_name_exchange


def test_company_tickers_exchange_from_store():
    data = get_company_ticker_name_exchange()
    assert list(data.columns) == ["cik", "name", "ticker", "exchange"]
    apple = data[data["ticker"] == "AAPL"].iloc[0]
    assert int(apple["cik"]) == 320193
    assert "Apple" in str(apple["name"])
    assert str(apple["exchange"]) == "Nasdaq"
    assert len(data) > 5000  # full company ticker map, not a truncated payload
