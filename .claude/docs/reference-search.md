## Reference Data & Search

### Overview

The Reference Data & Search domain provides SEC identifier resolution (ticker↔CIK↔CUSIP), static company datasets with industry/state/exchange filtering, form-type description lookup, place/country code utilities, and two distinct search subsystems: EDGAR Full-Text Search (EFTS) for searching inside filing bodies across the entire SEC corpus, and local in-memory search utilities (BM25, fuzzy, regex, grep) for searching within already-retrieved filing content. Together these components underpin Company resolution, filing discovery, and AI-optimized content retrieval throughout EdgarTools.

---

### Public API surface

| Symbol | file:line | Purpose |
|---|---|---|
| `get_company_tickers(as_dataframe, clean_name, clean_suffix)` | `edgar/reference/tickers.py:104` | Master ticker/CIK/company/exchange DataFrame, 3-source priority load |
| `find_cik(ticker)` | `edgar/reference/tickers.py:498` | Resolve ticker → CIK (company then mutual fund fallback) |
| `find_ticker(cik)` | `edgar/reference/tickers.py:317` | Resolve CIK → primary ticker (lru_cache 128) |
| `find_ticker_safe(cik)` | `edgar/reference/tickers.py:336` | CIK → ticker without triggering network calls; returns None if not cached |
| `get_cik_ticker_lookup()` | `edgar/reference/tickers.py:294` | CIK→ticker dict, prefers non-hyphenated / shortest ticker |
| `get_company_cik_lookup()` | `edgar/reference/tickers.py:269` | ticker→CIK dict, includes base ticker (pre-hyphen) aliases |
| `get_cik_tickers()` | `edgar/reference/tickers.py:252` | ticker+cik DataFrame (no name cleaning) |
| `list_all_tickers()` | `edgar/reference/tickers.py:263` | All ticker strings as a list |
| `get_company_ticker_name_exchange()` | `edgar/reference/tickers.py:372` | Live SEC API DataFrame: cik, name, ticker, exchange |
| `get_companies_by_exchange(exchange)` | `edgar/reference/tickers.py:381` | Filter by exchange string or list |
| `get_mutual_fund_tickers()` | `edgar/reference/tickers.py:395` | cik/seriesId/classId/ticker from SEC mutual fund API |
| `find_mutual_fund_cik(ticker)` | `edgar/reference/tickers.py:411` | Mutual fund ticker → CIK |
| `cusip_ticker_mapping(allow_duplicate_cusips)` | `edgar/reference/tickers.py:28` | CUSIP→Ticker DataFrame indexed on Cusip (from bundled ct.pq) |
| `get_ticker_from_cusip(cusip)` | `edgar/reference/tickers.py:514` | O(1) CUSIP→ticker dict lookup |
| `popular_us_stocks()` | `edgar/reference/tickers.py:578` | Bundled CSV of popular US stocks with CIK index |
| `get_icon_from_ticker(ticker)` | `edgar/reference/tickers.py:550` | Download PNG icon bytes from nvstly/icons (lru_cache 4) |
| `Exchange` (enum) | `edgar/reference/tickers.py:584` | Nasdaq / NYSE / OTC / CBOE |
| `describe_form(form, prepend_form)` | `edgar/reference/forms.py:9` | Human-readable description of a SEC form code |
| `PROSPECTUSES` (constant) | `edgar/reference/forms.py:30` | List of prospectus/registration form codes |
| `get_company_dataset(rebuild)` | `edgar/reference/company_dataset.py:522` | PyArrow Table of ~562K companies built from local submissions JSON |
| `build_company_dataset_parquet(submissions_dir, output_path, ...)` | `edgar/reference/company_dataset.py:123` | Build/save Parquet dataset from raw submissions directory |
| `build_company_dataset_duckdb(submissions_dir, output_path, ...)` | `edgar/reference/company_dataset.py:252` | Build DuckDB database from raw submissions directory |
| `to_duckdb(parquet_path, duckdb_path, ...)` | `edgar/reference/company_dataset.py:439` | Convert existing Parquet to DuckDB |
| `is_individual_from_json(data)` | `edgar/reference/company_dataset.py:70` | Classify SEC submission dict as individual vs company (9-signal chain) |
| `CompanySubset` | `edgar/reference/company_subsets.py:82` | Fluent builder for company subsets — chain `.from_exchange()`, `.from_industry()`, `.from_state()`, `.sample()`, `.get()` |
| `get_all_companies(use_comprehensive)` | `edgar/reference/company_subsets.py:307` | Standard (~13K tickers) or comprehensive (~562K, SIC/state metadata) DataFrame |
| `get_companies_by_exchanges(exchanges)` | `edgar/reference/company_subsets.py:352` | Filter by exchange name(s) |
| `get_popular_companies(tier)` | `edgar/reference/company_subsets.py:378` | Popular US stocks optionally filtered by PopularityTier |
| `get_companies_by_industry(sic, sic_range, sic_description_contains)` | `edgar/reference/company_subsets.py:736` | SIC-based industry filter (forces comprehensive mode) |
| `get_companies_by_state(states)` | `edgar/reference/company_subsets.py:817` | State-of-incorporation filter (forces comprehensive mode) |
| `get_random_sample / get_stratified_sample` | `edgar/reference/company_subsets.py:427,463` | Sampling utilities (random / exchange-proportional) |
| `filter_companies / exclude_companies` | `edgar/reference/company_subsets.py:571,621` | Ticker/name/CIK/custom include and exclude filters |
| `combine_company_sets / intersect_company_sets` | `edgar/reference/company_subsets.py:666,698` | Set union / intersection on company DataFrames |
| Industry convenience functions | `edgar/reference/company_subsets.py:903-991` | `get_pharmaceutical_companies`, `get_biotechnology_companies`, `get_software_companies`, `get_semiconductor_companies`, `get_banking_companies`, `get_investment_companies`, `get_insurance_companies`, `get_real_estate_companies`, `get_oil_gas_companies`, `get_retail_companies` |
| General convenience functions | `edgar/reference/company_subsets.py:874-899` | `get_faang_companies`, `get_tech_giants`, `get_dow_jones_sample` |
| `MarketCapTier` (enum) | `edgar/reference/company_subsets.py:66` | LARGE_CAP / MID_CAP / SMALL_CAP / MICRO_CAP |
| `PopularityTier` (enum) | `edgar/reference/company_subsets.py:74` | MEGA_CAP (top 10) / POPULAR (top 50) / MAINSTREAM (top 100) / EMERGING (all) |
| `get_place_name(code)` | `edgar/reference/_codes.py:15` | SEC place code → full name string |
| `get_place_type(code)` | `edgar/reference/_codes.py:32` | Code → 'US' / 'CANADIAN' / 'FOREIGN' / 'UNKNOWN' |
| `get_filer_type(state_code)` | `edgar/reference/_codes.py:46` | Code → 'Domestic' / 'Canadian' / 'Foreign' / None |
| `is_us_company / is_foreign_company / is_canadian_company` | `edgar/reference/_codes.py:69,83,97` | Boolean jurisdiction tests |
| `search_filings(query, *, forms, items, cik, ticker, start_date, end_date, limit)` | `edgar/search/efts.py:459` | Full-text search over SEC filing bodies via EFTS; returns `EFTSSearch` |
| `EFTSSearch` | `edgar/search/efts.py:127` | Result container with pagination, filtering, sorting, AI context |
| `EFTSResult` | `edgar/search/efts.py:32` | Single EFTS hit with score, form, company, filed, CIK, period, SIC, items |
| `EFTSAggregations` / `Aggregation` | `edgar/search/efts.py:78,68` | Faceted counts (entities, forms, SICs, states) from EFTS |
| `FastSearch` | `edgar/search/datasearch.py:11` | PyArrow-backed fuzzy company/ticker search with inverted index |
| `create_search_index / search / cached_search` | `edgar/search/datasearch.py:89-100` | Factory and query functions for FastSearch |
| `BM25Search` | `edgar/search/textsearch.py:201` | BM25Okapi full-text search over in-memory document lists |
| `RegexSearch` | `edgar/search/textsearch.py:243` | Regex/case-insensitive search over in-memory document lists |
| `SimilaritySearchIndex` | `edgar/search/textsearch.py:24` | Jaro-distance fuzzy search on a DataFrame column |
| `SearchResults` | `edgar/search/textsearch.py:149` | Rich-renderable result container for BM25/Regex searches |
| `GrepResult` / `GrepMatch` | `edgar/search/grep.py:39,21` | Exact-match content grep with location and context window |
| `get_ticker_to_cik_lookup()` | `edgar/entity/tickers.py:16` | ticker→CIK dict (re-exports, wraps `get_company_tickers`) |
| `get_cik_lookup_data()` | `edgar/entity/tickers.py:38` | Full name/CIK DataFrame from `cik-lookup-data.txt` (SEC live fetch) |

