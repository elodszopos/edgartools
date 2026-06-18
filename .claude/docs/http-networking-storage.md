## HTTP, Networking & Storage

### Overview

This domain governs every interaction EdgarTools has with SEC EDGAR: throttled/cached HTTP via `httpx` + `httpxthrottlecache`, retry logic with SSL fail-fast, identity (User-Agent) enforcement, bulk filing download and extraction, local/cloud/datamule storage abstraction, and a standalone SSL diagnostic tool. It sits at the lowest layer of the library — all filing data flows through these modules before reaching entity, XBRL, or document parsers.

---

### Public API surface

| Symbol | file:line | Purpose |
|---|---|---|
| `configure_http` | `edgar/httpclient.py:211` | Runtime SSL/proxy/timeout reconfiguration |
| `get_http_config` | `edgar/httpclient.py:292` | Read current HTTP client settings |
| `use_local_storage` | `edgar/storage/_local.py:67` | Enable/disable local storage, optionally set path |
| `use_cloud_storage` | `edgar/filesystem.py:52` | Configure S3/GCS/Azure/R2/MinIO cloud backend |
| `use_datamule_storage` | `edgar/storage/datamule/storage.py:29` | Point to a directory of datamule `.tar` files |
| `download_edgar_data` | `edgar/storage/_local.py:258` | Bulk-download SEC metadata (submissions + facts + reference) |
| `download_filings` | `edgar/storage/_local.py:302` | Download per-date `.nc.tar.gz` filing feed files |
| `sync_to_cloud` | `edgar/filesystem.py:757` | Upload local filings to configured cloud storage |
| `diagnose_ssl` | `edgar/diagnose_ssl/__init__.py:36` | Run full SSL connectivity diagnostic, display results |
| `storage_info` | `edgar/storage/_management.py:250` | Get local storage statistics (Rich display) |
| `analyze_storage` | `edgar/storage/_management.py:355` | Storage analysis with optimization recommendations |
| `optimize_storage` | `edgar/storage/_management.py:482` | Compress uncompressed local files |
| `cleanup_storage` | `edgar/storage/_management.py:561` | Delete filings older than N days |
| `clear_cache` | `edgar/storage/_management.py:647` | Delete HTTP cache dirs (`_tcache`, `_pcache`) |
| `TooManyRequestsError` | `edgar/httprequests.py:136` | Raised on HTTP 429 |
| `SSLVerificationError` | `edgar/httprequests.py:537` | Raised on SSL certificate failure (with diagnostics) |
| `get_with_retry` | `edgar/httprequests.py:667` | GET with retry + identity enforcement |
| `stream_with_retry` | `edgar/httprequests.py:749` | Streaming GET with retry |
| `download_file` | `edgar/httprequests.py:972` | Download a file (text or binary, handles `.gz`) |
| `download_bulk_data` | `edgar/httprequests.py:1259` | Download and extract zip/tar.gz archives with progress |
| `local_filing_path` | `edgar/storage/_local.py:850` | Resolve local or cloud path for a filing |
| `is_using_local_storage` | `edgar/storage/_local.py:136` | Query `EDGAR_USE_LOCAL_DATA` env flag |
| `is_using_datamule_storage` | `edgar/storage/datamule/storage.py:68` | Query datamule active state |
| `is_cloud_storage_enabled` | `edgar/filesystem.py:246` | Query cloud storage active state |
| `EdgarPath` | `edgar/filesystem.py:349` | Path-like object for local or cloud files |
| `get_datamule_filing` | `edgar/storage/datamule/storage.py:73` | Load a `FilingSGML` from datamule tar by accession number |

---

### Key classes

**`HttpxThrottleCache` (HTTP_MGR singleton)** — wraps `httpx.Client` with rate limiting, file-based caching (`Hishel-File`), user-agent injection, and connection keepalive. Instantiated once at module load in `edgar/httpclient.py:323`.

