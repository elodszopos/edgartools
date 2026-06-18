"""Integration (U54): the S-3 / F-3 shelf-registration family over the one `RegistrationS3` ->
kind=registration_s3.

Six fixtures pin the dispatch + structural matrix. S-3, S-3ASR, S-3/A, F-3, F-3ASR all dispatch to
RegistrationS3 (matches_form expands each base form to its /A amendment); what differs is the
offering-type classification and which fee-table shape appears:

  central_pacific  S-3      domestic universal shelf -> the full multi-security fee table (9 rows:
                            8 unallocated security types + 1 "Unallocated (Universal) Shelf" row that
                            carries the $300M total + fee); offering_type=universal_shelf
  aerovironment    S-3ASR   domestic automatic shelf -> is_auto_shelf, Rule 462(e), DEFERRED fees
                            (total/net == 0.0, fee_deferred=True); offering_type=auto_shelf
  bakkt            S-3      resale shelf -> Exhibit 107 located but totals/securities do not parse ->
                            fee_table is a non-None SHELL (distinct from genuine None); high-conf cover
  tss              S-3/A    amendment -> is_amendment, NO Exhibit 107 -> fee_table is genuinely None
  cn_energy        F-3      foreign (Cayman) resale shelf -> single-security fee table, real amounts
  takeda           F-3ASR   foreign automatic shelf -> is_auto_shelf, DEFERRED fees

S-3 has none of S-1's prospectus tables (selling stockholders / dilution / capitalization /
underwriting) -- shelf registrations incorporate financials by reference. edgar's _fee_table
extractor column-misaligns DEFERRED Rule 457(r) ASR tables (row index -> security_type, type ->
title, "457(r)" -> amount_registered); the sidecar mirrors edgar's output faithfully, so the
aerovironment/takeda goldens carry those raw cells -- the asserts below pin the high-confidence
structural facts (deferred, zero totals, row count), not the misaligned per-cell strings.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_CENTRAL_PACIFIC = "0001140361-25-024210"  # S-3 universal shelf, Central Pacific Financial Corp
_AEROVIRONMENT = "0001104659-25-064107"  # S-3ASR auto shelf, AeroVironment Inc (deferred fees)
_BAKKT = "0001193125-25-149177"  # S-3 resale, Bakkt Holdings (fee-table shell)
_TSS = "0001654954-25-007450"  # S-3/A amendment, TSS, Inc. (fee_table None)
_CN_ENERGY = "0001477932-25-004859"  # F-3 foreign resale, CN Energy Group
_TAKEDA = "0001395064-25-000097"  # F-3ASR foreign auto shelf, Takeda Pharmaceutical


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _s3(client: TestClient, accession: str) -> dict:
    response = client.get(f"/filing/{accession}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["obj_type"] == "RegistrationS3"  # S-3 and F-3 (+ASR, +/A) all -> RegistrationS3
    assert body["data"] is not None
    assert body["data"]["kind"] == "registration_s3"
    return body


def test_s3_universal_shelf_fee_table(client: TestClient, golden) -> None:
    body = _s3(client, _CENTRAL_PACIFIC)
    data = body["data"]
    assert data["form"] == "S-3"
    assert data["is_amendment"] is False
    assert data["is_auto_shelf"] is False
    assert data["offering_type"] == "universal_shelf"
    assert data["company"] == "CENTRAL PACIFIC FINANCIAL CORP"

    cover = data["cover_page"]
    assert cover["company_name"] == "CENTRAL PACIFIC FINANCIAL CORP"
    assert cover["ein"] == "99-0212597"

    # the universal-shelf fee table: 8 unallocated security-type rows + the aggregate row carrying
    # the $300M total and the $45,930 fee (the per-type rows have no allocated amounts)
    ft = data["fee_table"]
    assert ft is not None
    assert ft["total_offering_amount"] == 300000000.0
    assert ft["net_fee_due"] == 45930.0
    assert ft["fee_deferred"] is False
    assert len(ft["securities"]) == 9
    assert ft["securities"][0]["security_type"] == "Equity"
    assert ft["securities"][0]["security_title"] == "Common Stock, no par value per share"
    agg = ft["securities"][8]
    assert agg["security_title"] == "Unallocated (Universal) Shelf"
    assert agg["max_aggregate_amount"] == 300000000.0
    assert agg["fee_amount"] == 45930.0
    golden("filing", "registration_s3_central_pacific_universal", body)


def test_s3asr_auto_shelf_deferred_fees(client: TestClient, golden) -> None:
    body = _s3(client, _AEROVIRONMENT)
    data = body["data"]
    assert data["form"] == "S-3ASR"
    assert data["is_amendment"] is False
    assert data["is_auto_shelf"] is True
    assert data["offering_type"] == "auto_shelf"
    assert data["company"] == "AeroVironment Inc"

    cover = data["cover_page"]
    assert cover["state_of_incorporation"] == "Delaware"
    assert cover["ein"] == "95-2705790"
    assert cover["is_rule_462e"] is True  # automatic shelf (WKSI)

    # deferred Rule 457(r) fee table: no fee paid at filing -> zero totals, fee_deferred flag set
    ft = data["fee_table"]
    assert ft is not None
    assert ft["fee_deferred"] is True
    assert ft["total_offering_amount"] == 0.0
    assert ft["net_fee_due"] == 0.0
    assert len(ft["securities"]) == 6
    golden("filing", "registration_s3_aerovironment_s3asr", body)


def test_s3_resale_fee_shell(client: TestClient, golden) -> None:
    body = _s3(client, _BAKKT)
    data = body["data"]
    assert data["form"] == "S-3"
    assert data["is_auto_shelf"] is False
    assert data["offering_type"] == "resale"
    assert data["company"] == "Bakkt Holdings, Inc."

    cover = data["cover_page"]
    assert cover["state_of_incorporation"] == "Delaware"
    assert cover["ein"] == "98-1550750"
    assert cover["confidence"] == "high"
    assert cover["is_smaller_reporting_company"] is True
    assert cover["is_rule_415"] is True
    assert cover["is_rule_462b"] is True

    # Exhibit 107 located (exhibit_url set) but totals/securities do not parse -> non-None shell;
    # the genuine fee_table=None branch is covered by tss below
    ft = data["fee_table"]
    assert ft is not None
    assert ft["total_offering_amount"] is None
    assert ft["securities"] == []
    assert ft["exhibit_url"].endswith("d84171dexfilingfees.htm")
    golden("filing", "registration_s3_bakkt_resale", body)


def test_s3a_amendment_no_fee_table(client: TestClient, golden) -> None:
    body = _s3(client, _TSS)
    data = body["data"]
    assert data["form"] == "S-3/A"
    assert data["is_amendment"] is True
    assert data["is_auto_shelf"] is False
    assert data["offering_type"] == "universal_shelf"
    assert data["company"] == "TSS, Inc."

    cover = data["cover_page"]
    assert cover["registration_number"] == "333-284153"
    assert cover["state_of_incorporation"] == "Delaware"
    assert cover["ein"] == "20-2027651"
    assert cover["is_rule_415"] is True

    # the amendment carries no Exhibit 107 -> genuinely None (not a shell)
    assert data["fee_table"] is None
    golden("filing", "registration_s3_tss_s3a_amendment", body)


def test_f3_foreign_resale_shelf(client: TestClient, golden) -> None:
    body = _s3(client, _CN_ENERGY)
    data = body["data"]
    assert data["form"] == "F-3"
    assert data["is_amendment"] is False
    assert data["offering_type"] == "resale"
    assert data["company"] == "CN ENERGY GROUP. INC."

    cover = data["cover_page"]
    assert cover["state_of_incorporation"] == "Not Applicable"  # foreign private issuer
    assert cover["is_rule_415"] is True

    ft = data["fee_table"]
    assert ft is not None
    assert ft["total_offering_amount"] == 86914697.7
    assert ft["net_fee_due"] == 13306.64
    assert len(ft["securities"]) == 1
    sec0 = ft["securities"][0]
    assert sec0["security_type"] == "Equity"
    assert sec0["security_title"].startswith("Class A Ordinary Shares")
    assert sec0["amount_registered"] == "32,012,780"
    assert sec0["price_per_unit"] == 2.72
    assert sec0["max_aggregate_amount"] == 86914697.7
    assert sec0["fee_amount"] == 13306.64
    golden("filing", "registration_s3_cn_energy_f3", body)


def test_f3asr_foreign_auto_shelf(client: TestClient, golden) -> None:
    body = _s3(client, _TAKEDA)
    data = body["data"]
    assert data["form"] == "F-3ASR"
    assert data["is_amendment"] is False
    assert data["is_auto_shelf"] is True
    assert data["offering_type"] == "auto_shelf"
    assert data["company"] == "TAKEDA PHARMACEUTICAL CO LTD"

    cover = data["cover_page"]
    assert cover["ein"] == "33-1784620"
    assert cover["is_rule_462e"] is True

    ft = data["fee_table"]
    assert ft is not None
    assert ft["fee_deferred"] is True
    assert ft["total_offering_amount"] == 0.0
    assert len(ft["securities"]) == 3
    golden("filing", "registration_s3_takeda_f3asr", body)