---

### Key classes

#### `Exchange` (Enum) — `edgar/reference/tickers.py:584`
Four-value enum for SEC exchange strings. `.value` is the display string.
- `Nasdaq`, `NYSE`, `OTC`, `CBOE`
- `__str__()` returns `.value` directly.

#### `MarketCapTier` / `PopularityTier` (Enums) — `edgar/reference/company_subsets.py:66,74`
Tier markers used as arguments to `get_popular_companies()` and `CompanySubset.from_popular()`. Not tied to live market-cap data — PopularityTier is purely positional in the `popular_us_stocks.csv` list.

#### `CompanySubset` — `edgar/reference/company_subsets.py:82`
Fluent builder pattern. Internally holds a mutable `_companies` DataFrame and replaces it on each chaining call.

- `__init__(companies=None, use_comprehensive=False)` — `edgar/reference/company_subsets.py:101`: seeds from `get_all_companies()` if no DataFrame provided
- `from_exchange(exchanges)` → `self` — `edgar/reference/company_subsets.py:116`: delegates to `get_companies_by_exchanges()`
- `from_popular(tier=None)` → `self` — `edgar/reference/company_subsets.py:121`: delegates to `get_popular_companies()`
- `from_industry(sic, sic_range, sic_description_contains)` → `self` — `edgar/reference/company_subsets.py:126`: forces comprehensive mode, delegates to `get_companies_by_industry()`
- `from_state(states)` → `self` — `edgar/reference/company_subsets.py:160`: forces comprehensive mode, delegates to `get_companies_by_state()`
- `filter_by(condition)` → `self` — `edgar/reference/company_subsets.py:183`: arbitrary callable `(DataFrame) -> DataFrame`
- `exclude_tickers(tickers)` / `include_tickers(tickers)` → `self` — `edgar/reference/company_subsets.py:188,193`
- `sample(n, random_state=None)` → `self` — `edgar/reference/company_subsets.py:198`
- `top(n, by='name')` → `self` — `edgar/reference/company_subsets.py:203`
- `combine_with(other)` / `intersect_with(other)` → `self` — `edgar/reference/company_subsets.py:208,213`: set union/intersection
- `get()` → `pd.DataFrame` — `edgar/reference/company_subsets.py:218`: returns a copy of current DataFrame
- `__len__()` / `__repr__()` — shows count + up to 3 sample tickers

