"""Integration (U57c): the N-CSR / N-CSRS certified shareholder report over one `FundShareholderReport`
-> kind=ncsr.

N-CSR is the ONLY fund form edgar builds from Inline XBRL (the open-end-fund `oef:` taxonomy via
filing.xbrl() + FactQuery), not lxml. A single filing covers a WHOLE TRUST -- several funds (SEC
"series"), each with its own net assets, turnover, advisory fee and share classes. edgar groups the
facts under each series via the SGML header (which also supplies the authoritative fund / class names
and tickers), so the wire shape is per-fund: `funds[]`, one NcsrFund each. Four fixtures pin the matrix:

  bny_muni      annual N-CSR, single fund, 5 share classes, average-annual-returns populated (incl. a
                negative return), advisory fee + per-$10k expenses; the rich single-fund case
  gator         annual N-CSR, single fund / single class -- authoritative SGML name + ticker (COAGX)
                where the XBRL ClassName concept is absent
  bny_intl      semi-annual N-CSRS covering a 3-FUND trust -> funds[] has three entries, each with its
                own net assets and turnover (the anti-flattening case); semi-annual omits returns
  emkt_amend    N-CSR/A amendment (dispatch via the "/A" form) -> still one FundShareholderReport

Value policy: every Decimal crosses as float|None; holdings_count as int|None; ids/names/tickers as
as-filed SGML text. net_assets is now recovered per fund (filed as us-gaap:AssetsNet, dimensioned by
ClassAxis and unanimous within a fund). holdings[] is empty while holdings_count is populated.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_BNY_MUNI = "0000797923-25-000001"  # N-CSR, BNY Mellon Opportunistic Municipal (single fund, 5 classes)
_GATOR = "0001580642-25-003942"  # N-CSR, Caldwell & Orkin Gator Capital (single fund / single class)
_BNY_INTL = "0000857114-25-000006"  # N-CSRS, BNY Mellon Index Funds (3-fund trust, semi-annual)
_EMKT = "0001145549-25-040244"  # N-CSR/A, Emerging Markets Equities Fund (amendment dispatch)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _ncsr(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "FundShareholderReport"  # every N-CSR/N-CSRS (+/A) -> this one object
    assert body["data"] is not None
    assert body["data"]["kind"] == "ncsr"
    return body


def test_ncsr_annual_single_fund_multiclass(client: TestClient, golden) -> None:
    body = _ncsr(client, _BNY_MUNI)
    data = body["data"]
    assert data["form"] == "N-CSR"
    assert data["report_type"] == "Annual"

    assert len(data["funds"]) == 1
    fund = data["funds"][0]
    assert fund["series_id"] == "S000000090"
    assert fund["fund_name"] == "BNY Mellon Opportunistic Municipal Securities Fund"
    # net_assets is recovered (filed as us-gaap:AssetsNet, unanimous across the fund's 5 classes)
    assert fund["net_assets"] == 431000000.0
    assert fund["portfolio_turnover"] == 0.1817
    assert fund["advisory_fees_paid"] == 1611298.0  # fund-level, not per-class
    assert fund["holdings_count"] == 233
    assert fund["holdings"] == []  # oef:HoldingPctOfNav absent -> the per-holding list is empty

    classes = fund["share_classes"]
    assert len(classes) == 5
    # SGML declaration order, with authoritative names + tickers
    assert [c["class_name"] for c in classes] == ["Class A", "Class C", "Class Z", "Class Y", "Class I"]
    assert [c["class_ticker"] for c in classes] == ["PTEBX", "DMBCX", "DMBZX", "DMBYX", "DMBVX"]
    assert [c["class_id"] for c in classes] == [
        "C000000131",
        "C000000133",
        "C000001400",
        "C000173299",
        "C000173300",
    ]

    class_a = classes[0]
    assert class_a["expense_ratio_pct"] == 0.0078
    assert class_a["expenses_paid_amt"] == 79.0  # expenses paid on a $10,000 investment
    # each return is one (horizon, sales-load) cell; the first is the 1yr standardized (max-load) return
    assert class_a["annual_returns"][0] == {
        "period_start": "2024-05-01",
        "period_end": "2025-04-30",
        "return_pct": -0.0323,
        "without_sales_load": False,
    }
    # Class A is a load class: 3 horizons x 2 load treatments = 6 DISTINCT cells. Before the per-cell
    # fix the parser keyed every return on the shared period-end -> 6 indistinguishable rows (data loss).
    ar_a = class_a["annual_returns"]
    assert len(ar_a) == 6
    assert len({(c["period_start"], c["without_sales_load"]) for c in ar_a}) == 6
    with_load = {c["period_start"]: c["return_pct"] for c in ar_a if not c["without_sales_load"]}
    without_load = {c["period_start"]: c["return_pct"] for c in ar_a if c["without_sales_load"]}
    assert with_load == {"2024-05-01": -0.0323, "2020-05-01": 0.0056, "2015-05-01": 0.0151}
    assert without_load == {"2024-05-01": 0.0136, "2020-05-01": 0.0148, "2015-05-01": 0.0198}

    class_z = classes[2]
    assert class_z["expense_ratio_pct"] == 0.0073
    assert class_z["expenses_paid_amt"] == 74.0
    # a no-load class files only the standardized member (without_sales_load=False) at 3 horizons
    assert len(class_z["annual_returns"]) == 3
    assert all(c["without_sales_load"] is False for c in class_z["annual_returns"])
    assert class_z["annual_returns"][0]["period_start"] == "2024-05-01"
    assert class_z["annual_returns"][0]["return_pct"] == 0.0141

    golden("filing", "ncsr_bny_muni", body)


def test_ncsr_annual_single_class_authoritative_name(client: TestClient, golden) -> None:
    body = _ncsr(client, _GATOR)
    data = body["data"]
    assert data["form"] == "N-CSR"
    assert data["report_type"] == "Annual"

    assert len(data["funds"]) == 1
    fund = data["funds"][0]
    assert fund["series_id"] == "S000011446"
    assert fund["fund_name"] == "Caldwell & Orkin - Gator Capital Long/Short Fund"
    assert fund["net_assets"] == 49872799.0
    assert fund["portfolio_turnover"] == 0.42
    assert fund["advisory_fees_paid"] == 435520.0
    assert fund["holdings_count"] == 86

    assert len(fund["share_classes"]) == 1
    sc = fund["share_classes"][0]
    assert sc["class_id"] == "C000031655"
    # authoritative SGML name + ticker (the XBRL oef:ClassName concept is absent for this class)
    assert sc["class_name"] == "Caldwell & Orkin - Gator Capital Long/Short Fund"
    assert sc["class_ticker"] == "COAGX"
    assert sc["expense_ratio_pct"] == 0.0262
    assert sc["expenses_paid_amt"] == 286.0
    # a pure no-load fund files every horizon under WithoutSalesLoadMember -> without_sales_load=True
    assert len(sc["annual_returns"]) == 3
    assert sc["annual_returns"][0] == {
        "period_start": "2024-05-01",
        "period_end": "2025-04-30",
        "return_pct": 0.1833,
        "without_sales_load": True,
    }

    golden("filing", "ncsr_gator", body)


def test_ncsr_semiannual_multifund_trust(client: TestClient, golden) -> None:
    body = _ncsr(client, _BNY_INTL)
    data = body["data"]
    assert data["form"] == "N-CSRS"
    assert data["report_type"] == "Semi-Annual"  # N-CSRS -> Semi-Annual (is_annual would be False)

    # The trust holds THREE funds, each with its own net assets and turnover -- never flattened to one.
    funds = data["funds"]
    assert len(funds) == 3
    assert [f["series_id"] for f in funds] == ["S000000130", "S000000131", "S000000132"]
    assert [f["fund_name"] for f in funds] == [
        "BNY Mellon International Stock Index Fund",
        "BNY Mellon S&P 500 Index Fund",
        "BNY Mellon Smallcap Stock Index Fund",
    ]
    assert [f["net_assets"] for f in funds] == [315000000.0, 2221000000.0, 819000000.0]
    assert [f["portfolio_turnover"] for f in funds] == [0.0174, 0.011, 0.2664]
    assert [f["holdings_count"] for f in funds] == [700, 506, 607]
    assert all(f["advisory_fees_paid"] is None for f in funds)  # no oef:AdvisoryFeesPaidAmt facts

    # International Stock Index Fund -> 2 classes; S&P 500 -> 1 class; Smallcap -> 2 classes
    assert [f["fund_name"] and len(f["share_classes"]) for f in funds] == [2, 1, 2]
    intl = funds[0]["share_classes"]
    assert [c["class_name"] for c in intl] == ["Investor Shares", "Class I"]
    assert [c["class_ticker"] for c in intl] == ["DIISX", "DINIX"]
    assert intl[0]["expense_ratio_pct"] == 0.006
    assert intl[0]["expenses_paid_amt"] == 31.0

    # semi-annual reports do not carry average annual returns
    assert all(c["annual_returns"] == [] for f in funds for c in f["share_classes"])

    golden("filing", "ncsr_bny_intl", body)


def test_ncsr_amendment_dispatch(client: TestClient, golden) -> None:
    body = _ncsr(client, _EMKT)
    data = body["data"]
    assert data["form"] == "N-CSR/A"  # amendment dispatches through NCSR_FORMS
    assert data["report_type"] == "Annual"  # "CSRS" not in "N-CSR/A" -> Annual

    assert len(data["funds"]) == 1
    fund = data["funds"][0]
    assert fund["series_id"] == "S000011439"
    assert fund["fund_name"] == "EMERGING MARKETS EQUITIES FUND, INC"
    assert fund["net_assets"] == 1373000000.0
    assert fund["portfolio_turnover"] == 0.34
    assert fund["advisory_fees_paid"] == 9000000.0

    classes = fund["share_classes"]
    assert len(classes) == 3
    assert [c["class_name"] for c in classes] == ["Class M", "Class F-3", "Class R-6"]
    assert [c["class_ticker"] for c in classes] == ["EMRGX", "EMGEX", "REFGX"]
    assert classes[0]["annual_returns"][0] == {
        "period_start": "2023-07-01",
        "period_end": "2024-06-30",
        "return_pct": 0.026,
        "without_sales_load": False,
    }

    golden("filing", "ncsr_emkt_amend", body)
