"""Unit tests for the URL-keyed SEC fixture store (pure mapping + store roundtrip, no network)."""

from __future__ import annotations

import httpx
import pytest
import sec_replay
from sec_replay import FixtureMissError, fixture_relpath


def _rel(url: str) -> str:
    return str(fixture_relpath(url))


# --- URL -> path mapping ---------------------------------------------------


def test_plain_path_maps_to_host_dir_and_filename() -> None:
    assert _rel("https://data.sec.gov/submissions/CIK0000320193.json") == "data.sec.gov/submissions/CIK0000320193.json"
    assert _rel("https://www.sec.gov/Archives/edgar/full-index/2025/QTR1/form.gz") == ("www.sec.gov/Archives/edgar/full-index/2025/QTR1/form.gz")


def test_root_or_empty_path_uses_index_filename() -> None:
    assert _rel("https://www.sec.gov/") == "www.sec.gov/index"
    assert _rel("https://www.sec.gov") == "www.sec.gov/index"


def test_host_is_lowercased_and_trailing_dot_stripped() -> None:
    assert _rel("https://DATA.SEC.GOV./submissions/x.json") == "data.sec.gov/submissions/x.json"


def test_query_appends_hint_and_stable_hash() -> None:
    rel = _rel("https://efts.sec.gov/LATEST/search-index?q=supply+chain&ciks=0000320193")
    head, _, tail = rel.rpartition("/")
    assert head == "efts.sec.gov/LATEST"
    assert tail.startswith("search-index__")
    # hint is readable; suffix is the 12-hex sha of the canonical query
    digest = tail.rsplit("-", 1)[-1]
    assert len(digest) == 12 and all(c in "0123456789abcdef" for c in digest)


def test_mapping_is_deterministic() -> None:
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&count=10&type=&output=atom"
    assert _rel(url) == _rel(url)


def test_query_param_order_does_not_fork_the_key() -> None:
    a = _rel("https://efts.sec.gov/LATEST/search-index?q=x&forms=8-K&from=10")
    b = _rel("https://efts.sec.gov/LATEST/search-index?from=10&forms=8-K&q=x")
    assert a == b


def test_distinct_queries_get_distinct_files() -> None:
    base = "https://efts.sec.gov/LATEST/search-index?q=cyber&forms=8-K"
    assert _rel(base) != _rel(base + "&from=10")


def test_blank_query_value_is_preserved_in_key() -> None:
    # type= (empty) must not collapse onto a no-type request
    assert _rel("https://www.sec.gov/cgi-bin/browse-edgar?action=x&type=") != _rel("https://www.sec.gov/cgi-bin/browse-edgar?action=x")


def test_real_corpus_urls_do_not_collide() -> None:
    urls = [
        "https://data.sec.gov/submissions/CIK0000320193.json",
        "https://data.sec.gov/submissions/CIK0000815097.json",
        "https://www.sec.gov/files/company_tickers.json",
        "https://www.sec.gov/files/company_tickers_exchange.json",
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&count=10&type=&output=atom",
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&count=40&type=4&output=atom",
        "https://efts.sec.gov/LATEST/search-index?q=supply+chain&ciks=0000320193",
        "https://efts.sec.gov/LATEST/search-index?q=cyber&forms=8-K",
    ]
    mapped = [_rel(u) for u in urls]
    assert len(set(mapped)) == len(mapped)


# --- traversal / hostile guards --------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://www.sec.gov/a/../../etc/passwd",
        "https://www.sec.gov/../secret",
        "https://www.sec.gov/x/..",
    ],
)
def test_path_traversal_is_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        fixture_relpath(url)


@pytest.mark.parametrize("url", ["https:///nohost", "file:///etc/passwd", "https://under_score/x"])
def test_missing_or_hostile_host_is_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        fixture_relpath(url)


def test_hostile_path_chars_are_sanitized_under_root() -> None:
    rel = fixture_relpath("https://www.sec.gov/a b/c:d*e")
    assert ".." not in str(rel)
    # every segment is filesystem-safe
    for seg in rel.parts:
        assert all(ch.isalnum() or ch in "._-" for ch in seg)


# --- store roundtrip + replay miss -----------------------------------------


@pytest.fixture
def temp_store(tmp_path, monkeypatch):
    monkeypatch.setattr(sec_replay, "FIXTURES_ROOT", tmp_path)
    return tmp_path


def test_meta_and_body_roundtrip(temp_store) -> None:
    url = "https://data.sec.gov/submissions/CIK0000999999.json"
    body = b'{"cik": 999999, "name": "x"}'
    newly = sec_replay.write_fixture(url, 200, "application/json", body)
    assert newly is True
    assert sec_replay.write_fixture(url, 200, "application/json", body) is False  # idempotent

    fixture = sec_replay.read_fixture(url)
    assert fixture is not None
    status, headers, read_body = fixture
    assert status == 200
    assert headers == {"content-type": "application/json"}
    assert read_body == body


def test_binary_body_roundtrip_is_byte_exact(temp_store) -> None:
    url = "https://www.sec.gov/Archives/edgar/full-index/1995/QTR1/form.gz"
    body = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03rawgzip\xff\x00"
    sec_replay.write_fixture(url, 200, "binary/octet-stream", body)
    fixture = sec_replay.read_fixture(url)
    assert fixture is not None
    assert fixture[2] == body


def test_read_fixture_missing_returns_none(temp_store) -> None:
    assert sec_replay.read_fixture("https://data.sec.gov/submissions/CIK0000000001.json") is None


def test_serve_replay_miss_raises_loud_error(temp_store) -> None:
    request = httpx.Request("GET", "https://data.sec.gov/submissions/CIK0000000001.json")
    with pytest.raises(FixtureMissError) as exc:
        sec_replay._serve(request)
    message = str(exc.value)
    assert "CIK0000000001.json" in message  # names the URL
    assert "EDGAR_FIXTURE_RECORD=1" in message  # names the record flag
    assert str(temp_store) in message  # names the mapped store path


def test_serve_returns_recorded_status_and_body(temp_store) -> None:
    url = "https://data.sec.gov/submissions/CIK9999999999.json"
    sec_replay.write_fixture(url, 404, "application/xml", b"<error>not found</error>")
    response = sec_replay._serve(httpx.Request("GET", url))
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/xml"
    assert response.headers["content-length"] == str(len(b"<error>not found</error>"))
    assert response.content == b"<error>not found</error>"