#### `EFTSResult` (dataclass) — `edgar/search/efts.py:32`
Immutable value object for one EFTS hit.
- Fields: `accession_number`, `form`, `filed`, `company`, `cik`, `period`, `score`, `file_type`, `file_description`, `document_id`, `items` (List[str]), `sic`, `location`, `state`, `inc_state`
- `get_filing()` → `Filing` — `edgar/search/efts.py:63`: loads full Filing via `get_by_accession_number()`

#### `EFTSSearch` (dataclass) — `edgar/search/efts.py:127`
Main result container for EFTS searches. Iterable, sliceable. Not a `Filings` object — it's a separate dataclass wrapping `List[EFTSResult]`.
- `__init__`: `query`, `total`, `results`, `aggregations`, `_params` (private for pagination), `_offset` (private)
- `filter(*, form, sic, items, file_type, min_score, start_date, end_date, state)` → `EFTSSearch` — `edgar/search/efts.py:161`: client-side filter, returns new instance
- `head(n)` / `tail(n)` / `sample(n)` → `EFTSSearch` — `edgar/search/efts.py:218-229`
- `sort_by(field='score', reverse=True)` → `EFTSSearch` — `edgar/search/efts.py:232`: sort fields: `score`, `filed`, `company`, `sic`
- `next()` → `Optional[EFTSSearch]` — `edgar/search/efts.py:250`: fetches next page; returns None when exhausted
- `fetch_more(n=100)` → `EFTSSearch` — `edgar/search/efts.py:269`: fetches up to n more results (capped at 5,000), appends to current results; 100ms sleep between requests
- `to_context(detail='standard')` → `str` — `edgar/search/efts.py:334`: AI-optimized string; detail levels: `'minimal'`, `'standard'`, `'full'` (includes aggregations)
- `empty` property → `bool` — `edgar/search/efts.py:247`
- `__rich__()` / `__repr_html__()`: Rich panel table + Jupyter HTML