Key methods of `HTTP_MGR` (from `httpxthrottlecache` library):
- `http_client(**kwargs) -> Generator[httpx.Client]` — context manager yielding a sync client — `edgar/httpclient.py:197`
- `async_http_client(**kwargs) -> AsyncGenerator[httpx.AsyncClient]` — async variant — `edgar/httpclient.py:192`
- `close()` — closes persistent client — called by `close_clients()` at `edgar/httpclient.py:207`

**`TooManyRequestsError`** (`edgar/httprequests.py:136`) — raised on HTTP 429. Carries `url`, `retry_after` (from `Retry-After` header). Includes a detailed multi-paragraph error message explaining SEC's 10-req/s limit and ~10-minute IP block. Constructor extracts `Retry-After` as both integer seconds and HTTP date formats via `_get_retry_after()` at line 583.

**`SSLVerificationError`** (`edgar/httprequests.py:537`) — raised when `ConnectError` is SSL-related. Constructor categorizes the error via `_categorize_ssl_error()` (line 255), gathers diagnostic state via `_get_ssl_diagnostic()` (line 282), and builds a targeted multi-section error message. Carries `original_error`, `url`, `category` (`SSLErrorCategory` enum), and `diagnostic` (`SSLDiagnostic` dataclass).

**`SSLDiagnostic`** (`edgar/httprequests.py:216`) — dataclass:

| Field | Type | Purpose |
|---|---|---|
| `configured_verify` | `bool` | What `HTTP_MGR.httpx_params["verify"]` is set to |
| `client_exists` | `bool` | Whether HTTP client is already instantiated |
| `client_verify` | `Optional[bool]` | Actual SSL context `check_hostname` from running client |
| `requests_ca_bundle` | `Optional[str]` | `REQUESTS_CA_BUNDLE` env var |
| `ssl_cert_file` | `Optional[str]` | `SSL_CERT_FILE` env var |
| `certifi_path` | `Optional[str]` | Path from `certifi.where()` |

Properties: `mismatch` (detects configure_http called after first request), `custom_ca_configured`, `status` (one of `"MISMATCH"`, `"LIKELY_MISMATCH"`, `"SSL_DISABLED_BUT_FAILED"`, `"CUSTOM_CA_NOT_WORKING"`, `"SSL_ENABLED"`).

**`EdgarPath`** (`edgar/filesystem.py:349`) — path-like adapter for transparent local/cloud I/O. Stores a relative `_path` string; `full_path` prepends `get_storage_root()` which is either a cloud URI or local edgar data dir. Supports: `exists()`, `is_file()`, `is_dir()`, `mkdir()`, `read_text()`, `read_bytes()`, `write_text()`, `write_bytes()`, `open()`, `glob()`, `iterdir()`, `unlink()`, `rmdir()`, `as_local_path()` (local only). Auto-decompresses `.gz` on `read_text()`/`read_bytes()`.

**`StorageInfo`** (`edgar/storage/_management.py:99`) — dataclass with `total_size_bytes`, `total_size_compressed`, `file_count`, `filing_count`, `compression_savings_bytes`, `compression_ratio`, `by_type` dict, `by_year` dict, `last_updated`, `storage_path`. Rich `__rich__` panel display.

**`StorageAnalysis`** (`edgar/storage/_management.py:40`) — dataclass wrapping `StorageInfo` plus `issues: List[str]`, `recommendations: List[str]`, `potential_savings_bytes`. Rich panel display.

