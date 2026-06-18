"""One-off migration: explode the 8 vcrpy cassette YAMLs into the URL-keyed fixture store.

Reads each cassette with plain pyyaml (format: interactions[].request.{method,uri},
response.{status,headers,body}; body is a str or !!binary -> bytes). Writes one decoded
body file per URL plus a .meta.json sibling via tests/sec_replay.write_fixture.

Kept in the repo as migration evidence. Re-runnable (idempotent: identical bodies skip).

Rules enforced here:
- Body bytes match vcrpy replay exactly: str -> utf-8 encode, !!binary -> bytes as-is
  (this mirrors vcr.serialize.deserialize -> compat.convert_body_to_bytes).
- content-encoding (gzip/deflate) is decoded before writing; fixtures store decoded bytes.
  (Note: vcr recorded with decode_compressed_response=True, so none remain in practice.)
- Same URL + byte-identical body -> one file. Same URL + DIFFERING body -> hard stop,
  unless listed in CONFLICT_RESOLUTIONS with the cassette whose snapshot is canonical.
- Only GET/HEAD expected; any other method is reported and aborts.
- No body >= MAX_FIXTURE_BYTES; if one appears, stop and report (never compress/split).

Run: cd sidecar && uv run python scripts/decompose_cassettes.py
"""

from __future__ import annotations

import gzip
import hashlib
import sys
import zlib
from collections import defaultdict
from pathlib import Path

import yaml

# import the canonical mapping + writer from the test harness (one source of truth)
SIDECAR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SIDECAR / "tests"))
from sec_replay import FIXTURES_ROOT, fixture_relpath, write_fixture  # noqa: E402

CASSETTES_DIR = SIDECAR / "tests" / "cassettes"
MAX_FIXTURE_BYTES = 95_000_000  # plan stop-gate: no fixture body >= 95MB

_Loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

# URLs recorded more than once with genuinely different bodies (SEC data drifted between
# recording sessions). Value = cassette whose snapshot is canonical for the shared fixture.
# company_tickers_exchange.json: the tickers/first_page golden was dumped from this snapshot;
# both ticker tests assert facts (AAPL/Nasdaq, len>5000) true in it, so it keeps goldens byte-identical.
CONFLICT_RESOLUTIONS = {
    "https://www.sec.gov/files/company_tickers_exchange.json": "test_tickers_full_map_and_paging.yaml",
}


def _header(headers: dict, name: str) -> str | None:
    for key, value in (headers or {}).items():
        if key.lower() == name:
            return value[0] if isinstance(value, list) and value else (value if isinstance(value, str) else None)
    return None


def _body_bytes(response: dict) -> bytes:
    body = response.get("body")
    raw = body.get("string") if isinstance(body, dict) else body
    if raw is None:
        return b""
    data = raw if isinstance(raw, bytes) else raw.encode("utf-8")
    encoding = (_header(response.get("headers", {}), "content-encoding") or "").lower()
    if encoding in ("gzip", "x-gzip"):
        return gzip.decompress(data)
    if encoding == "deflate":
        return zlib.decompress(data)
    if encoding:
        raise SystemExit(f"unhandled content-encoding {encoding!r} -- decode it explicitly before writing")
    return data


def main() -> int:
    # url -> { body_sha256 -> {body, status, content_type, cassettes:set} }
    variants: dict[str, dict[str, dict]] = defaultdict(dict)
    other_methods: list[tuple[str, str, str]] = []

    for cassette in sorted(CASSETTES_DIR.glob("*.yaml")):
        with open(cassette, "rb") as handle:
            doc = yaml.load(handle, Loader=_Loader)
        for interaction in doc.get("interactions", []):
            request = interaction["request"]
            method, url = request["method"], request["uri"]
            if method not in ("GET", "HEAD"):
                other_methods.append((method, url, cassette.name))
                continue
            response = interaction["response"]
            status = response.get("status", {})
            code = status.get("code") if isinstance(status, dict) else status
            if code is None:
                raise SystemExit(f"interaction without a status code: {method} {url} ({cassette.name})")
            body = _body_bytes(response)
            digest = hashlib.sha256(body).hexdigest()
            slot = variants[url].setdefault(
                digest,
                {"body": body, "status": int(code), "content_type": _header(response.get("headers", {}), "content-type"), "cassettes": set()},
            )
            slot["cassettes"].add(cassette.name)

    if other_methods:
        print("ABORT: non-GET/HEAD methods recorded:")
        for method, url, name in other_methods:
            print(f"  {method} {url}  ({name})")
        return 1

    # resolve conflicts (same URL, differing bodies)
    resolved: dict[str, dict] = {}
    unresolved: list[str] = []
    for url, by_hash in variants.items():
        if len(by_hash) == 1:
            resolved[url] = next(iter(by_hash.values()))
            continue
        preferred = CONFLICT_RESOLUTIONS.get(url)
        pick = next((v for v in by_hash.values() if preferred in v["cassettes"]), None) if preferred else None
        if pick is None:
            unresolved.append(url)
            continue
        resolved[url] = pick
        others = sorted(len(v["body"]) for v in by_hash.values())
        print(f"CONFLICT RESOLVED: {url}\n  picked {len(pick['body'])}B from {preferred} (variants: {others})")

    if unresolved:
        print("ABORT: same URL recorded with differing bodies and no resolution:")
        for url in unresolved:
            print(f"  {url}")
            for digest, v in variants[url].items():
                print(f"    sha={digest[:12]} {len(v['body'])}B status={v['status']} in={sorted(v['cassettes'])}")
        return 1

    # 95MB stop-gate
    oversized = [(url, len(v["body"])) for url, v in resolved.items() if len(v["body"]) >= MAX_FIXTURE_BYTES]
    if oversized:
        print(f"ABORT: fixture body >= {MAX_FIXTURE_BYTES} bytes (never compress/split):")
        for url, size in oversized:
            print(f"  {size:,}B  {url}\n     -> {FIXTURES_ROOT / fixture_relpath(url)}")
        return 1

    written = 0
    for url, v in sorted(resolved.items()):
        if write_fixture(url, v["status"], v["content_type"], v["body"]):
            written += 1

    # stats
    per_host: dict[str, list[int]] = defaultdict(list)
    total = 0
    sizes: list[tuple[int, str]] = []
    for url, v in resolved.items():
        size = len(v["body"])
        total += size
        per_host[fixture_relpath(url).parts[0]].append(size)
        sizes.append((size, str(fixture_relpath(url))))

    print(f"\nDONE: {len(resolved)} fixtures ({written} newly written), {total:,} bytes total")
    print("per-host:")
    for host, host_sizes in sorted(per_host.items()):
        print(f"  {host}: {len(host_sizes)} files, {sum(host_sizes):,} bytes")
    print("largest 5:")
    for size, rel in sorted(sizes, reverse=True)[:5]:
        print(f"  {size:>12,}B  {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