#### `EFTSAggregations` (dataclass) — `edgar/search/efts.py:78`
Faceted count buckets from EFTS. Fields: `entities`, `sics`, `states`, `forms` (each `List[Aggregation]`).
- `__rich__()`: four side-by-side Rich tables capped at 5 buckets each

#### `Aggregation` (dataclass) — `edgar/search/efts.py:68`
Simple `key: str, count: int` value object.

#### `FastSearch` — `edgar/search/datasearch.py:11`
PyArrow-backed inverted word index for fuzzy company/ticker lookup. Not used directly for SEC-wide search — used internally for Company resolution from name/ticker.
- `__init__(data, columns, preprocess_func=None, score_func=None)`: builds per-column word→row inverted index
- `search(query, top_n=10, threshold=60)` → `List[Dict]` — `edgar/search/datasearch.py:44`: candidate lookup then `fuzz.ratio` scoring; tickers ≤5 chars get prefix match, not ratio
- Hash-based `__hash__` / `__eq__` enables `lru_cache` keying on `FastSearch` instances

#### `BM25Search` — `edgar/search/textsearch.py:201`
BM25Okapi ranking for searching within in-memory document collections (e.g. filing sections).
- `__init__(document_objs, text_fn=None)`: preprocesses corpus (lowercase → item tokenization → stop word removal → numeric normalization)
- `search(query, tables=True)` → `SearchResults` — `edgar/search/textsearch.py:228`: returns only docs with score > 0, sorted by relevance

#### `RegexSearch` — `edgar/search/textsearch.py:243`
Case-insensitive regex search over a document list. Simpler than BM25 — matches `re.search()`.
- `search(query, tables=True)` → `SearchResults` — `edgar/search/textsearch.py:257`

#### `SimilaritySearchIndex` — `edgar/search/textsearch.py:24`
Jaro-distance similarity search over a DataFrame column.
- `similar(query, threshold=0.6, topn=20)` → `DataFrame` — `edgar/search/textsearch.py:35`: requires `textdistance` package; adds `match` score column and `matches_start` sort key

#### `SearchResults` — `edgar/search/textsearch.py:149`
Container for BM25/Regex results. Holds `List[DocSection]`, Rich-renderable.
- `empty` property, `__len__`, `__getitem__`, `json()`
- Renders as Rich panels, sorted by score descending; Markdown sections or table (if doc starts with `|  |`)
- Panel title is the **source corpus index** (`DocSection.loc`) — the section's position in the original document, not the display rank. BM25 re-orders by score; `loc` lets callers correlate back to the original sections list.
- Matched query terms are highlighted `bold red` in rendered output. BM25 mode highlights each non-stopword query word as a case-insensitive substring. Regex mode highlights the pattern matches themselves. See `SearchResults.HIGHLIGHT_STYLE` and `_build_highlight_pattern()` in `edgar/search/textsearch.py`.

#### `GrepResult` / `GrepMatch` — `edgar/search/grep.py:39,21`
`GrepMatch`: `location` (document section name), `match` (matched text), `context` (±100 chars surrounding text).
`GrepResult`: list-like, Rich table (capped at 20 display), `to_context(detail)` for AI use.
- `_grep_text(text, pattern, location, regex=False, context_chars=100)` → `List[GrepMatch]` — `edgar/search/grep.py:107`: always case-insensitive; supports regex mode; returns all occurrences with context

---

### Class hierarchy