**SSL Diagnostic report structures** (`edgar/diagnose_ssl/report.py`):
- `DiagnosticResult` — top-level, holds `EnvironmentInfo`, `CertificateConfig`, `HttpClientState`, `NetworkTestResults`, `ProxyConfig`, `List[CheckResult]`, `List[Recommendation]`. Properties: `ssl_ok`, `all_passed`, `has_warnings`, `has_failures`, `diagnosis`.
- `NetworkTestResults` — DNS (IPv4+IPv6), TCP, SSL handshake, raw HTTP, configured HTTP results.
- `SSLHandshakeResult` — success, error, cert chain, `is_corporate_proxy` flag.
- `CertificateInfo` — subject, issuer, validity dates, `is_corporate_proxy`.
- `CheckResult` — name, `CheckStatus` enum (PASS/FAIL/WARN/SKIP), message, details.
- `Recommendation` — title, description, `code_snippet`, `priority`.

**Datamule classes:**
- `TarSGMLDocument` (`edgar/storage/datamule/documents.py:17`) — subclass of `SGMLDocument`; overrides `content` property to return `raw_content` directly (bypasses SGML tag extraction).
- `_accession_index` (`edgar/storage/datamule/storage.py:26`) — module-level `Dict[str, Path]` mapping normalized accession numbers to `.tar` file paths; populated by `_scan_tars()` at `use_datamule_storage` call time.

**Filing directory / headers** (`edgar/headers.py`):
- `FilingDirectory` — name, parent_dir, items DataFrame. `load(basedir)` fetches `index.json`. `index_headers` property fetches `<accession>-index-headers.html`.
- `IndexHeaders` (Pydantic `BaseModel`) — full filing header parsed from HTML comment in index-headers.html. Nested: `Filer`, `SubjectCompany`, `ReportingOwner`, `Issuer` (each with `CompanyData`, `FilingValues`, `Address`, `FormerCompany`).

---

### Class hierarchy

```
Exception
├── TooManyRequestsError           (edgar/httprequests.py:136)
├── IdentityNotSetException        (edgar/httprequests.py:198)
└── SSLVerificationError           (edgar/httprequests.py:537)

Enum
├── SSLErrorCategory               (edgar/httprequests.py:206)
│   CORPORATE_NETWORK, SELF_SIGNED, EXPIRED, HOSTNAME_MISMATCH,
│   CERT_REVOKED, UNKNOWN
└── CheckStatus                    (edgar/diagnose_ssl/report.py:11)
    PASS, FAIL, WARN, SKIP

pydantic.BaseModel
├── CompanyData                    (edgar/headers.py:86)
├── FilingValues                   (edgar/headers.py:107)
├── FormerCompany                  (edgar/headers.py:114)
├── Filer (headers)                (edgar/headers.py:119)
├── SubjectCompany                 (edgar/headers.py:137)
├── OwnerData                      (edgar/headers.py:155)
├── ReportingOwner                 (edgar/headers.py:176)
├── Issuer                         (edgar/headers.py:196)
└── IndexHeaders                   (edgar/headers.py:216)

dataclass
├── SSLDiagnostic                  (edgar/httprequests.py:216)
├── StorageInfo                    (edgar/storage/_management.py:99)
├── StorageAnalysis                (edgar/storage/_management.py:40)
├── EnvironmentInfo                (edgar/diagnose_ssl/report.py:37)
├── CertificateConfig              (edgar/diagnose_ssl/report.py:48)
├── ProxyConfig                    (edgar/diagnose_ssl/report.py:59)
├── HttpClientState                (edgar/diagnose_ssl/report.py:67)
├── CertificateInfo                (edgar/diagnose_ssl/report.py:79)
├── SSLHandshakeResult             (edgar/diagnose_ssl/report.py:89)
├── NetworkTestResults             (edgar/diagnose_ssl/report.py:99)
├── Recommendation                 (edgar/diagnose_ssl/report.py:116)
├── CheckResult                    (edgar/diagnose_ssl/report.py:19)
└── DiagnosticResult               (edgar/diagnose_ssl/report.py:125)

SGMLDocument  (edgar/sgml/sgml_parser.py)
└── TarSGMLDocument                (edgar/storage/datamule/documents.py:17)

object
├── EdgarPath                      (edgar/filesystem.py:349)
├── FilingDirectory                (edgar/headers.py:24)
└── TerminalFormatter / NotebookFormatter  (edgar/diagnose_ssl/output.py)
```

