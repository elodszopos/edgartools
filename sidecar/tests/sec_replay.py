"""URL-keyed SEC fixture store + httpx replay transport (replaces vcrpy).

One file per SEC URL under tests/fixtures/sec/<host>/<path...>; bodies stored DECODED
(no content-encoding on disk), status + content-type in a sibling <body>.meta.json.

Replay (default): every httpx request resolves to a fixture; a miss is a hard error
naming the URL, the mapped path, and the record flag -- never a silent network call.
Record (EDGAR_FIXTURE_RECORD=1): pass through to the real transport, persist body+meta,
then serve; caps NEW files per run at RECORD_BUDGET. The store is the sole arbiter of
what tests see, so the harness disables edgartools' disk HTTP cache + rate limiter.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qsl, urlencode, urlsplit

import httpx

# tests/fixtures/sec — module is tests/sec_replay.py
FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "sec"

RECORD_BUDGET = 60  # plan: SEC recording budget — hard cap on NEW fixtures per run
_recorded = {"count": 0}

# filesystem-hostile -> '_' in path segments; '.' kept (real SEC names carry it), '..' rejected upstream
_UNSAFE_SEGMENT = re.compile(r"[^A-Za-z0-9._-]")
_UNSAFE_HINT = re.compile(r"[^A-Za-z0-9]+")
_HOST_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*$")


class FixtureMissError(RuntimeError):
    """Replay hit a URL with no recorded fixture."""


def _canonical_query(query: str) -> str:
    # sort params (blanks kept, dup pairs kept) so param order can't fork the key
    return urlencode(sorted(parse_qsl(query, keep_blank_values=True)))


def _query_hint(canonical_query: str) -> str:
    slug = _UNSAFE_HINT.sub("-", canonical_query).strip("-").lower()
    return slug[:40].strip("-") or "q"


def fixture_relpath(url: str) -> PurePosixPath:
    """Pure deterministic URL -> store-relative path. Raises on traversal / hostile host.

    Query strings: filename = last-path-segment + '__' + readable-hint + '-' + sha256[:12]
    of the canonicalized (sorted) query. This is the ONE place the mapping is defined.
    """
    parts = urlsplit(url)
    host = (parts.hostname or "").lower().rstrip(".")
    if not host or ".." in host or not _HOST_RE.match(host):
        raise ValueError(f"unsafe or missing host in url: {url!r}")

    segments: list[str] = []
    for seg in parts.path.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            raise ValueError(f"path traversal segment in url: {url!r}")
        segments.append(_UNSAFE_SEGMENT.sub("_", seg))

    if segments:
        *dirs, filename = segments
    else:
        dirs, filename = [], "index"

    if parts.query:
        canon = _canonical_query(parts.query)
        digest = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]
        filename = f"{filename}__{_query_hint(canon)}-{digest}"

    relpath = PurePosixPath(host, *dirs, filename)

    # defense in depth: the mapped path must stay under the store root
    root = FIXTURES_ROOT.resolve()
    resolved = (root / relpath).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"mapped path escapes store root: {url!r}")
    return relpath


def body_fs_path(url: str) -> Path:
    return FIXTURES_ROOT / fixture_relpath(url)


def meta_fs_path(url: str) -> Path:
    body = body_fs_path(url)
    return body.with_name(body.name + ".meta.json")


def _render_meta(url: str, status: int, content_type: str | None) -> str:
    headers: dict[str, str] = {}
    if content_type:
        headers["content-type"] = content_type
    meta = {"url": url, "status": int(status), "headers": headers}
    return json.dumps(meta, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def write_fixture(url: str, status: int, content_type: str | None, body: bytes) -> bool:
    """Persist body + meta. Returns True when the body file is newly created."""
    body_path = body_fs_path(url)
    meta_path = meta_fs_path(url)
    newly = not body_path.exists()
    body_path.parent.mkdir(parents=True, exist_ok=True)
    if newly or body_path.read_bytes() != body:
        body_path.write_bytes(body)
    rendered = _render_meta(url, status, content_type)
    if not meta_path.exists() or meta_path.read_text("utf-8") != rendered:
        meta_path.write_text(rendered, encoding="utf-8")
    return newly


def read_fixture(url: str) -> tuple[int, dict[str, str], bytes] | None:
    body_path = body_fs_path(url)
    meta_path = meta_fs_path(url)
    if not body_path.exists() or not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text("utf-8"))
    return int(meta["status"]), dict(meta.get("headers", {})), body_path.read_bytes()


def _response(request: httpx.Request, status: int, headers: dict[str, str], body: bytes) -> httpx.Response:
    # content= lets httpx set content-length == len(body); no content-encoding is claimed
    out: list[tuple[str, str]] = []
    ct = headers.get("content-type")
    if ct:
        out.append(("content-type", ct))
    return httpx.Response(status_code=status, headers=out, content=body, request=request)


def _serve(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    fixture = read_fixture(url)
    if fixture is None:
        try:
            mapped = str(FIXTURES_ROOT / fixture_relpath(url))
        except ValueError as exc:
            mapped = f"<unmappable: {exc}>"
        raise FixtureMissError(
            f"No SEC fixture for {request.method} {url}\n"
            f"  expected store file: {mapped}\n"
            f"  record it by re-running with EDGAR_FIXTURE_RECORD=1 "
            f"(migration: scripts/decompose_cassettes.py)"
        )
    status, headers, body = fixture
    if request.method == "HEAD":
        body = b""
    return _response(request, status, headers, body)


def _capture(request: httpx.Request, net: httpx.Response) -> httpx.Response:
    # net.read() yields httpx-decoded bytes: HTTP content-encoding is undone, while a
    # gzip *file* payload (e.g. full-index/form.gz, no content-encoding header) stays raw.
    body = net.read()
    content_type = net.headers.get("content-type")
    if write_fixture(str(request.url), net.status_code, content_type, body):
        _recorded["count"] += 1
        if _recorded["count"] > RECORD_BUDGET:
            raise RuntimeError(
                f"SEC recording budget exceeded: more than {RECORD_BUDGET} new fixtures written in one run (plan: edgar-sidecar.md, recording budget)"
            )
    return _response(request, net.status_code, {"content-type": content_type} if content_type else {}, body)


def install_replay(mp) -> None:
    """Route ALL httpx traffic through the store; disable cache+throttle so it is sole arbiter."""
    from edgar.httpclient import HTTP_MGR

    mp.setattr(HTTP_MGR, "cache_mode", "Disabled")
    mp.setattr(HTTP_MGR, "rate_limiter_enabled", False)
    HTTP_MGR.close()  # drop any client built with the real transport chain

    def _sync(self: httpx.HTTPTransport, request: httpx.Request) -> httpx.Response:
        return _serve(request)

    async def _async(self: httpx.AsyncHTTPTransport, request: httpx.Request) -> httpx.Response:
        return _serve(request)

    mp.setattr(httpx.HTTPTransport, "handle_request", _sync)
    mp.setattr(httpx.AsyncHTTPTransport, "handle_async_request", _async)


def install_record(mp) -> None:
    """Pass through to the real network, persist, then serve. Throttle stays ON (respect SEC)."""
    from edgar.httpclient import HTTP_MGR

    orig_sync = httpx.HTTPTransport.handle_request
    orig_async = httpx.AsyncHTTPTransport.handle_async_request

    mp.setattr(HTTP_MGR, "cache_mode", "Disabled")  # every request must reach the recorder
    HTTP_MGR.close()

    def _sync(self: httpx.HTTPTransport, request: httpx.Request) -> httpx.Response:
        return _capture(request, orig_sync(self, request))

    async def _async(self: httpx.AsyncHTTPTransport, request: httpx.Request) -> httpx.Response:
        return _capture(request, await orig_async(self, request))

    mp.setattr(httpx.HTTPTransport, "handle_request", _sync)
    mp.setattr(httpx.AsyncHTTPTransport, "handle_async_request", _async)