```
# Reference data — no significant inheritance, mostly standalone functions + enums

Enum
├── Exchange                         (tickers.py:584)
├── MarketCapTier                    (company_subsets.py:66)
└── PopularityTier                   (company_subsets.py:74)

CompanySubset                        (company_subsets.py:82)   [no base class]

dataclass
├── EFTSResult                       (efts.py:32)
├── Aggregation                      (efts.py:68)
├── EFTSAggregations                 (efts.py:78)
├── EFTSSearch                       (efts.py:127)
├── GrepMatch                        (grep.py:21)
└── DocSection                       (textsearch.py:120)

# GrepResult and SearchResults are plain classes (not dataclasses)
GrepResult                           (grep.py:39)
SearchResults                        (textsearch.py:149)
FastSearch                           (datasearch.py:11)
BM25Search                           (textsearch.py:201)
RegexSearch                          (textsearch.py:243)
SimilaritySearchIndex                (textsearch.py:24)
```

---

### Configuration & options

| Option | Type | Default | Effect |
|---|---|---|---|
| `get_company_tickers(as_dataframe)` | `bool` | `True` | Return pandas DataFrame vs pyarrow Table |
| `get_company_tickers(clean_name)` | `bool` | `True` | Strip `/XX/` country suffixes from company names |
| `get_company_tickers(clean_suffix)` | `bool` | `False` | Remove Inc/Corp/Ltd/PLC/LP suffixes |
| `cusip_ticker_mapping(allow_duplicate_cusips)` | `bool` | `True` | If False, deduplicate by keeping first CUSIP occurrence |
| `get_all_companies(use_comprehensive)` | `bool` | `False` | False=~13K tickers only; True=~562K companies with SIC/state/EIN metadata |
| `get_company_dataset(rebuild)` | `bool` | `False` | Force rebuild of companies.pq from raw submissions even if cache exists |
| `build_company_dataset_parquet(filter_individuals)` | `bool` | `True` | Skip individual filers during build |
| `build_company_dataset_parquet(show_progress)` | `bool` | `True` | tqdm progress bar during build |
| `build_company_dataset_duckdb(create_indexes)` | `bool` | `True` | Create indexes on cik, sic, name in DuckDB |
| `describe_form(prepend_form)` | `bool` | `True` | Include "Form XX:" prefix in description string |
| `search_filings(limit)` | `int` | `20` | Max results per page (clamped 1–100) |
| `get_random_sample(random_state)` | `Optional[int]` | `None` | Seed for reproducibility |
| `get_stratified_sample(stratify_by)` | `str` | `'exchange'` | Column to stratify proportional sampling by |
| `EFTSSearch.filter(min_score)` | `Optional[float]` | `None` | Minimum relevance score for client-side filter |
| `_grep_text(context_chars)` | `int` | `100` | Characters of context before/after each match |
| `FastSearch.search(threshold)` | `float` | `60` | Min `fuzz.ratio` score to include in results |
| `EDGAR_USE_LOCAL_DATA` env var | str | unset | When set, attempts to load tickers from local `~/.edgar/reference/` before SEC API |

---

### Data flow / lifecycle

**Ticker/CIK resolution chain:**

- `_get_company_tickers_raw()` (lru_cache maxsize=1) is the canonical internal source. On first call it attempts: (1) `load_company_tickers_from_package()` reads `edgar/reference/data/company_tickers.parquet` via `importlib.resources` — this is bundled with the package, always offline; (2) if `EDGAR_USE_LOCAL_DATA` env var is set, reads from `~/.edgar/reference/company_tickers.json`; (3) falls back to live SEC API at `https://data.sec.gov/submissions/company_tickers.json`.
- `get_company_tickers()` calls `_get_company_tickers_raw()`, optionally copies and applies name cleaning, then optionally converts to pyarrow Table.
- `get_cik_tickers()` (lru_cache) → calls `get_company_tickers(clean_name=False)`, returns `[ticker, cik]` slice.
- `get_company_cik_lookup()` (lru_cache) → builds `dict[ticker → cik]` plus base-ticker aliases (pre-hyphen part).
- `get_cik_ticker_lookup()` (lru_cache) → builds `dict[cik → primary_ticker]` with preference rules: non-hyphenated over hyphenated, shorter over longer; then applies `_PREFERRED_TICKER` manual overrides for 3 known-bad CIKs.
- `find_cik(ticker)` → `find_company_cik(ticker)` → checks `get_company_cik_lookup()` first; on miss, calls `_get_live_company_cik_lookup()` (lru_cache, live SEC fetch) as fallback; then falls through to `find_mutual_fund_cik()`.
- `get_cik_lookup_data()` (entity/tickers.py, lru_cache) → downloads `https://www.sec.gov/Archives/edgar/cik-lookup-data.txt` — a complete name:CIK list parsed line-by-line; this is a separate, larger dataset than the ticker parquet.