---

### Configuration & options

#### HTTP client (httpclient.py)

| Option | Type | Default | Effect |
|---|---|---|---|
| `EDGAR_IDENTITY` env | str | (required) | User-Agent header value for SEC compliance |
| `EDGAR_RATE_LIMIT_PER_SEC` env | int | `9` | Requests/sec cap via pyrate-limiter |
| `EDGAR_VERIFY_SSL` env | bool str | `"true"` | SSL verification on/off (read once at module init) |
| `EDGAR_USE_SYSTEM_CERTS` env | bool str | `"false"` | Use OS trust store via `truststore` |
| `EDGAR_LOCAL_DATA_DIR` env | str | `~/.edgar` | Root directory for local cache and filings |
| `configure_http(verify_ssl)` | `Optional[bool]` | `None` | Override SSL verify at runtime; forces client recreation |
| `configure_http(use_system_certs)` | `Optional[bool]` | `None` | Activate `truststore.SSLContext`; takes precedence over verify_ssl |
| `configure_http(proxy)` | `Optional[str]` | `None` | Set proxy URL (supports user:pass@host:port format) |
| `configure_http(timeout)` | `Optional[float]` | `None` | Replace the default timeout at runtime |
| `EDGAR_HTTP_TIMEOUT` env | float str | `"30.0"` | Default timeout (seconds) applied to `HTTP_MGR` at init. Set to `"none"`, `"unlimited"`, or `"0"` to disable. |
| keepalive_expiry | `httpx.Limits` | `30s` | Increased from httpx default 5s for connection reuse |

Cache rules (`_get_cache_rules()` at `httpclient.py:74`):

