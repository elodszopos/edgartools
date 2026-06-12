"""Integration: /company/{id}/financials statements + /financials/metrics scalars.

Each company costs ~2 requests (submissions JSON + the filing's SGML .txt); XBRL parses
from the in-memory SGML. Ground truth verified by hand against the recorded SEC filings
(2026-06-12): AAPL 10-K 0000320193-25-000079 / 10-Q 0000320193-26-000013, Realty Income
10-K 0000726728-26-000011, Infosys 20-F 0000950170-25-091925 (IFRS path).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_STATEMENT_KEYS = (
    "income_statement",
    "balance_sheet",
    "cashflow_statement",
    "statement_of_equity",
    "comprehensive_income",
    "cover",
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _record(statement: dict, concept: str, label: str) -> dict:
    matches = [r for r in statement["records"] if r["concept"] == concept and r["label"] == label]
    assert len(matches) == 1, f"expected exactly one {concept} / {label!r} row, got {len(matches)}"
    return matches[0]


def _values(record: dict) -> list:
    return [v["value"] for v in record["values"]]


def test_financials_annual_standardized(client: TestClient, golden) -> None:
    response = client.get("/company/AAPL/financials")
    assert response.status_code == 200
    body = response.json()

    assert body["cik"] == "0000320193"
    assert body["company"] == "Apple Inc."
    assert body["form"] == "10-K"
    assert body["accession_number"] == "0000320193-25-000079"
    assert body["filing_date"] == "2025-10-31"
    assert body["period_of_report"] == "2025-09-27"
    assert body["period"] == "annual"
    assert body["view"] == "standardized"
    assert body["dimensions"] is False

    assert body["amendments"] is False
    assert body["superseded_by"] is None  # no 10-K/A amends FY2025 in the fixture submissions

    income = body["income_statement"]
    assert income["periods"] == [
        {
            "key": "duration_2024-09-29_2025-09-27",
            "label": "Annual: September 29, 2024 to September 27, 2025",
            "period_type": "duration",
            "period_start": "2024-09-29",
            "period_end": "2025-09-27",
            "period_months": 12,  # 363-day fiscal year
        },
        {
            "key": "duration_2023-10-01_2024-09-28",
            "label": "Annual: October 01, 2023 to September 28, 2024",
            "period_type": "duration",
            "period_start": "2023-10-01",
            "period_end": "2024-09-28",
            "period_months": 12,
        },
        {
            "key": "duration_2022-09-25_2023-09-30",
            "label": "Annual: September 25, 2022 to September 30, 2023",
            "period_type": "duration",
            "period_start": "2022-09-25",
            "period_end": "2023-09-30",
            "period_months": 12,  # 370-day 53-week fiscal year still rounds to 12
        },
    ]
    assert len(income["records"]) == 18

    net_sales = _record(income, "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax", "Net sales")
    assert _values(net_sales) == [416161000000.0, 391035000000.0, 383285000000.0]
    assert net_sales["balance"] == "credit"
    assert net_sales["preferred_sign"] == 1.0
    assert net_sales["unit"] == "usd"
    assert net_sales["currency"] == "USD"
    assert net_sales["is_abstract"] is False
    # numeric facts carry the discriminator; absent values stay null
    assert {v["value_type"] for v in net_sales["values"]} == {"number"}
    assert _values(_record(income, "us-gaap_GrossProfit", "Gross margin")) == [
        195201000000.0,
        180683000000.0,
        169148000000.0,
    ]
    assert _values(_record(income, "us-gaap_ResearchAndDevelopmentExpense", "Research and development")) == [
        34550000000.0,
        31370000000.0,
        29915000000.0,
    ]

    # abstract section headers carry structure, never values
    opex_header = _record(income, "us-gaap_OperatingExpensesAbstract", "Operating expenses:")
    assert opex_header["is_abstract"] is True
    assert _values(opex_header) == [None, None, None]

    balance = body["balance_sheet"]
    assert balance["periods"] == [
        {
            "key": "instant_2025-09-27",
            "label": "September 27, 2025",
            "period_type": "instant",
            "period_start": None,
            "period_end": "2025-09-27",
            "period_months": None,  # instant periods have no duration
        },
        {
            "key": "instant_2024-09-28",
            "label": "September 28, 2024",
            "period_type": "instant",
            "period_start": None,
            "period_end": "2024-09-28",
            "period_months": None,
        },
    ]
    assert len(balance["records"]) == 37
    assert _values(_record(balance, "us-gaap_CashAndCashEquivalentsAtCarryingValue", "Cash and cash equivalents")) == [
        35934000000.0,
        29943000000.0,
    ]

    cashflow = body["cashflow_statement"]
    assert len(cashflow["records"]) == 35
    ocf = _record(cashflow, "us-gaap_NetCashProvidedByUsedInOperatingActivities", "Cash generated by operating activities")
    assert ocf["standard_concept"] == "NetCashFromOperatingActivities"
    assert _values(ocf) == [111482000000.0, 118254000000.0, 110543000000.0]

    equity = body["statement_of_equity"]
    assert len(equity["records"]) == 11
    assert _values(_record(equity, "us-gaap_StockholdersEquity", "Beginning balances")) == [
        56950000000.0,
        62146000000.0,
        50672000000.0,
    ]

    comprehensive = body["comprehensive_income"]
    assert len(comprehensive["records"]) == 13
    assert _values(_record(comprehensive, "us-gaap_NetIncomeLoss", "Net income")) == [
        112010000000.0,
        93736000000.0,
        96995000000.0,
    ]

    cover = body["cover"]
    assert len(cover["records"]) == 36
    assert [p["key"] for p in cover["periods"]] == ["duration_2024-09-29_2025-09-27"]
    # cover facts are text - the wire value union carries them as strings
    assert _values(_record(cover, "dei_DocumentType", "Document Type")) == ["10-K"]
    assert [v["value_type"] for v in _record(cover, "dei_DocumentType", "Document Type")["values"]] == ["text"]
    assert _values(_record(cover, "dei_CurrentFiscalYearEndDate", "Current Fiscal Year End Date")) == ["--09-27"]
    assert _values(_record(cover, "dei_DocumentPeriodEndDate", "Document Period End Date")) == ["2025-09-27"]

    golden("company_financials", "aapl_annual_standardized", body)


def test_financials_raw_view_with_dimensions(client: TestClient, golden) -> None:
    response = client.get("/company/AAPL/financials", params={"view": "raw", "dimensions": "true"})
    assert response.status_code == 200
    body = response.json()
    assert body["view"] == "raw"
    assert body["dimensions"] is True

    income = body["income_statement"]
    assert len(income["records"]) == 47
    assert len([r for r in income["records"] if r["is_dimension"]]) == 29

    iphone = _record(income, "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax", "iPhone")
    assert iphone["is_dimension"] is True
    assert iphone["dimension_axis"] == "srt:ProductOrServiceAxis"
    assert iphone["dimension_member_label"] == "iPhone"
    assert _values(iphone) == [209586000000.0, 201183000000.0, 200583000000.0]

    golden("company_financials", "aapl_annual_raw_dimensions", body)


def test_financials_quarterly(client: TestClient, golden) -> None:
    response = client.get("/company/AAPL/financials", params={"period": "quarterly"})
    assert response.status_code == 200
    body = response.json()
    assert body["form"] == "10-Q"
    assert body["accession_number"] == "0000320193-26-000013"
    assert body["period"] == "quarterly"

    # a 10-Q carries quarter + fiscal-YTD durations; both label kinds must survive the wire
    income = body["income_statement"]
    assert [p["label"] for p in income["periods"]] == [
        "Quarterly: December 28, 2025 to March 28, 2026",
        "Quarterly: December 29, 2024 to March 29, 2025",
        "Semi-Annual: September 28, 2025 to March 28, 2026",
        "Semi-Annual: September 29, 2024 to March 29, 2025",
    ]
    assert [p["key"] for p in income["periods"]] == [
        "duration_2025-12-28_2026-03-28",
        "duration_2024-12-29_2025-03-29",
        "duration_2025-09-28_2026-03-28",
        "duration_2024-09-29_2025-03-29",
    ]
    net_sales = _record(income, "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax", "Net sales")
    assert _values(net_sales) == [111184000000.0, 95359000000.0, 254940000000.0, 219659000000.0]

    golden("company_financials", "aapl_quarterly", body)


def test_financials_reit_revenue_composition(client: TestClient, golden) -> None:
    # diversify beyond AAPL: REIT income statements lead with lease income, not product sales
    response = client.get("/company/O/financials")
    assert response.status_code == 200
    body = response.json()
    assert body["cik"] == "0000726728"
    assert body["form"] == "10-K"
    assert body["accession_number"] == "0000726728-26-000011"

    income = body["income_statement"]
    assert [p["key"] for p in income["periods"]] == [
        "duration_2025-01-01_2025-12-31",
        "duration_2024-01-01_2024-12-31",
        "duration_2023-01-01_2023-12-31",
    ]
    assert _values(_record(income, "us-gaap_LeaseIncome", "Rental (including reimbursements)")) == [
        5437332000.0,
        5043748000.0,
        3958150000.0,
    ]
    assert _values(_record(income, "us-gaap_Revenues", "Total revenue")) == [
        5749377000.0,
        5271142000.0,
        4078993000.0,
    ]
    assert _values(_record(income, "us-gaap_DepreciationDepletionAndAmortization", "Depreciation and amortization")) == [
        2524200000.0,
        2395644000.0,
        1895177000.0,
    ]

    golden("company_financials", "realty_income_annual", body)


def test_financials_ifrs_foreign_filer(client: TestClient, golden) -> None:
    # 20-F filer: annual chain falls through 10-K to 20-F; concepts are ifrs-full_*
    response = client.get("/company/INFY/financials")
    assert response.status_code == 200
    body = response.json()
    assert body["cik"] == "0001067491"
    assert body["company"] == "Infosys Ltd"
    assert body["form"] == "20-F"
    assert body["accession_number"] == "0000950170-25-091925"
    assert body["filing_date"] == "2025-07-01"
    assert body["period_of_report"] == "2025-03-31"

    income = body["income_statement"]
    # Indian fiscal year: April-March annual durations
    assert income["periods"][0] == {
        "key": "duration_2024-04-01_2025-03-31",
        "label": "Annual: April 01, 2024 to March 31, 2025",
        "period_type": "duration",
        "period_start": "2024-04-01",
        "period_end": "2025-03-31",
        "period_months": 12,
    }
    revenue = _record(income, "ifrs-full_RevenueFromContractsWithCustomers", "Revenues")
    assert _values(revenue) == [19277000000.0, 18562000000.0, 18212000000.0]
    assert revenue["unit"] == "u_usd"  # INFY declares its own unit id, unlike AAPL's 'usd'
    assert revenue["currency"] is None  # filer-specific unit ids are not ISO-resolvable
    assert _values(_record(income, "ifrs-full_GrossProfit", "Gross profit")) == [
        5872000000.0,
        5587000000.0,
        5503000000.0,
    ]
    assert _values(_record(income, "ifrs-full_ProfitLossFromOperatingActivities", "Operating profit")) == [
        4071000000.0,
        3834000000.0,
        3825000000.0,
    ]
    assert {k: len(body[k]["records"]) for k in _STATEMENT_KEYS} == {
        "income_statement": 40,
        "balance_sheet": 53,
        "cashflow_statement": 66,
        "statement_of_equity": 28,
        "comprehensive_income": 40,
        "cover": 41,
    }
    golden("company_financials", "infy_annual_standardized", body)

    # All metrics resolve for this IFRS 20-F filer: operating_income/OCF/shares via
    # ifrs-full_* and capex via the infy_* extension concept (operating_income equals
    # the 'Operating profit' row above); FCF = OCF - abs(capex).
    response = client.get("/company/INFY/financials/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics == {
        "cik": "0001067491",
        "company": "Infosys Ltd",
        "form": "20-F",
        "accession_number": "0000950170-25-091925",
        "filing_date": "2025-07-01",
        "period_of_report": "2025-03-31",
        "superseded_by": None,  # no 20-F/A for FY2025 in the fixture submissions
        "period": "annual",
        "amendments": False,
        "revenue": 19277000000.0,
        "operating_income": 4071000000.0,
        "net_income": 3162000000.0,
        "total_assets": 17419000000.0,
        "total_liabilities": 6164000000.0,
        "stockholders_equity": 11255000000.0,
        "current_assets": 11359000000.0,
        "current_liabilities": 5012000000.0,
        "operating_cash_flow": 4351000000.0,
        "capital_expenditures": 263000000.0,
        "free_cash_flow": 4088000000.0,
        "shares_outstanding_basic": 4141611738.0,
        "shares_outstanding_diluted": 4152051184.0,
        "current_ratio": 2.2663607342378294,
        "debt_to_assets": 0.35386646765026697,
    }
    golden("company_financials_metrics", "infy_annual", metrics)


def test_financial_metrics(client: TestClient, golden) -> None:
    response = client.get("/company/AAPL/financials/metrics")
    assert response.status_code == 200
    body = response.json()
    # operating_cash_flow + derived free_cash_flow resolve by us-gaap concept
    # (NetCashProvidedByUsedInOperatingActivities), independent of AAPL's rendered
    # label 'Cash generated by operating activities'; FCF = OCF - abs(capex).
    assert body == {
        "cik": "0000320193",
        "company": "Apple Inc.",
        "form": "10-K",
        "accession_number": "0000320193-25-000079",
        "filing_date": "2025-10-31",
        "period_of_report": "2025-09-27",
        "superseded_by": None,  # no 10-K/A amends FY2025 in the fixture submissions
        "period": "annual",
        "amendments": False,
        "revenue": 416161000000.0,
        "operating_income": 133050000000.0,
        "net_income": 112010000000.0,
        "total_assets": 359241000000.0,
        "total_liabilities": 285508000000.0,
        "stockholders_equity": 73733000000.0,
        "current_assets": 147957000000.0,
        "current_liabilities": 165631000000.0,
        "operating_cash_flow": 111482000000.0,
        "capital_expenditures": 12715000000.0,
        "free_cash_flow": 98767000000.0,
        "shares_outstanding_basic": 14948500000.0,
        "shares_outstanding_diluted": 15004697000.0,
        "current_ratio": 0.8932929222186667,
        "debt_to_assets": 0.7947533828265705,
    }

    golden("company_financials_metrics", "aapl_annual", body)


def test_financials_silence_no_annual_filing(client: TestClient) -> None:
    # individual filer (Form 4s only) - the error names the form chain that was tried
    response = client.get("/company/0001347842/financials")
    assert response.status_code == 404
    assert response.json() == {"detail": "no annual filing (10-K/20-F/40-F) at SEC for CIK 0001347842"}


def test_financials_multi_annual(client: TestClient, golden) -> None:
    # one fiscal year stitched in from each of the 3 most recent 10-Ks
    response = client.get("/company/AAPL/financials/multi", params={"n": "3"})
    assert response.status_code == 200
    body = response.json()
    assert body["cik"] == "0000320193"
    assert body["period"] == "annual"
    assert body["amendments"] is False
    assert body["filings"] == [
        {
            "form": "10-K",
            "accession_number": "0000320193-25-000079",
            "filing_date": "2025-10-31",
            "period_of_report": "2025-09-27",
            "superseded_by": None,  # no 10-K/A in the fixture submissions for any stitched year
        },
        {
            "form": "10-K",
            "accession_number": "0000320193-24-000123",
            "filing_date": "2024-11-01",
            "period_of_report": "2024-09-28",
            "superseded_by": None,
        },
        {
            "form": "10-K",
            "accession_number": "0000320193-23-000106",
            "filing_date": "2023-11-03",
            "period_of_report": "2023-09-30",
            "superseded_by": None,
        },
    ]

    income = body["income_statement"]
    assert income["periods"] == [
        {
            "key": "duration_2024-09-29_2025-09-27",
            "label": "FY Sep 27, 2025",
            "period_type": "duration",
            "period_start": "2024-09-29",
            "period_end": "2025-09-27",
            "period_months": 12,
        },
        {
            "key": "duration_2023-10-01_2024-09-28",
            "label": "FY Sep 28, 2024",
            "period_type": "duration",
            "period_start": "2023-10-01",
            "period_end": "2024-09-28",
            "period_months": 12,
        },
        {
            "key": "duration_2022-09-25_2023-09-30",
            "label": "FY Sep 30, 2023",
            "period_type": "duration",
            "period_start": "2022-09-25",
            "period_end": "2023-09-30",
            "period_months": 12,
        },
    ]
    net_sales = _record(income, "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax", "Net sales")
    assert _values(net_sales) == [
        416161000000.0,
        391035000000.0,
        383285000000.0,
    ]
    # stitched rows now carry the concept-level attributes from the newest filing
    assert net_sales["balance"] == "credit"
    assert net_sales["unit"] == "usd"
    assert net_sales["currency"] == "USD"
    assert net_sales["preferred_sign"] == 1.0
    total_opex = _record(income, "us-gaap_OperatingExpenses", "Total operating expenses")
    assert total_opex["is_total"] is True
    assert _values(total_opex) == [62151000000.0, 57467000000.0, 54847000000.0]
    assert _values(_record(income, "us-gaap_OperatingIncomeLoss", "Operating income")) == [
        133050000000.0,
        123216000000.0,
        114301000000.0,
    ]
    assert {k: len(body[k]["records"]) for k in ("income_statement", "balance_sheet", "cashflow_statement")} == {
        "income_statement": 18,
        "balance_sheet": 37,
        "cashflow_statement": 34,
    }
    # the multi response now stitches equity + comprehensive income as well
    assert _values(_record(body["comprehensive_income"], "us-gaap_NetIncomeLoss", "Net income")) == [
        112010000000.0,
        93736000000.0,
        96995000000.0,
    ]
    assert len(body["statement_of_equity"]["records"]) > 0

    golden("company_financials_multi", "aapl_annual_n3", body)


def test_financials_multi_quarterly(client: TestClient, golden) -> None:
    # default stitching takes ONE column per filing (GH #780): the newest 10-Q
    # contributes its YTD column, so quarter and YTD durations mix across periods -
    # the period keys carry start/end dates for consumers to interpret
    response = client.get("/company/AAPL/financials/multi", params={"period": "quarterly", "n": "3"})
    assert response.status_code == 200
    body = response.json()
    assert [f["accession_number"] for f in body["filings"]] == [
        "0000320193-26-000013",
        "0000320193-26-000006",
        "0000320193-25-000073",
    ]
    income = body["income_statement"]
    assert [p["label"] for p in income["periods"]] == [
        "Q2 YTD Mar 28, 2026",
        "Q1 Dec 27, 2025",
        "Q3 YTD Jun 28, 2025",
    ]
    assert _values(_record(income, "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax", "Net sales")) == [
        254940000000.0,
        143756000000.0,
        313695000000.0,
    ]

    golden("company_financials_multi", "aapl_quarterly_n3", body)


def test_financials_multi_reit_and_errors(client: TestClient, golden) -> None:
    response = client.get("/company/O/financials/multi", params={"n": "2"})
    assert response.status_code == 200
    body = response.json()
    assert [f["accession_number"] for f in body["filings"]] == ["0000726728-26-000011", "0000726728-25-000055"]
    assert [p["key"] for p in body["income_statement"]["periods"]] == [
        "duration_2025-01-01_2025-12-31",
        "duration_2024-01-01_2024-12-31",
    ]
    golden("company_financials_multi", "realty_income_n2", body)

    response = client.get("/company/0001347842/financials/multi")
    assert response.status_code == 404
    assert response.json() == {"detail": "no annual filing (10-K/20-F/40-F) at SEC for CIK 0001347842"}

    # n bounds reject before any SEC traffic
    assert client.get("/company/AAPL/financials/multi", params={"n": "1"}).status_code == 422
    assert client.get("/company/AAPL/financials/multi", params={"n": "9"}).status_code == 422


_TTM_DERIVED_WARNING = "Some quarters were derived from YTD or annual facts. These are calculated values, not directly reported quarterly data."


def test_financials_ttm(client: TestClient, golden) -> None:
    response = client.get("/company/AAPL/financials/ttm")
    assert response.status_code == 200
    body = response.json()
    # per-quarter provenance: the accessions/dates match the 10-Qs pinned in
    # test_financials_multi_quarterly and the 10-K pinned in the annual tests; the
    # derived Q4 inherits the provenance of its FY source fact (the 10-K)
    current_window = [
        {
            "fiscal_year": 2025,
            "fiscal_period": "Q3",
            "filing_date": "2025-08-01",
            "accession_number": "0000320193-25-000073",
            "form_type": "10-Q",
        },
        {
            "fiscal_year": 2025,
            "fiscal_period": "Q4",
            "filing_date": "2025-10-31",
            "accession_number": "0000320193-25-000079",
            "form_type": "10-K",
        },
        {
            "fiscal_year": 2026,
            "fiscal_period": "Q1",
            "filing_date": "2026-01-30",
            "accession_number": "0000320193-26-000006",
            "form_type": "10-Q",
        },
        {
            "fiscal_year": 2026,
            "fiscal_period": "Q2",
            "filing_date": "2026-05-01",
            "accession_number": "0000320193-26-000013",
            "form_type": "10-Q",
        },
    ]
    assert body == {
        "cik": "0000320193",
        "company": "Apple Inc.",
        "as_of": None,
        "concept": None,
        "revenue": {
            "concept": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
            "label": "Revenue from Contract with Customer, Excluding Assessed Tax",
            "value": 451442000000.0,
            "unit": "USD",
            "as_of_date": "2026-03-28",
            # the TTM through 2026-03-28 became publicly knowable when its last
            # source fact was filed: the Q2 FY26 10-Q on 2026-05-01
            "public_date": "2026-05-01",
            "periods": current_window,
            "has_gaps": False,
            "has_calculated_q4": True,
            "warning": _TTM_DERIVED_WARNING,
        },
        "net_income": {
            "concept": "us-gaap:NetIncomeLoss",
            "label": "Net Income (Loss) Attributable to Parent",
            "value": 122575000000.0,
            "unit": "USD",
            "as_of_date": "2026-03-28",
            "public_date": "2026-05-01",
            "periods": current_window,
            "has_gaps": False,
            "has_calculated_q4": True,
            "warning": _TTM_DERIVED_WARNING,
        },
        "metric": None,
    }
    golden("company_financials_ttm", "aapl_default", body)


def test_financials_ttm_concept_and_as_of(client: TestClient, golden) -> None:
    response = client.get("/company/AAPL/financials/ttm", params={"concept": "GrossProfit"})
    assert response.status_code == 200
    body = response.json()
    assert body["concept"] == "GrossProfit"
    assert body["metric"]["concept"] == "us-gaap:GrossProfit"
    assert body["metric"]["value"] == 216071000000.0
    assert body["metric"]["as_of_date"] == "2026-03-28"

    response = client.get("/company/AAPL/financials/ttm", params={"concept": "GrossProfit", "as_of": "2025-Q1"})
    assert response.status_code == 200
    body = response.json()
    assert body["as_of"] == "2025-Q1"
    metric = body["metric"]
    # hand-verified against AAPL 10-Qs/10-K: Q3 FY24 39678 + derived Q4 FY24 43879
    # + Q1 FY25 58275 + Q2 FY25 44867 = 186699 (millions)
    assert metric["value"] == 186699000000.0
    assert metric["as_of_date"] == "2025-03-29"
    # periods label each quarter's fiscal_year from its period_end + the company's
    # FYE month (Apple: September), not the SEC-tagged fiscal_year (which marks
    # comparative-period facts with the reporting filing's FY). So this historical
    # as_of window reads as four consecutive quarters Q3'24..Q2'25, matching how
    # calculate_ttm_trend derives label years (GH #793).
    # Provenance shows the VINTAGE actually consumed: the library backs these
    # historical quarters with comparative facts re-reported in FY25/FY26 filings,
    # not the original FY24 10-Qs - which is why public_date (2026-05-01) postdates
    # the window and must never be read as "earliest knowable".
    assert metric["periods"] == [
        {
            "fiscal_year": 2024,
            "fiscal_period": "Q3",
            "filing_date": "2025-08-01",
            "accession_number": "0000320193-25-000073",
            "form_type": "10-Q",
        },
        {
            "fiscal_year": 2024,
            "fiscal_period": "Q4",
            "filing_date": "2025-10-31",
            "accession_number": "0000320193-25-000079",
            "form_type": "10-K",
        },
        {
            "fiscal_year": 2025,
            "fiscal_period": "Q1",
            "filing_date": "2026-01-30",
            "accession_number": "0000320193-26-000006",
            "form_type": "10-Q",
        },
        {
            "fiscal_year": 2025,
            "fiscal_period": "Q2",
            "filing_date": "2026-05-01",
            "accession_number": "0000320193-26-000013",
            "form_type": "10-Q",
        },
    ]
    assert metric["public_date"] == "2026-05-01"
    golden("company_financials_ttm", "aapl_grossprofit_2025q1", body)


def test_financials_ttm_silence(client: TestClient) -> None:
    response = client.get("/company/AAPL/financials/ttm", params={"concept": "NoSuchConceptXyz"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Concept 'NoSuchConceptXyz' not found in facts"}

    response = client.get("/company/AAPL/financials/ttm", params={"as_of": "bogus"})
    assert response.status_code == 422
    assert response.json() == {"detail": "as_of must be YYYY-MM-DD or YYYY-QN, got 'bogus'"}

    response = client.get("/company/0001347842/financials/ttm")
    assert response.status_code == 404
    assert response.json() == {"detail": "no XBRL facts at SEC for CIK 0001347842"}


def test_financials_param_validation(client: TestClient) -> None:
    # FastAPI rejects bad query params before the handler runs - no SEC traffic
    assert client.get("/company/AAPL/financials", params={"period": "bogus"}).status_code == 422
    assert client.get("/company/AAPL/financials", params={"view": "bogus"}).status_code == 422
    assert client.get("/company/AAPL/financials", params={"dimensions": "maybe"}).status_code == 422
    assert client.get("/company/AAPL/financials/metrics", params={"period": "bogus"}).status_code == 422