**CUSIP resolution:**

- `cusip_ticker_mapping()` reads bundled `edgar/reference/data/ct.pq` (lru_cache maxsize=1); `_cusip_ticker_dict()` (lru_cache) deduplicates by keeping first CUSIP row for O(1) `get_ticker_from_cusip()` lookups.

**Company Dataset lifecycle:**

- `get_company_dataset()` checks in-memory `_CACHE['companies']` dict first, then disk at `~/.edgar/companies.pq`. If neither exists, calls `build_company_dataset_parquet()` which iterates all `~CIK*.json` files under `~/.edgar/submissions/`, calls `is_individual_from_json()` for each (delegating to `edgar.entity.constants._classify_is_individual` with a 9-signal priority chain), serializes matching companies using `COMPANY_SCHEMA`, and writes zstd-compressed Parquet. The `tickers` and `exchanges` fields are stored pipe-delimited (`|`) in the Parquet — `company_subsets._get_comprehensive_companies()` splits these back to extract primary ticker/exchange.
- Build time: ~30s for ~562K companies with orjson (fallback to stdlib json if orjson unavailable). Subsequent loads: <100ms.

**Form reference:**

- `sec_form_data` is loaded at module import time (module-level) from bundled `secforms.csv`. `describe_form()` is lru_cache(maxsize=64) — amendment suffix `/A` is stripped before lookup, re-appended as " Amendment" in output. Unknown forms fall back to `"Form {form}"`.

**EFTS full-text search lifecycle:**

- `search_filings()` validates args (must have query or items), builds a `params` dict: `q`, optionally `forms` (comma-separated), `items` (comma-separated), `dateRange`/`startdt`/`enddt`, `ciks` (zero-padded 10-digit). Ticker is resolved to CIK via `Company(ticker).cik` before being added to params.
- `_fetch_page(params, offset, limit)` makes a GET to `https://efts.sec.gov/LATEST/search-index` with `get_with_retry`; parses response with `orjson`. Each hit is parsed via `_parse_hit()` which extracts from `_source`; document_id comes from `_id` field as `"accession:document_filename"`.
- `EFTSSearch._params` stores the original params; `_offset` tracks current position. `next()` computes `next_offset = _offset + len(results)` and calls `_fetch_page` again. `fetch_more(n)` loops, sleeping 100ms between requests, capped at 5,000 additional results (EFTS hard pagination cap ~10,000).
- EFTS results are NOT `Filings` objects — they are `EFTSSearch` containing `List[EFTSResult]`. To load a full `Filing`, call `result.get_filing()` which calls `get_by_accession_number()`.

**Local text search lifecycle:**

- `BM25Search.__init__()` preprocesses all documents immediately (pipeline: lowercase → item-token conversion → tokenize → punctuation filter → stopword filter → numeric normalization → item-token revert). BM25Okapi corpus is built once; no lazy loading.
- `FastSearch` builds inverted word index at init time per column. Querying candidates by word overlap then scores with `fuzz.ratio` (via rapidfuzz). Short queries (≤5 chars) trigger prefix matching against the full index word set for ticker-style lookups.
- `_grep_text()` is a pure function operating on a string — the filing or document object is responsible for calling it with the right text and location label; no lazy loading.

---

### Design patterns

