"""Integration (U55a): the 424B prospectus family over the one `Prospectus424B` -> kind=prospectus_424b.

Every 424B variant (B1/B2/B3/B4/B5/B7/B8, +/A) maps to the one object; the variant is the `form`
field and `offering_type` is the classifier's verdict. Nine fixtures pin the matrix:

  kentucky      424B1  unknown                debt, multi-entity, underwriting only
  americamovil  424B2  debt_offering          preliminary supplement, capitalization + 9 underwriters
  bofa          424B2  structured_note        pricing grid + structured-note key terms
  amaze         424B3  pipe_resale            resale: selling stockholders + offering terms (pricing None)
  bone          424B4  best_efforts           priced IPO: pricing + dilution + capitalization
  jefferies     424B5  structured_note        EX-FILING FEES XBRL exhibit (457(r) row, CLEAN -- not the
                                              HTML-extractor misalignment) + structured-note terms
  avalonbay     424B5  firm_commitment        REIT shelf takedown: 8-underwriter syndicate
  chewy         424B7  base_prospectus_update WKSI update (type hardcoded) + filing-fees XBRL
  citi          424B8  structured_note        supplement: structured-note terms + filing-fees (header
                                              totals present, zero rows)

The selling-stockholders / underwriting legs come from edgar HTML extractors that OVER-TRIGGER on
non-table prose (header fragments, risk-factor paragraphs) -- the sidecar mirrors edgar faithfully, so
these asserts target the GENUINE rows that are present, not list purity (U53a precedent).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_KENTUCKY = "0001193125-25-137390"  # 424B1, Kentucky Power Cost Recovery (debt, multi-entity)
_AMERICAMOVIL = "0001140361-25-024100"  # 424B2, America Movil (debt_offering)
_BOFA = "0001918704-25-010277"  # 424B2, Bank of America (structured note)
_AMAZE = "0001554795-25-000169"  # 424B3, Amaze Holdings (pipe resale)
_BONE = "0001641172-25-017063"  # 424B4, Bone Biologics (priced IPO)
_JEFFERIES = "0001140361-25-024029"  # 424B5, Jefferies (filing-fees XBRL + structured note)
_AVALONBAY = "0001104659-25-063879"  # 424B5, AvalonBay (firm-commitment takedown)
_CHEWY = "0001193125-25-145720"  # 424B7, Chewy (WKSI base update + filing-fees XBRL)
_CITI = "0000950103-25-008035"  # 424B8, Citigroup (structured note + filing-fees, zero rows)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _p424b(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "Prospectus424B"  # every 424B variant -> this one object
    assert body["data"] is not None
    assert body["data"]["kind"] == "prospectus_424b"
    return body


def test_424b1_debt_underwriting_only(client: TestClient, golden) -> None:
    body = _p424b(client, _KENTUCKY)
    data = body["data"]
    assert data["form"] == "424B1"
    assert data["offering_type"] == "unknown"
    # envelope company is the SEC filer entity (enriched-accession path), not the SPE named on the
    # cover ("Kentucky Power Cost Recovery LLC") -- a securitization filed under the parent utility
    assert data["company"] == "KENTUCKY POWER CO"
    # base shelf number, deterministic after the file_numbers dedup fix (a co-registrant filing also
    # carries 333-284112-01; document-order dedup keeps the primary registrant's base number first)
    assert data["cover_page"]["registration_number"] == "333-284112"
    assert data["cover_page"]["rule_number"] == "1"
    # underwriting carries allocations; no pricing/resale/fee-exhibit on this debt B1
    uw = data["underwriting"]
    assert uw is not None
    assert uw["underwriters"][0]["name"] == "Jefferies LLC"
    assert uw["underwriters"][0]["shares_allocated"] == "191,099,600"
    assert data["pricing"] is None
    assert data["selling_stockholders"] is None
    assert data["filing_fees"]["has_exhibit"] is False
    golden("filing", "prospectus_424b_kentucky_b1", body)


def test_424b2_debt_offering_capitalization(client: TestClient, golden) -> None:
    body = _p424b(client, _AMERICAMOVIL)
    data = body["data"]
    assert data["form"] == "424B2"
    assert data["offering_type"] == "debt_offering"
    assert data["company"] == "AMERICA MOVIL SAB DE CV/"
    cp = data["cover_page"]
    assert cp["is_supplement"] is True
    assert cp["is_preliminary"] is True
    assert cp["offering_price"] == "preliminary-TBD"  # sentinel kept as-filed, never coerced
    assert cp["base_prospectus_date"] == "June 3, 2025"
    assert data["capitalization"] is not None
    assert len(data["capitalization"]["rows"]) > 5
    assert len(data["underwriting"]["underwriters"]) == 9
    assert data["structured_note_terms"] is None
    assert data["filing_fees"]["has_exhibit"] is False
    golden("filing", "prospectus_424b_americamovil_b2_debt", body)


def test_424b2_structured_note_pricing(client: TestClient, golden) -> None:
    body = _p424b(client, _BOFA)
    data = body["data"]
    assert data["form"] == "424B2"
    assert data["offering_type"] == "structured_note"
    assert data["company"] == "BANK OF AMERICA CORP /DE/"
    assert data["cover_page"]["security_description"] == "$1,000.00 in principal amount of Notes"
    pricing = data["pricing"]
    assert pricing is not None
    assert pricing["columns"][0]["column_label"] == "Per Note"
    assert pricing["columns"][0]["offering_price"] == "$1,000.00"
    assert pricing["columns"][0]["proceeds"] == "$991.00"
    assert data["structured_note_terms"] is not None
    assert data["filing_fees"]["has_exhibit"] is False
    golden("filing", "prospectus_424b_bofa_b2_snote", body)


def test_424b3_resale_selling_stockholders(client: TestClient, golden) -> None:
    body = _p424b(client, _AMAZE)
    data = body["data"]
    assert data["form"] == "424B3"
    assert data["offering_type"] == "pipe_resale"
    assert data["company"] == "AMAZE HOLDINGS, INC."
    cp = data["cover_page"]
    assert cp["offering_price"] == "market-price"  # sentinel kept as-filed
    assert cp["exchange_ticker"] == "AMZE"
    # resale -> selling stockholders; edgar's extractor also lifts header fragments, so assert the
    # GENUINE holder is present rather than list purity (U53a over-trigger precedent)
    ss = data["selling_stockholders"]
    assert ss is not None
    names = [s["name"] for s in ss["stockholders"]]
    assert any("C/M Capital Master Fund" in n for n in names)
    assert data["offering_terms"] is not None
    assert data["pricing"] is None  # resale prospectuses carry no pricing grid
    golden("filing", "prospectus_424b_amaze_b3_resale", body)


def test_424b4_priced_ipo_dilution(client: TestClient, golden) -> None:
    body = _p424b(client, _BONE)
    data = body["data"]
    assert data["form"] == "424B4"
    assert data["offering_type"] == "best_efforts"
    assert data["company"] == "Bone Biologics Corp"
    assert data["cover_page"]["offering_price"] == "$4.00"
    assert data["cover_page"]["exchange_ticker"] == "BBLG"
    pricing = data["pricing"]
    assert pricing is not None
    assert pricing["fee_type"] == "placement_agent_fees"
    assert pricing["columns"][0]["offering_price"] == "$4.00"
    assert pricing["columns"][0]["proceeds"] == "$3.72"
    dil = data["dilution"]
    assert dil is not None
    assert dil["public_offering_price"] == "$4.00"
    assert dil["ntbv_after_offering"] == "$3.99"
    cap = data["capitalization"]
    assert cap is not None
    assert cap["total_stockholders_equity_actual"] == "2,910,902"
    assert cap["total_capitalization_actual"] == "3,162,060"
    golden("filing", "prospectus_424b_bone_b4_ipo", body)


def test_424b5_filing_fees_xbrl_clean_457r(client: TestClient, golden) -> None:
    body = _p424b(client, _JEFFERIES)
    data = body["data"]
    assert data["form"] == "424B5"
    assert data["offering_type"] == "structured_note"
    assert data["company"] == "Jefferies Financial Group Inc."
    assert data["cover_page"]["is_supplement"] is True
    assert data["cover_page"]["offering_amount"] == "$6,777,000"
    snt = data["structured_note_terms"]
    assert snt is not None
    assert snt["issuer"] == "Jefferies Financial Group Inc."
    assert snt["cusip"] == "47233WKC2 / US47233WKC28"
    # filing_fees from the EX-FILING FEES XBRL exhibit (NOT the HTML Exhibit-107 path) -- the 457(r)
    # deferred row is column-CORRECT here (security_type=Debt, the real fee_rate), unlike the U54
    # ASR misalignment which only afflicts the shared HTML extract_registration_fee_table
    ff = data["filing_fees"]
    assert ff["has_exhibit"] is True
    assert ff["form_type"] == "S-3"
    assert ff["total_offering_amount"] == "6,777,000.00"  # as-filed XBRL string, not a parsed float
    assert ff["total_fee_amount"] == "1,037.56"
    assert ff["is_final_prospectus"] is False
    row = ff["offering_rows"][0]
    assert row["security_type"] == "Debt"
    assert row["fee_rate"] == "0.0001531"
    assert row["fee_rule"] == "457(r)"
    golden("filing", "prospectus_424b_jefferies_b5_filingfees", body)


def test_424b5_firm_commitment_syndicate(client: TestClient, golden) -> None:
    body = _p424b(client, _AVALONBAY)
    data = body["data"]
    assert data["form"] == "424B5"
    assert data["offering_type"] == "firm_commitment"
    assert data["company"] == "AVALONBAY COMMUNITIES INC"
    assert data["cover_page"]["is_supplement"] is True
    assert data["cover_page"]["base_prospectus_date"] == "February 23, 2024"
    uw = data["underwriting"]
    assert uw is not None
    assert len(uw["underwriters"]) == 8
    assert uw["underwriters"][0]["name"] == "Wells Fargo Securities"
    assert data["filing_fees"]["has_exhibit"] is False
    golden("filing", "prospectus_424b_avalonbay_b5", body)


def test_424b7_wksi_update_filing_fees(client: TestClient, golden) -> None:
    body = _p424b(client, _CHEWY)
    data = body["data"]
    assert data["form"] == "424B7"
    assert data["offering_type"] == "base_prospectus_update"  # 424B7 hardcoded by the classifier
    assert data["company"] == "Chewy, Inc."
    cp = data["cover_page"]
    assert cp["exchange_ticker"] == "CHWY"
    assert cp["base_prospectus_date"] == "September 15, 2023"
    assert data["pricing"] is not None
    ff = data["filing_fees"]
    assert ff["has_exhibit"] is True
    assert ff["form_type"] == "S-3"
    assert ff["total_offering_amount"] == "1,155,509,017"
    assert ff["total_fee_amount"] == "176,909"
    assert ff["offering_rows"][0]["security_type"] == "Equity"
    golden("filing", "prospectus_424b_chewy_b7_filingfees", body)


def test_424b8_structured_note_supplement(client: TestClient, golden) -> None:
    body = _p424b(client, _CITI)
    data = body["data"]
    assert data["form"] == "424B8"
    assert data["offering_type"] == "structured_note"
    # filer entity is the parent (CITIGROUP INC); the cover issuer is Citigroup Global Markets
    # Holdings Inc. -- the holdco/parent co-registrant structure typical of structured notes
    assert data["company"] == "CITIGROUP INC"
    assert data["cover_page"]["is_supplement"] is True
    snt = data["structured_note_terms"]
    assert snt is not None
    assert snt["pricing_date"] == "June 25, 2025"
    assert snt["maturity_date"] == "Unless earlier redeemed, July 2, 2035"
    assert snt["principal_amount"] == "$1,000 per security"
    # filing-fees exhibit present with header totals but NO per-security rows extracted (real edge)
    ff = data["filing_fees"]
    assert ff["has_exhibit"] is True
    assert ff["total_offering_amount"] == "918,000"
    assert ff["offering_rows"] == []
    golden("filing", "prospectus_424b_citi_b8_snote", body)