| URL pattern | TTL | Behavior |
|---|---|---|
| `/submissions.*` | 30s | Revalidate every 30s (Issue #471 reduced from 10min) |
| `/include/ticker.txt.*` | 30s | Same |
| `/files/company_tickers.json.*` | 30s | Same |
| `.*index/.*` | 1800s (30min) | Daily index revalidation |
| `/Archives/edgar/data` | `True` | **Cache forever** — never revalidate |

Cache directory: `EDGAR_LOCAL_DATA_DIR/_tcache` (Hishel file-based cache).

#### Retry constants (httprequests.py)

| Constant | Value | Applied to |
|---|---|---|
| `QUICK_RETRY_ATTEMPTS` | 5 | `get_with_retry`, `post_with_retry`, `stream_with_retry` |
| `QUICK_WAIT_MAX` | 16s | Same |
| `BULK_RETRY_ATTEMPTS` | 8 | `stream_file`, `download_bulk_data` |
| `BULK_WAIT_MAX` | 120s (2min) | Same |
| `BULK_RETRY_TIMEOUT` | `None` (unlimited) | Same |
| `BULK_TIMEOUT` | `Timeout(300, connect=10)` | Bulk stream — 5min read, 10s connect |
| `RETRY_WAIT_INITIAL` | 1s | All retry decorators |
| `wait_exp_base` | 2 | Exponential backoff factor |
| `wait_jitter` | 0.5s | Jitter to avoid synchronized retries |

#### Local storage (storage/_local.py)

| Option | Type | Default | Effect |
|---|---|---|---|
| `EDGAR_USE_LOCAL_DATA` env | bool str | `"False"` | Enable local storage mode |
| `EDGAR_ALLOW_NETWORK_FALLBACK` env | bool str | `"True"` | Allow network if local data missing |
| `use_local_storage(path)` | str/Path/bool | `True` | Enable; sets `EDGAR_LOCAL_DATA_DIR` if path given |
| `use_local_storage(allow_network_fallback=False)` | bool | `True` | Strict offline mode |
| `download_filings(compress)` | bool | `True` | gzip-compress `.nc` files after extraction |
| `download_filings(compression_level)` | int 1-9 | 6 | gzip compression level |
| `download_filings(upload_to_cloud)` | bool | `False` | Auto-sync to cloud after download |

#### Cloud storage (filesystem.py)

| Option | Type | Default | Effect |
|---|---|---|---|
| `use_cloud_storage(uri)` | str | required | Protocol://bucket/prefix |
| `use_cloud_storage(client_kwargs)` | dict | `{}` | Provider-specific credentials/endpoint |
| `use_cloud_storage(verify)` | bool | `True` | Verify connection by listing bucket at setup |
| `use_cloud_storage(disable=True)` | bool | `False` | Reverts to local filesystem |
| `sync_to_cloud(batch_size)` | int | 20 | Concurrent file transfers |
| `sync_to_cloud(overwrite)` | bool | `False` | Skip existing files by default |
| `sync_to_cloud(dry_run)` | bool | `False` | Preview without uploading |

---

### Data flow / lifecycle

#### HTTP request lifecycle

1. Caller invokes `get_with_retry(url)` (or async variant). The `@with_identity` decorator resolves `User-Agent` from `identity` parameter → `identity_callable` → `EDGAR_IDENTITY` env var; raises `IdentityNotSetException` if all are `None`.
2. `@retry(on=should_retry, ...)` from `stamina` wraps the decorated function. `should_retry()` consults `RETRYABLE_EXCEPTIONS` tuple but short-circuits to `False` for SSL errors (these raise `SSLVerificationError` instead).
3. Inside the function, `http_client()` context manager yields an `httpx.Client` from `HTTP_MGR` (already rate-limited and cache-enabled).
4. On HTTP 429: raises `TooManyRequestsError` immediately — not retried (falls outside `RETRYABLE_EXCEPTIONS`).
5. On SSL `ConnectError`: `is_ssl_error()` walks the exception `__cause__` chain; if SSL error, raises `SSLVerificationError` (categorized + diagnostic state captured).
6. On 301/302: recursively calls self with `Location` header.
7. Cache layer: `httpxthrottlecache` intercepts at transport level. Cache-forever rules apply to `/Archives/edgar/data` — corrupted/empty responses can be permanently cached (mitigated by `stream_with_retry(bypass_cache=True)` for bulk downloads, and `clear_empty_cached_responses()` on install).

#### Bulk download lifecycle (download_bulk_data)

1. Calls `stream_file(url, path=download_path)` (bulk retry params: 8 attempts, unlimited timeout, 5min read timeout).
2. `stream_file` creates a `tempfile.mkdtemp(prefix="edgar_")` for atomic download; streams to temp file in adaptive chunks (2MB/4MB/8MB based on `Content-Length`).
3. `shutil.move()` atomically moves temp file to final destination.
4. Post-download: `zipfile.ZipFile` or `tarfile.open("r:gz")` extraction with progress bar.
5. Security: tar extraction checks `os.path.commonpath()` against target directory to prevent path traversal.
6. Archive file always deleted in `finally` block; on error, entire `download_path` directory is cleaned up.

#### Local filing storage lookup

1. `local_filing_path(filing_date, accession_number)` converts date to `YYYYMMDD` format.
2. If `is_cloud_storage_enabled()`: returns `EdgarPath('filings', date, '<accession>.nc')` or `.nc.gz` variant.
3. Otherwise: `get_edgar_data_directory() / 'filings' / date / '<accession>.nc'` — checks `.gz` first.
4. When loading a filing, `FilingSGML.from_source()` first checks local path, with network fallback logged if missing (unless `EDGAR_ALLOW_NETWORK_FALLBACK=0`).

#### Datamule storage lifecycle

1. `use_datamule_storage(path)` resolves and validates the directory, calls `_scan_tars(tar_dir)`.
2. `_scan_tars` iterates all `*.tar` files sorted by name; each is opened and all `*metadata.json` members are read to build the `_accession_index`.
3. Two tar layouts supported: single-filing (metadata.json at root) and batch (accession_no/metadata.json per filing).
4. Accession numbers normalized to dashed format `XXXXXXXXXX-YY-ZZZZZZ`.
5. On lookup: `get_datamule_filing(accession_no)` → finds `tar_path` in index → `load_filing_from_tar()` → reopens tar, locates correct metadata by accession, calls `_build_filing_sgml()`.
6. Document content: decoded via UTF-8 with latin-1 fallback; `_maybe_decompress_zstd()` handles zstd-compressed files (magic bytes `\x28\xb5\x2f\xfd`) using the `zstandard` package.
7. Documents wrapped in `TarSGMLDocument` (SGMLDocument subclass) which bypasses SGML tag extraction — `content` property returns raw content directly.
8. `FilingHeader` built from datamule metadata via `filing_header_from_metadata()` with multi-format key support: kebab-case nested (real datamule), snake_case flat, camelCase flat.

#### Cloud storage filesystem lazy init

1. `_fs` is `None` until first access via `get_filesystem()`.
2. Double-checked lock: fast-path avoids lock if already initialized.
3. On first call: imports `fsspec`, normalizes S3 `client_kwargs` (maps `aws_access_key_id`→`key`, moves `endpoint_url`/`region_name` into nested `client_kwargs` for s3fs compatibility), creates `fsspec.filesystem(protocol, **kwargs)`.
4. `sync_to_cloud` batches files by checking existing files via `fs.ls()` per directory (not per-file `fs.exists()`) to minimize API calls; uses `fs.put(list, list)` for batch uploads; falls back to individual uploads on batch failure.

#### SSL diagnostics flow

1. `diagnose_ssl()` calls `run_diagnostics()` → runs all checks in sequence: `get_environment_info()`, `get_certificate_config()`, `get_proxy_config()`, `get_http_client_state()`, `run_network_tests()`.
2. `run_network_tests()` chain: DNS (IPv4+IPv6) → TCP port 443 → SSL handshake (cert chain without verification, then with) → HTTP raw request (default SSL) → HTTP configured request (user's settings). Each step skipped if prior step fails.
3. `get_certificate_chain()` opens SSL context with `CERT_NONE` to capture chain even if verification fails; uses `cryptography.x509` if available.
4. `_is_corporate_proxy_cert()` uses tiered detection: SSL inspection product names, proxy context words, then unknown issuers not from known CAs.
5. `display_result()` auto-detects Jupyter (`ZMQInteractiveShell`) vs terminal; renders HTML via `NotebookFormatter` or ANSI color via `TerminalFormatter`.

#### Cache invalidation events

- `clear_empty_cached_responses()` (`httpclient.py:326`): one-time cache wipe for Issue #672 (empty responses permanently cached). Uses marker file `.empty_response_fix_672_applied`.
- `clear_locale_corrupted_cache()` (`httpclient.py:375`): one-time cache wipe for Issue #457 (locale-corrupted timestamps). Uses marker `.locale_fix_457_applied`. Both called via `__init__.py` on library import.
- `LC_TIME` forced to `'C'` locale at `httpclient.py:14` to prevent httpxthrottlecache date parsing failures on non-English systems.

---

### Design patterns

- **Decorator-based cross-cutting concerns**: `@with_identity` and `@async_with_identity` inject User-Agent without polluting business logic. `@retry(on=should_retry, ...)` from `stamina` adds exponential-backoff retry declaratively — `edgar/httprequests.py:658-780`.
- **Singleton HTTP manager**: `HTTP_MGR` module-level global (`httpclient.py:323`) — single `HttpxThrottleCache` instance holds rate limiter, cache, and client pool. `configure_http()` mutates it and forces client recreation.
- **Monkey-patch for upstream bug**: `_patched_get_httpx_transport_params` (`httpclient.py:39`) patches `HttpxThrottleCache._get_httpx_transport_params` at import time to pass `verify` param through. Documented with upstream issue link and TODO to remove on fix.
- **Two retry tiers**: QUICK (5 attempts, 16s max delay) for interactive API requests; BULK (8 attempts, 120s max, unlimited total timeout) for large archive downloads.
- **SSL fail-fast**: `should_retry()` returns `False` for SSL errors — they are deterministic failures that won't succeed on retry. Dedicated `SSLVerificationError` with categorized diagnostics is raised instead.
- **Atomic downloads**: `stream_file` downloads to `tempfile.mkdtemp` then `shutil.move()` to final path — prevents partial files on crash/interrupt.
- **Lazy double-checked locking**: `get_filesystem()` uses `_config_lock` with double-check pattern for thread-safe lazy fsspec initialization.
- **Accession index pattern**: datamule builds a full in-memory `Dict[str, Path]` index at configuration time for O(1) tar lookup — `edgar/storage/datamule/storage.py:26`.
- **Storage statistics caching**: `_scan_storage()` caches `StorageInfo` for 60 seconds (`_CACHE_TTL = 60.0`) to avoid repeated filesystem scans.
- **Transparent local/cloud path abstraction**: `EdgarPath` dispatches all I/O operations to either `pathlib.Path` (local) or `fsspec` (cloud) based on `is_cloud_storage_enabled()` — callers use identical API.

---

### Cross-domain interactions

**Imports FROM other edgar.* modules:**
- `edgar.core`: `get_edgar_data_directory`, `get_identity`, `strtobool`, `text_extensions`, `log`
- `edgar.config`: `SEC_BASE_URL`, `SEC_ARCHIVE_URL`
- `edgar.urls`: `build_feed_url`, `build_ticker_url`, `build_company_tickers_url`, etc.
- `edgar.dates`: `extract_dates`
- `edgar.sgml.sgml_parser`: `SGMLDocument` (base class for `TarSGMLDocument`)
- `edgar.sgml.sgml_header`: `FilingHeader`, `FilingInformation`, `CompanyInformation`, `Filer`
- `edgar.sgml.sgml_common`: `FilingSGML`
- `edgar._party`: `Address`

**Consumed BY other edgar.* modules:**
- `edgar/_filings.py` — uses `download_file`, `get_with_retry`, `local_filing_path`, `is_using_local_storage`
- `edgar/entity/core.py` — uses `get_with_retry` for submissions
- `edgar/xbrl/xbrl.py` — uses `download_file`, `download_json`
- `edgar/sgml/sgml_common.py` — uses `is_using_local_storage`, `get_datamule_filing`, `local_filing_path`, `http_client`
- `edgar/reference/` — uses `download_datafile`
- All modules importing `from edgar import configure_http, get_http_config` directly

---

### Gotchas & notable behaviors

1. **Cache-forever trap**: `/Archives/edgar/data` responses are cached forever (`True` in cache rules). A transient SEC 500/empty response gets permanently cached. `FilingSGML.from_source()` mitigates with a cache-bypass retry on empty/error responses. `clear_empty_cached_responses()` performs a one-time full cache wipe on upgrade (Issue #672).

2. **configure_http must be called before first request**: The `HTTP_MGR` client is lazily created on first `http_client()` call. If `configure_http(verify_ssl=False)` is called AFTER the first request, the existing client still uses old SSL settings. `configure_http()` detects this (`HTTP_MGR._client is not None`) and forces `_client.close(); _client = None` to trigger recreation — but this only works if called after the first-use, not before. In Jupyter notebooks, restart and call `configure_http()` before any `from edgar import ...` that triggers a request.

3. **Locale bug for non-English systems**: httpxthrottlecache uses `time.strptime()` for HTTP date headers, which is locale-dependent. `LC_TIME` is forced to `'C'` at module import. Cache files created before v4.19.0 with non-English locales have corrupted timestamps — `clear_locale_corrupted_cache()` runs once via marker file.

4. **pyrate-limiter version compatibility**: `_create_rate_limiter()` handles both pyrate-limiter 3.x (accepts `max_delay`, `raise_when_fail`, `retry_until_max_delay`) and 4.x (removed those params) via `try/except TypeError` — `httpclient.py:151`.

5. **rate limit is 9/sec, SEC allows 10/sec**: Default is deliberately 1 under the SEC limit. Users can increase via `EDGAR_RATE_LIMIT_PER_SEC` env var (e.g., for custom mirrors). In tests, mock-backed tests should zero the rate limit since the limiter fires against mock interceptors.

6. **HTTP 429 is NOT retried**: `TooManyRequestsError` is not in `RETRYABLE_EXCEPTIONS`. The SEC penalizes continued requests during the block window (~10 minutes). The error message explicitly warns against retrying.

7. **Datamule tar must be pre-scanned**: `use_datamule_storage(path)` is synchronous and scans all `.tar` files eagerly at call time. Large directories with many tars will take time. Missing or corrupt tars are logged as warnings and skipped.

8. **Datamule zstd decompression**: Files inside datamule tars may be zstd-compressed. The `_ZSTD_MAGIC` constant (`\x28\xb5\x2f\xfd`) is checked at byte 0-3; if matched, `zstandard` package is required. If not installed, content is returned compressed (will likely fail downstream parsing).

9. **Datamule metadata key format varies**: Three formats supported via `_nested_get()` fallback: kebab-case nested (`filer.company-data.cik`), snake_case flat (`cik`), camelCase flat (`cik`). Accession numbers accepted with or without dashes, 18-digit undashed normalized automatically.

10. **Cloud storage sets EDGAR_USE_LOCAL_DATA=1**: `use_cloud_storage()` side-effects `os.environ['EDGAR_USE_LOCAL_DATA'] = '1'` at `filesystem.py:155`. This ensures the rest of the library uses the configured storage path.

11. **EdgarPath.as_local_path() raises if cloud enabled**: Callers must use `read_text()`/`read_bytes()`/`open()` for cloud-compatible code — `filesystem.py:748`.

12. **sync_to_cloud skips files by directory listing**: Instead of N `fs.exists()` calls, `sync_to_cloud` calls `fs.ls()` per parent directory and builds a set of existing cloud paths. Much more efficient for cloud APIs with per-request billing. Falls back to individual checks on `ls()` failure.

13. **SGML vs datamule content**: Standard `SGMLDocument.content` extracts text between `<TEXT>`, `<HTML>`, or `<XML>` SGML tags. `TarSGMLDocument.content` returns `raw_content` directly since datamule files are already raw — the override is a one-line property that skips all SGML tag logic.

14. **`stream_with_retry` yields the response, not bytes**: Despite the name, `stream_with_retry` yields the `httpx.Response` object for streaming. Callers iterate `response.iter_lines()` (used in `download_text_between_tags`).

16. **Default HTTP timeout is set on `HTTP_MGR` at init, not per-request**: `get_http_mgr()` calls `get_edgar_http_timeout()` (default `30.0s` from `EDGAR_HTTP_TIMEOUT` env var) and sets `http_mgr.httpx_params["timeout"] = httpx.Timeout(timeout, connect=10.0)`. This applies a `30s` read timeout + `10s` connect timeout to all requests. Stalled SEC connections that previously blocked indefinitely now time out. Override via `EDGAR_HTTP_TIMEOUT` env var or `configure_http(timeout=...)` at runtime. `EDGAR_HTTP_TIMEOUT=0` or `=none` disables the timeout entirely.

15. **Chunk size adapts to file size in stream_file**: 2MB chunks for <100MB, 4MB for <500MB, 8MB for >500MB. Progress bar update frequency also adapts (0.1MB threshold vs 1.0MB threshold for very large files) — `httprequests.py:1106`.