- **Three-source priority with fallback**: `_get_company_tickers_raw()` follows bundled-parquet → local-file → live-API priority. This makes the common case (bundled data) instant and offline, while supporting enterprise scenarios (local mirror) and catching recent IPOs (live fallback in `find_company_cik()`).
- **`lru_cache` as session-level singleton**: Used throughout `tickers.py` and `company_subsets.py` (`maxsize=1` or `maxsize=2`) to make the first call pay the load cost and all subsequent calls free within a Python session.
- **Fluent builder (CompanySubset)**: Mutates an internal DataFrame through chained method calls. Each method replaces `_companies` in-place. `get()` returns a copy, preserving the builder state for potential further use.
- **Dataclass result containers (EFTS)**: `EFTSResult`, `EFTSSearch`, `EFTSAggregations`, `Aggregation` are all `@dataclass` instances. `EFTSSearch` is effectively immutable — all filtering/sorting/pagination methods create new instances via `_with_results()`.
- **`_with_results()` copy constructor**: `EFTSSearch._with_results(results)` creates a new `EFTSSearch` sharing `query`, `total`, `aggregations`, `_params`, `_offset` but with a different results list. This keeps pagination state intact through client-side filter/sort operations.
- **Module-level preloaded CSV**: `sec_form_data` in `forms.py` loads at import time; `describe_form()` then only needs the lru_cache for string construction. This is very fast but means any update to `secforms.csv` requires a package reinstall.
- **BM25 preprocessing pipeline**: The shared `preprocess()` function in `textsearch.py` includes special handling for SEC "Item N.N" patterns — converting `Item 4.` to `item_4` before tokenization to prevent splitting, then reversing after stopword removal, so item-numbers survive as intact search tokens.
- **orjson for EFTS response parsing**: `_fetch_page()` in `efts.py` uses `orjson.loads()` directly on response bytes, avoiding UTF-8 decode roundtrips.

---

### Cross-domain interactions

**Imports consumed by this domain:**

- `edgar/reference/tickers.py` imports from `edgar.core` (data directory, listify, log), `edgar.httprequests` (download_file, download_json), `edgar.reference.data.common` (read_csv_from_package, read_parquet_from_package), `edgar.urls` (URL builders).
- `edgar/reference/company_dataset.py` imports from `edgar.core` (get_edgar_data_directory, log), `edgar.entity.constants._classify_is_individual`.
- `edgar/reference/company_subsets.py` imports `get_company_ticker_name_exchange` and `popular_us_stocks` from `edgar.reference.tickers`.
- `edgar/reference/_codes.py` imports from `edgar.reference.data.common`.
- `edgar/search/efts.py` imports `get_with_retry` from `edgar.httprequests`, `orjson` (direct), `edgar.Company` for ticker-to-CIK resolution, `get_by_accession_number` from `edgar`.
- `edgar/search/datasearch.py` uses `rapidfuzz.fuzz`, `unidecode`, `pyarrow`.
- `edgar/search/textsearch.py` uses `rank_bm25.BM25Okapi`, `textdistance` (lazy import in SimilaritySearchIndex.similar).
- `edgar/entity/tickers.py` re-exports from `edgar.reference.tickers`.

**Consumers of this domain:**

- `edgar/__init__.py` re-exports `get_company_tickers` (via entity), `EFTSResult`, `EFTSSearch`, `search_filings` directly at top level.
- `edgar/entity/core.py` uses `find_cik`, `find_ticker`, `get_cik_tickers`, `get_company_tickers` for Company/Entity resolution by ticker or CIK.
- 13F parsers use `cusip_ticker_mapping()` for vectorized CUSIP→ticker DataFrame mapping.
- `edgar/reference/__init__.py` re-exports the complete public surface of all reference submodules plus a `states` dict.
- `edgar/search/__init__.py` re-exports all four search module surfaces.
- CLAUDE.md for `edgar/entity/` explicitly calls out `tickers.py` and `get_cik_lookup_data()` as the entity resolution points.

---

### Gotchas & notable behaviors

**Ticker/CIK resolution:**

- The bundled `company_tickers.parquet` has an `exchange` column; JSON sources (live SEC API, local file) do NOT include exchange — the exchange column will be absent or all-None when loading from those sources. `get_company_tickers()` documents this in comments but does not raise.
- SEC's `ticker.txt` endpoint has been deprecated (returns 503 "apology page" since Dec 2024). `get_cik_tickers_from_ticker_txt()` is kept for backward compat but always returns `None` unless `EDGAR_USE_LOCAL_DATA` is set and the local file already exists.
- `get_company_cik_lookup()` adds base-ticker aliases: `BRK-A` → also registers `BRK`. This means searching `BRK` may resolve to Berkshire via the base-ticker path.
- `get_cik_ticker_lookup()` applies `_PREFERRED_TICKER` manual overrides for 3 specific CIKs (Comcast 1166691→CMCSA, Aluminum Corp 1161611→ALMMF, T3 Defense 1787518→DFNSW) where the algorithm would pick the wrong ticker.
- `find_ticker_safe()` checks all three lru_cache `.cache_info().currsize` values before proceeding. If any cache is cold (e.g. first call in a new process), it returns `None` rather than triggering a network call. Designed for display methods that must not block.
- Mutual fund tickers share CIK namespace with company tickers but are stored in a separate SEC endpoint (`company_tickers_mf.json`). `find_cik()` checks companies first, mutual funds second.

**Company Dataset:**

- `get_company_dataset()` requires that `~/.edgar/submissions/` exists with at least 100,000 `CIK*.json` files (the full SEC bulk submissions download ~500MB compressed). If the directory exists but is incomplete (fewer files), it raises `FileNotFoundError` with instructions.
- `COMPANY_SCHEMA` stores `tickers` and `exchanges` as pipe-delimited strings (not arrays). PyArrow arrays do not have a native list-of-strings column type in this schema. Downstream consumers must split on `|`.
- The `cik` field in `COMPANY_SCHEMA` is `pa.string()` to preserve leading zeros. This is different from `get_company_tickers()` which returns `cik` as `int64`.
- `_get_comprehensive_companies()` (called by `get_all_companies(use_comprehensive=True)`) calls `get_company_dataset()` which can take ~30s on first call. This is silently invoked whenever any `from_industry()`, `from_state()`, or `use_comprehensive=True` path is used.
- The `_CACHE` module-level dict in `company_dataset.py` is a plain dict (not lru_cache) — it persists for the lifetime of the module import. It is distinct from the lru_cache mechanisms in `tickers.py`.

**EFTS full-text search:**

- `search_filings()` raises `ValueError` if both `query` and `items` are empty/None. An empty string `query=""` is valid when `items` is provided (e.g., structured 8-K item lookup).
- `limit` is clamped to 1–100. EFTS itself has a maximum page size of 100. Deep pagination is capped at ~10,000 results by the EFTS server; `fetch_more()` enforces a client-side 5,000 additional results cap.
- The `forms` parameter is sent to EFTS as a comma-separated string: `"10-K,10-Q"`. Amendment forms (`10-K/A`) must be listed separately if desired.
- `items` is an 8-K-specific EFTS server-side filter (e.g. `"1.05"` for cybersecurity incidents). Sending `items` without `forms="8-K"` will return 8-K results only since items are only indexed on 8-K filings.
- Scores in `EFTSResult.score` come from Elasticsearch's `_score` field; they are floating-point relevance scores, not normalized to any fixed range.
- `EFTSResult.cik` is a string (zero-padded is NOT guaranteed — it is whatever EFTS returns from `ciks[0]`). The accession number is formatted from 18-char `adsh` to standard `XXXXXXXXXX-YY-ZZZZZZ` format in `_format_accession()`.
- EFTS searches filing bodies and exhibit content — NOT filing metadata. `get_filings()` searches metadata (form type, date, CIK). These are fundamentally different: EFTS can find a 10-K that mentions "tariff" in its risk factors; `get_filings()` cannot.
- There is no EFTS rate-limit handling beyond `get_with_retry()`. The `fetch_more()` loop inserts 100ms sleeps between pages to be polite.

**Local search utilities:**

- `BM25Search` and `RegexSearch` operate on already-downloaded text — they do not make network calls. They are used inside filing/document objects to search section text.
- `SimilaritySearchIndex.similar()` has a lazy `import textdistance` — raises ImportError at call time, not at construction time, if `textdistance` is not installed.
- `Filing.search()` and `Filing.grep()` now support plain-text (non-HTML) filings. `search()` splits the full filing text on `<PAGE>` markers and double-newlines as section boundaries; `grep()` falls back to `_grep_filing_text()` when no attachment yields usable text. See `core-filing-access.md` for details on the fallback path.
- `_codes.py` contains `ISO_STATES_AND_OUTLYING_AREAS` and `ISO_COUNTRY_CODES` dicts that are defined but truncated/incomplete in the source (the dict literals are cut off). The functional place-code lookup uses `place_codes.csv` via `_load_place_codes()`, not these dicts.
- `describe_form()` handles `/A` amendments by stripping suffix before lookup and appending " Amendment" to the result. Any other amendment suffixes (e.g. `/T`, `/W`) are not specially handled.
- `edgar/reference/financials.py` is minimal — only contains a URL constant and a `__main__` block for downloading DERA financial statement ZIP files. It exports nothing for normal use.
