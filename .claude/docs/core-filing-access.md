## Core & Filing Access

### Overview

This domain is the entry point of EdgarTools. It provides the `Filing` and `Filings` classes that represent individual SEC filings and collections thereof, the two primary retrieval functions (`get_filings` for historical quarterly-index data and `get_current_filings` for real-time data), the `find()` uber-search dispatcher, and the `obj()` form-to-typed-object dispatch table. It also houses all core utilities (identity management, rate-limit mode constants, `listify`, `edgar_mode`, path configuration, URL builders, and date parsing) that every other module depends on.

---

### Public API surface

| Symbol | file:line | Purpose |
|---|---|---|
| `Filing` | `edgar/_filings.py:1411` | Single SEC filing — primary domain object |
| `Filings` | `edgar/_filings.py:527` | PyArrow-backed collection of filings |
| `FilingHeader` | `edgar/sgml/sgml_header.py:371` | Parsed SEC-HEADER metadata block from SGML |
| `FilingHomepage` | `edgar/attachments.py:917` | HTML index page scraped from EDGAR per filing |
| `Attachment` | `edgar/attachments.py:254` | Single document within a filing (HTML, XML, PDF, etc.) |
| `Attachments` | `edgar/attachments.py:488` | Ordered collection of `Attachment` objects |
| `CurrentFilings` | `edgar/current_filings.py:142` | Subclass of `Filings` for real-time (RSS Atom) data |
| `get_filings` | `edgar/_filings.py:1240` | Download quarterly index(es) and return `Filings` |
| `get_current_filings` | `edgar/current_filings.py:404` | Fetch current-day EDGAR feed; returns `CurrentFilings` |
| `get_all_current_filings` | `edgar/current_filings.py:363` | Iterate all pages and return plain `Filings` |
| `iter_current_filings_pages` | `edgar/current_filings.py:450` | Generator over `CurrentFilings` pages |
| `get_by_accession_number` | `edgar/_filings.py:2632` | Look up a `Filing` by accession number |
| `get_by_accession_number_enriched` | `edgar/_filings.py:2580` | Same but populates `related_entities` for multi-filer filings |
| `find` | `edgar/__init__.py:143` | Uber-search: accession/CIK/ticker/name → typed object |
| `obj` | `edgar/__init__.py:307` | Dispatch a `Filing` to its typed data class |
| `matches_form` | `edgar/__init__.py:179` | Test whether a `Filing.form` is in a form list (incl. `/A`) |
| `get_obj_info` | `edgar/__init__.py:195` | Static lookup: form string → (has_obj, class_name, description) |
| `DataObjectException` | `edgar/__init__.py:188` | Raised when `obj()` cannot construct a data object |
| `set_identity` | `edgar/core.py:169` | Set `EDGAR_IDENTITY` env var + reset HTTP clients |
| `get_identity` | `edgar/core.py:235` | Get identity, prompting interactively if unset |
| `edgar_mode` | `edgar/core.py:150` | Active `EdgarSettings` (rate-limit mode) |
| `NORMAL` / `CAUTION` / `CRAWL` | `edgar/core.py:142-148` | Preset `EdgarSettings` for rate limiting |
| `listify` | `edgar/core.py:516` | Coerce any value to a list |
| `HasContext` | `edgar/context.py:14` | Protocol: objects with `to_context(detail)` |
| `compose_context` | `edgar/context.py:25` | Assemble multiple `HasContext` objects into a token-budgeted string |
| `FormType` | `edgar/enums.py:55` | StrEnum of common SEC form type strings |
| `PeriodType` | `edgar/enums.py:124` | StrEnum: annual/quarterly/ttm/ytd |
| `StatementType` | `edgar/enums.py:148` | StrEnum: income_statement/balance_sheet/etc. |
| `FilerStatus` | `edgar/enums.py:188` | StrEnum: large-accelerated/accelerated/non-accelerated |
| `FilerCategory` | `edgar/enums.py:234` | Parsed compound category string (status + qualifications) |
| `ValidationError` | `edgar/enums.py:363` | ValueError subclass with fuzzy-match suggestions |
| `SecForms` | `edgar/forms.py:73` | DataFrame-backed SEC forms catalog (from SEC website) |
| `SecForm` | `edgar/forms.py:45` | Single row of SEC forms catalog |
| `list_forms` | `edgar/forms.py:23` | Cached fetch of all SEC form definitions (7 pages) |
| `Address` | `edgar/_party.py:25` | Pydantic model: street/city/state/zip |
| `Issuer` | `edgar/_party.py:84` | Parsed `<primaryIssuer>` XML block |
| `extract_dates` | `edgar/dates.py:14` | Parse date strings and ranges into (start, end, is_range) |
| `InvalidDateException` | `edgar/dates.py:9` | Raised on malformed date strings |
| `get_data_directory` | `edgar/paths.py:92` | Resolve `~/.edgar` (or `EDGAR_LOCAL_DATA_DIR`) |
| `set_data_directory` | `edgar/paths.py:120` | Override data directory path |
| `get_cache_directory` | `edgar/paths.py:149` | Resolve `~/.edgar_cache` (or `EDGAR_CACHE_DIR`) |
| `SEC_BASE_URL` | `edgar/config.py:33` | `https://www.sec.gov` (or `EDGAR_BASE_URL`) |
| `SEC_DATA_URL` | `edgar/config.py:34` | `https://data.sec.gov` (or `EDGAR_DATA_URL`) |
| `SEC_ARCHIVE_URL` | `edgar/config.py:36` | `{SEC_BASE_URL}/Archives/edgar` |
| `VERBOSE_EXCEPTIONS` | `edgar/config.py:48` | Bool flag for verbose exception logging |

---

### Key classes

#### `Filing` (`edgar/_filings.py:1411`)

Single SEC filing; owns identity fields and all lazy-loaded document access.

Constructor:
- `__init__(cik, company, form, filing_date, accession_no, related_entities=None)` — `edgar/_filings.py:1416`

Instance data (set at construction):
- `cik: int`, `company: str`, `form: str`, `filing_date: str`, `accession_no: str`
- `_related_entities: List[Dict]` — populated by `get_filing_at(enrich=True)` or `get_by_accession_number_enriched`
- `_filing_homepage`: lazily set on first `.homepage` access
- `_sgml`: lazily set on first `.sgml()` call

**Document-content methods (all cached):**

| Method | Returns | Purpose | file:line |
|---|---|---|---|
| `sgml() -> FilingSGML` | `FilingSGML` | Load/parse full SGML bundle; tries local storage, then datamule, then network; falls back to homepage on transient errors | `edgar/_filings.py:1872` |
| `html() -> Optional[str]` | `str\|None` | Primary document HTML; converts XML ownership forms to HTML; returns None for PDF/binary | `edgar/_filings.py:1598` |
| `xml() -> Optional[str]` | `str\|None` | Primary document XML; falls back to homepage XML attachment | `edgar/_filings.py:1639` |
| `text() -> str` | `str` | HTML→text via `HTMLParser`; falls back to TEXT-EXTRACT attachment | `edgar/_filings.py:1655` |
| `markdown(...) -> str` | `str` | HTML→Markdown via `to_markdown`; falls back to `text_to_markdown` | `edgar/_filings.py:1699` |
| `parse() -> Optional[Document]` | `Document\|None` | Parse HTML into structured `Document` tree (for section extraction) | `edgar/_filings.py:1735` |
| `xbrl() -> Optional[XBRL]` | `XBRL\|None` | Parse XBRL data; returns None if no XBRL, raises network errors (with local-storage hint) | `edgar/_filings.py:1765` |
| `full_text_submission() -> str` | `str` | Download full `.txt` SGML submission file | `edgar/_filings.py:1688` |

**Typed-object dispatch:**

| Method | Returns | Purpose | file:line |
|---|---|---|---|
| `obj() / data_object()` | `Optional[object]` | Delegates to module-level `obj(self)` function | `edgar/_filings.py:2004-2006` |
| `obj_type: Optional[str]` | property | Class name that `.obj()` would return, or None | `edgar/_filings.py:2009` |

**Document structure:**

| Property/Method | Returns | Purpose | file:line |
|---|---|---|---|
| `attachments` | `Attachments` | All documents in SGML bundle | `edgar/_filings.py:1587` |
| `exhibits` | list | `attachments.exhibits` shortcut | `edgar/_filings.py:1593` |
| `document` | `Attachment` | Primary display document (HTML/XHTML) | `edgar/_filings.py:1532` |
| `primary_documents` | list | Primary HTML + XML docs | `edgar/_filings.py:1550` |
| `period_of_report` | `Optional[str]` | Reporting period; from SGML header, fallback to homepage | `edgar/_filings.py:1560` |
| `header` | `FilingHeader` | Parsed SEC-HEADER metadata (cached_property) | `edgar/_filings.py:1994` |
| `reports` | `Optional[Reports]` | XBRL viewer reports (cached_property, from filing_summary) | `edgar/_filings.py:1922` |
| `statements` | `Optional[Statements]` | Financial statement reports (cached_property) | `edgar/_filings.py:1932` |
| `viewer` | `FilingViewer\|None` | SEC Interactive Data Viewer (cached_property) | `edgar/_filings.py:1940` |
| `agent` | `Optional[str]` | Filing agent name (cached_property, e.g. Workiva) | `edgar/_filings.py:1576` |

**Navigation & search:**

| Method | Returns | Purpose | file:line |
|---|---|---|---|
| `sections() -> List[str]` | `List[str]` | Sections list (cached); for HTML filings parses structure; for plain-text splits on `<PAGE>`/double-newline | `edgar/_filings.py:2035` |
| `search(query, regex=False)` | `SearchResults` | BM25 or regex search across sections; works on HTML and plain-text filings | `edgar/_filings.py:2053` |
| `grep(pattern, *, regex=False, document=None)` | `GrepResult` | grep-like search across all attachments; falls back to `_grep_filing_text()` for plain-text filings with empty attachment shells | `edgar/_filings.py:2061` |
| `_attachment_matches(attachment, document)` | `bool` | Filter helper: `"primary"` matches sequence `"1"`, else checks `document_type` and filename | `edgar/_filings.py:2127` |
| `_attachment_location(attachment)` | `str` | Label for grep result locations: `"primary"`, `document_type`, or `document` filename | `edgar/_filings.py:2137` |
| `_grep_filing_text(pattern, regex)` | `list` | Grep fallback for plain-text filings: calls `self.text()` and searches the combined filing text as `"primary"` | `edgar/_filings.py:2145` |
| `get_entity()` | `Company` | Company owning this filing (lru_cache) | `edgar/_filings.py:2172` |
| `related_filings()` | `CompanyFilings` | All filings sharing the same file_number | `edgar/_filings.py:2191` |
| `correspondence()` | `Optional[CorrespondenceThread]` | SEC correspondence thread (any form type) | `edgar/_filings.py:2223` |
| `as_company_filing()` | `CompanyFiling\|None` | Richer company-filing object via entity lookup | `edgar/_filings.py:2179` |

**URL properties:**

| Property | Value | file:line |
|---|---|---|
| `base_dir` | `{SEC_ARCHIVE_URL}/data/{cik}/{accession_no_nodash}` | `edgar/_filings.py:2149` |
| `homepage_url` | `{SEC_ARCHIVE_URL}/data/{cik}/{accession_no}-index.html` | `edgar/_filings.py:2137` |
| `text_url` | `{base_dir}/{accession_no}.txt` | `edgar/_filings.py:2141` |
| `url` | alias for `homepage_url` | `edgar/_filings.py:2153` |
| `homepage` | `FilingHomepage` | Lazy-loaded index page | `edgar/_filings.py:2157` |

**Multi-entity support:**

| Property/Method | Purpose | file:line |
|---|---|---|
| `is_multi_entity: bool` | True if filing has multiple filers (index or header) | `edgar/_filings.py:1510` |
| `all_ciks: List[int]` | All CIKs including related entities | `edgar/_filings.py:1443` |
| `all_entities: List[Dict]` | All `{cik, company}` dicts | `edgar/_filings.py:1475` |

**Persistence:**

| Method | Purpose | file:line |
|---|---|---|
| `save(directory_or_file)` | Pickle to file; preloads SGML first | `edgar/_filings.py:1796` |
| `load(path) -> Filing` | Load from pickle | `edgar/_filings.py:1816` |
| `from_sgml(source) -> Filing` | Construct from SGML file/string | `edgar/_filings.py:1833` |
| `from_sgml_text(text) -> Filing` | Construct from full-text submission string | `edgar/_filings.py:1853` |
| `from_dict(data) -> Filing` | Construct from dict with 5 required keys | `edgar/_filings.py:1973` |
| `to_dict() -> Dict` | Serialize to 5-key dict | `edgar/_filings.py:1965` |

**AI integration:**

| Method | Purpose | file:line |
|---|---|---|
| `to_context(detail='standard') -> str` | LLM-optimized markdown-KV context (minimal/standard/full) | `edgar/_filings.py:2278` |

---

#### `Filings` (`edgar/_filings.py:527`)

PyArrow Table-backed filing collection. Implements Python sequence protocol plus pagination.

Constructor:
- `__init__(filing_index: pa.Table, original_state: Optional[PagingState] = None)` — `edgar/_filings.py:532`
- `self.data: pa.Table` — 5 columns: `form(str)`, `company(str)`, `cik(int32)`, `filing_date(date32)`, `accession_number(str)`
- `self.data_pager: DataPager` — default page_size=50

**Filtering & selection:**

| Method | Returns | Purpose | file:line |
|---|---|---|---|
| `filter(*, form, amendments, filing_date, date, cik, exchange, ticker, accession_number) -> Filings` | `Filings` | Chainable multi-criterion filter; `date` and `filing_date` are aliases | `edgar/_filings.py:654` |
| `head(n) -> Filings` | `Filings` | First n filings | `edgar/_filings.py:748` |
| `tail(n) -> Filings` | `Filings` | Last n filings | `edgar/_filings.py:759` |
| `sample(n) -> Filings` | `Filings` | Random sample | `edgar/_filings.py:767` |
| `latest(n=1)` | `Filing` or `Filings` | Latest n by filing_date descending; returns single `Filing` if n=1 | `edgar/_filings.py:636` |
| `find(company_search_str) -> Filings` | `Filings` | Search by company name via `find_company` then filter by CIK | `edgar/_filings.py:836` |
| `get(index_or_accession_number)` | `Filing\|None` | By integer index or accession number string | `edgar/_filings.py:809` |

**Pagination:**

| Method | Purpose | file:line |
|---|---|---|
| `next() -> Optional[Filings]` | Next page (page_size=50); warns at end | `edgar/_filings.py:780` |
| `previous() -> Optional[Filings]` | Previous page | `edgar/_filings.py:790` |
| `current()` | Returns self (for symmetry) | `edgar/_filings.py:776` |

**Sequence protocol:**

| Dunder | Behavior | file:line |
|---|---|---|
| `__getitem__(int)` | `get_filing_at(item)` — constructs `Filing` with related-entity enrichment | `edgar/_filings.py:849` |
| `__getitem__(slice)` | Returns `Filings` slice (step!=1 returns list) | `edgar/_filings.py:850-856` |
| `__iter__` / `__next__` | Standard iteration yielding `Filing` objects | `edgar/_filings.py:862-872` |
| `__len__` | `len(self.data)` | `edgar/_filings.py:859` |
| `__eq__` | Compares accession_number columns | `edgar/_filings.py:889` |
| `__hash__` | Hash of length + first/mid/last accession numbers | `edgar/_filings.py:907` |

**Output:**

| Method | Purpose | file:line |
|---|---|---|
| `to_pandas(*columns) -> pd.DataFrame` | Export to DataFrame | `edgar/_filings.py:545` |
| `to_dict(max_rows=1000) -> Dict` | JSON-serializable list of records | `edgar/_filings.py:845` |
| `to_context(detail='standard') -> str` | LLM-optimized context | `edgar/_filings.py:928` |
| `save_parquet(location)` / `save(location)` | Write parquet | `edgar/_filings.py:550-556` |
| `download(data_directory, compress, ...)` | Download actual filing files to local storage | `edgar/_filings.py:558` |

**Properties:**

| Property | Returns | file:line |
|---|---|---|
| `date_range` | `Tuple[datetime, datetime]` (min, max) | `edgar/_filings.py:621` |
| `start_date / end_date` | `Optional[str]` | `edgar/_filings.py:627-633` |
| `empty` | `bool` | `edgar/_filings.py:773` |
| `summary` | summary string | `edgar/_filings.py:875` |
| `docs` | `Docs` object (API documentation) | `edgar/_filings.py:541` |

---

#### `CurrentFilings` (`edgar/current_filings.py:142`)

Extends `Filings` for the EDGAR RSS Atom feed (real-time data). The underlying `pa.Table` gains a 6th column: `accepted: timestamp('s')`.

Constructor:
- `__init__(filing_index, form='', start=1, page_size=40, owner='include')` — `edgar/current_filings.py:148`

Key overrides:
- `next()` — fetches the next page from EDGAR (mutates `self.data` and `self._start`) — `edgar/current_filings.py:171`
- `previous()` — fetches previous page — `edgar/current_filings.py:182`
- `get(index_or_accession_number)` — uses page-relative indexing; searches beyond current page for accession lookups — `edgar/current_filings.py:217`
- `__getitem__` — raises `IndexError`/`KeyError` (not None) on miss — `edgar/current_filings.py:194`
- `current_page: int` property — 1-indexed current page number — `edgar/current_filings.py:161`

---

#### `FilingHeader` (`edgar/sgml/sgml_header.py:371`)

Parsed SEC-HEADER from the SGML submission. Accessed via `filing.header`.

Key properties (all read from `self.filing_metadata`):
- `accession_number`, `cik`, `form`, `period_of_report`, `filing_date`, `date_as_of_change`, `document_count`, `acceptance_datetime`, `file_numbers` — `edgar/sgml/sgml_header.py:397-451`

Child objects in `FilingHeader`:
- `filers: List[Filer]` — company filers with `company_information` (name, CIK, SIC, etc.)
- `reporting_owners: List[ReportingOwner]` — for Forms 3/4/5
- `issuer: Optional[Issuer]` — for Forms 3/4/5
- `subject_companies: List[SubjectCompany]`

---

#### `FilingHomepage` (`edgar/attachments.py:917`)

Scraped HTML index page from `{SEC_ARCHIVE_URL}/data/{cik}/{accession_no}-index.html`.

Constructor: `__init__(url, soup, attachments)` — `edgar/attachments.py:918`

Key properties:
- `attachments: Attachments`
- `primary_html_document: Optional[Attachment]`, `primary_xml_document: Optional[Attachment]`
- `period_of_report: Optional[str]` — `edgar/attachments.py:1016`
- `xbrl_document` — finds XBRL instance document from data_files
- `get_filers()` — parses filer divs from soup — `edgar/attachments.py:966`

Class method: `FilingHomepage.load(url) -> FilingHomepage` — `edgar/attachments.py` (fetches and parses)

---

#### `Attachment` (`edgar/attachments.py:254`)

A single document in a filing.

Constructor fields: `sequence_number, description, document, ixbrl, path, document_type, size, sgml_document, purpose, filing_sgml`

Key properties:
- `content` — downloads via `sgml_document.content` or `download_file(url)`; patchable for tests — `edgar/attachments.py:283`
- `url` — constructed via `sec_document_url(self.path)` — `edgar/attachments.py:330`
- `extension` — file extension (`.html`, `.xml`, `.pdf`, `.paper`, etc.) — `edgar/attachments.py:334`
- `display_description` — uses `purpose`, then `description`, then standard exhibit description lookup — `edgar/attachments.py:313`
- `is_text()`, `is_binary()`, `empty` — content-type predicates
- `text()` — HTML→text conversion

---

#### `Attachments` (`edgar/attachments.py:488`)

Ordered container of `Attachment` objects split into `documents` and `data_files`.

| Method | Purpose | file:line |
|---|---|---|
| `__getitem__(int\|str)` | By sequence number (int) or filename (str) | `edgar/attachments.py:506` |
| `get_by_sequence(seq)` | By exact sequence number | `edgar/attachments.py:518` |
| `get_by_index(index)` | By list index (0-based) | `edgar/attachments.py:528` |
| `primary_html_document` | First `.html`/`.htm` in primary_documents | `edgar/attachments.py:547` |
| `primary_xml_document` | First `.xml` in primary_documents | `edgar/attachments.py:563` |
| `query(condition_str)` | Filter by column expression | (further in file) |

---

#### `EdgarSettings` / `edgar_mode` (`edgar/core.py:121-159`)

Dataclass controlling HTTP rate limiting. Three presets:

| Name | http_timeout | max_connections | retries | file:line |
|---|---|---|---|---|
| `NORMAL` | 15s | 10 | 3 | `edgar/core.py:142` |
| `CAUTION` | 20s | 5 | 3 | `edgar/core.py:145` |
| `CRAWL` | 25s | 2 | 2 | `edgar/core.py:148` |

`edgar_mode` is the active mode, initialized from `EDGAR_ACCESS_MODE` env var (default: `NORMAL`) — `edgar/core.py:150-159`.

---

#### `HasContext` / `compose_context` (`edgar/context.py`)

`HasContext` is a `runtime_checkable` Protocol — any object with `to_context(detail='standard') -> str` satisfies it without inheritance — `edgar/context.py:14`.

`compose_context(objects, max_tokens=2000, detail='standard', separator) -> str` — `edgar/context.py:25`:
- First object gets 60% of char budget; remainder split equally
- Auto-downgrades detail level (full → standard → minimal) if over budget
- Fallback to `str()` if object lacks `to_context`

---

### Class hierarchy

```
Filings
└── CurrentFilings          # real-time RSS Atom feed; overrides next()/previous()/get()

Filing                      # standalone — not a subclass of anything

FilingHeader                # from sgml/sgml_header.py; accessed via filing.header

FilingHomepage              # from attachments.py; accessed via filing.homepage

Attachment                  # from attachments.py

Attachments                 # from attachments.py; accessed via filing.attachments

Address (pydantic.BaseModel)  # _party.py; used in FilingHeader filer data

EdgarSettings (dataclass)   # core.py; NORMAL / CAUTION / CRAWL are instances

SecForms                    # forms.py; wraps pd.DataFrame of SEC form catalog
SecForm (frozen dataclass)  # forms.py; single form entry

FormType (StrEnum)          # enums.py
PeriodType (StrEnum)
StatementType (StrEnum)
FilerStatus (StrEnum)
FilerCategory               # enums.py; not a StrEnum — composite parsed object

HasContext (Protocol)       # context.py — runtime-checkable; Filing and Filings satisfy it
```

---

### Configuration & options

#### `get_filings` parameters

| Option | Type | Default | Effect |
|---|---|---|---|
| `year` | `Optional[Years]` | current year | Calendar year(s) of filing — NOT fiscal year |
| `quarter` | `Optional[Quarters]` | all quarters in year | Quarter(s) 1-4 |
| `form` | `Optional[str\|List]` | None | Form filter (applied post-download) |
| `amendments` | `bool` | `True` | Include `/A` amendment forms |
| `filing_date` | `Optional[str]` | None | YYYY-MM-DD or YYYY-MM-DD:YYYY-MM-DD range |
| `index` | `str` | `"form"` | Index type: `"form"`, `"company"`, or `"xbrl"` |
| `priority_sorted_forms` | `Optional[List[str]]` | None | Form priority for display sort |

#### `get_current_filings` parameters

| Option | Type | Default | Effect |
|---|---|---|---|
| `form` | `str` | `''` | Form type filter (also applied client-side, see Gotchas) |
| `owner` | `str` | `'include'` | `'include'`, `'exclude'`, `'only'` |
| `page_size` | `Optional[int]` | `40` | Valid: 10/20/40/80/100; `None` fetches all pages |

#### `Filings.filter` parameters

| Option | Type | Effect |
|---|---|---|
| `form` | `str\|List` | Form type(s) |
| `amendments` | `Optional[bool]` | If None: no amendment filter; False: strip /A; True: add /A |
| `filing_date` / `date` | `str` | YYYY-MM-DD or range with `:` |
| `cik` | `IntString\|List` | CIK filter |
| `exchange` | `str\|List\|Exchange` | Exchange filter (resolves via ticker lookup) |
| `ticker` | `str\|List` | Ticker symbol filter (resolves via CIK) |
| `accession_number` | `str\|List` | Exact accession number(s) |

#### Environment variables

| Variable | Module | Default | Effect |
|---|---|---|---|
| `EDGAR_IDENTITY` | `edgar/core.py:161` | (required) | UserAgent string sent to SEC |
| `EDGAR_ACCESS_MODE` | `edgar/core.py:150` | `'NORMAL'` | `NORMAL`, `CAUTION`, or `CRAWL` |
| `EDGAR_BASE_URL` | `edgar/config.py:33` | `https://www.sec.gov` | Override SEC base URL (mirrors) |
| `EDGAR_DATA_URL` | `edgar/config.py:34` | `https://data.sec.gov` | Override data API URL |
| `EDGAR_XBRL_URL` | `edgar/config.py:35` | `http://xbrl.sec.gov` | Override XBRL taxonomy URL |
| `EDGAR_VERBOSE_EXCEPTIONS` | `edgar/config.py:48` | `false` | Log caught exceptions verbosely |
| `EDGAR_LOCAL_DATA_DIR` | `edgar/paths.py:51` | `~/.edgar` | Root for local filing storage |
| `EDGAR_CACHE_DIR` | `edgar/paths.py:52` | `~/.edgar_cache` | Root for search/anchor caches |
| `EDGAR_TEST_DIR` | `edgar/paths.py:53` | `~/.edgar_test` | Test harness data directory |
| `CLAUDE_SKILLS_DIR` | `edgar/paths.py:54` | `~/.claude/skills` | Claude skills install path |

---

### Data flow / lifecycle

**Historical retrieval (`get_filings`):**
1. `get_filings(year, quarter, form)` calls `expand_quarters(year, quarter)` to build a list of `(year, quarter)` tuples — `edgar/_filings.py:1317-1323`
2. `get_filings_for_quarters` fetches quarterly index GZ files in parallel using `parallel_thread_map` — `edgar/_filings.py:504-524`
3. Each quarterly index is parsed by `fetch_filing_index_at_url` → `read_index_file` → `pa.Table` with 5 columns — `edgar/_filings.py:470-482`
4. Tables are concatenated into a single `pa.Table`, wrapped in `Filings`
5. Optional `form`/`filing_date` filters applied via `Filings.filter()`
6. `sort_filings_by_priority` adds a temporary priority column, sorts by date+priority, drops the column — `edgar/_filings.py:1196`
7. Returns `Filings(sorted_filing_index)`

**Real-time retrieval (`get_current_filings`):**
1. Calls EDGAR's browse-edgar RSS Atom endpoint — `edgar/current_filings.py:107`
2. Parses `<entry>` elements: title → (form, company, CIK, status), summary → (date, accession_no), `<updated>` → accepted timestamp — `edgar/current_filings.py:118-138`
3. Returns `CurrentFilings` wrapping a `pa.Table` with 6 columns (adds `accepted`)
4. `next()`/`previous()` refetch pages by adjusting `start` offset; mutate `self.data` in-place

**Filing construction:**
- `Filings.__getitem__(n)` → `get_filing_at(n, enrich=True)` — scans ±10 rows for same accession number to populate `related_entities` — `edgar/_filings.py:585-618`
- `Filing` is created with identity fields; all content is lazy

**Filing SGML loading (`filing.sgml()`):**
1. Returns cached `self._sgml` if already loaded
2. If local storage enabled: tries `local_filing_path(filing_date, accession_no)` — `edgar/_filings.py:1882-1886`
3. If datamule storage: tries `get_datamule_filing(accession_no)` — `edgar/_filings.py:1889-1892`
4. Network fallback: `FilingSGML.from_filing(self)` downloads `.txt` bundle — `edgar/_filings.py:1902`
5. On permanent errors (identity not set, filing not found): propagates
6. On transient content errors: falls back to `FilingSGML.from_homepage(self.homepage)` — `edgar/_filings.py:1919`

**`filing.obj()` dispatch:**
1. Calls module-level `obj(filing)` in `edgar/__init__.py:307`
2. `matches_form(filing, form_str)` tests `filing.form in [form, form+"/A"]` — `edgar/__init__.py:179`
3. Dispatch is a sequential if/elif chain over 40+ form types — `edgar/__init__.py:323-438`
4. Special case for `10-D`: only returns `TenD` if EX-102 CMBS data present — `edgar/__init__.py:334-342`
5. Fallback: checks `XML_FILING_FORMS` set, then tries `filing.xbrl()` — `edgar/__init__.py:432-438`
6. Returns `None` for completely unknown form types with no XBRL

**`find()` regex dispatch (`edgar/__init__.py:143`):**
- Input is `int` → `Entity(search_id)` (CIK)
- `\d{10}-\d{2}-\d{6}` → `get_by_accession_number_enriched` (dashed accession)
- `^\d{18}$` → reformat to dashed accession then retrieve
- `\d{4,10}$` → `Entity(search_id)` (numeric CIK string)
- `^[A-WYZ]{1,5}([.-][A-Z])?$` → `Entity(ticker)` with `find_company` fallback
- `^[A-Z]{4}X$` → `find_fund` (mutual fund ticker)
- `^[CS]\d+$` → `find_fund` (series/class ID)
- `^\d{6,}-` → None (likely malformed accession)
- else → `find_company(search_id)` (company name search)

**Caching layers:**
- `_get_cached_filings` — `lru_cache(maxsize=8)` for quarterly index tables — `edgar/_filings.py:1362`
- `available_quarters()` — `lru_cache(maxsize=1)` — `edgar/_filings.py:246`
- `find()` — `lru_cache(maxsize=16)` — `edgar/__init__.py:142`
- `filing.html()`, `xml()`, `text()`, `sections()` — `lru_cache(maxsize=4)` per filing instance
- `filing.header`, `filing.reports`, `filing.statements`, `filing.viewer`, `filing.agent` — `cached_property`
- `filing.homepage` — simple `_filing_homepage` instance cache (not `cached_property`)
- `list_forms()` — `lru_cache(maxsize=1)` — `edgar/forms.py:23`
- `filing.get_entity()`, `as_company_filing()`, `related_filings()` — `lru_cache(maxsize=1)`

---

### Design patterns

- **Lazy loading everywhere**: `Filing` stores only identity fields at construction. SGML, homepage, header, XBRL, HTML/text are all loaded on first access and cached. This avoids network calls unless the data is needed.
- **PyArrow as internal storage spine**: `Filings.data` is a `pa.Table`. All filtering, slicing, date-range computation, and sort operations use `pyarrow.compute` for vectorized performance. Conversion to pandas is explicit (`to_pandas()`).
- **Strategy pattern for rate limiting**: `EdgarSettings` instances (`NORMAL`/`CAUTION`/`CRAWL`) are interchangeable configurations; the active one is referenced by the module-level `edgar_mode` variable, read by `httpclient`.
- **Template method / fallback chain for SGML loading**: `filing.sgml()` implements a priority chain (local storage → datamule → network → homepage fallback) without the caller knowing which path was taken.
- **Protocol-based duck typing for AI context**: `HasContext` is a `runtime_checkable` Protocol — no inheritance needed; `compose_context` uses it for token-budget composition.
- **`lru_cache` on module-level functions for index caching**: `_get_cached_filings` caches quarterly index fetches (8 quarters) so that multiple `get_by_accession_number` calls within a session don't re-download the same index.
- **`cache_except_none` decorator**: Custom caching that clears None results from `lru_cache`, ensuring transient None results don't get permanently cached — `edgar/core.py:552`.
- **Partial functions for domain-specific shortcuts**: `get_fund_portfolio_filings`, `get_insider_transaction_filings`, etc. are `functools.partial(get_filings, form=...)` defined in `__init__.py:127-139`.
- **StrEnum for form/period/statement types** (`edgar/enums.py`): StrEnum values equal their string equivalents, so both `FormType.ANNUAL_REPORT` and `"10-K"` work in any function accepting `Union[FormType, str]`.
- **Fuzzy validation with typo detection**: `enhanced_validate` in `edgar/enums.py:488` combines exact match, case-insensitive match, common typo patterns (missing hyphens, transpositions), and difflib fuzzy matching to produce `ValidationError` with suggestions.

---

### Cross-domain interactions

**What this domain imports:**

| Module | Used for |
|---|---|
| `edgar.attachments` | `Attachment`, `Attachments`, `FilingHomepage` |
| `edgar.sgml` | `FilingHeader`, `FilingSGML`, `Reports`, `Statements` |
| `edgar.xbrl` | `XBRL`, `XBRLFilingWithNoXbrlData` |
| `edgar.storage` | `is_using_local_storage`, `local_filing_path` |
| `edgar.documents` | `HTMLParser`, `ParserConfig` |
| `edgar.filtering` | `filter_by_form`, `filter_by_date`, `filter_by_cik`, `filter_by_ticker`, `filter_by_exchange`, `filter_by_accession_number` |
| `edgar.search` | `BM25Search`, `RegexSearch` |
| `edgar.httprequests` | `download_file`, `download_text` |
| `edgar.reference` | `describe_form`, `find_ticker` |
| `edgar.dates` | `extract_dates`, `InvalidDateException` |
| `edgar.urls` | `build_full_index_url`, `build_daily_index_url` |
| `edgar.config` | `SEC_ARCHIVE_URL`, `SEC_BASE_URL` |
| `edgar.core` | `DataPager`, `PagingState`, `listify`, `parallel_thread_map`, etc. |

**What other domains import from this domain:**

- `edgar.entity` — imports `Filing`, `Filings` (and `Filings` subclass `CompanyFilings`)
- `edgar.company_reports` — every report class (TenK, TenQ, EightK, etc.) receives a `Filing` object
- `edgar.ownership`, `edgar.thirteenf`, `edgar.funds.*`, `edgar.proxy`, etc. — all receive a `Filing` via their `from_filing(filing)` factory
- `edgar.current_filings` — imports `Filings` as its base class
- `edgar.search.efts` — `EFTSSearch` returns `Filing`/`Filings` objects
- `edgar.storage` — `download_filings(filings=...)` accepts a `Filings` object
- `edgar.__init__` — re-exports everything; defines `find()`, `obj()`, `matches_form()`, `get_obj_info()`, `DataObjectException`

---

### Gotchas & notable behaviors

1. **Calendar year, not fiscal year**: `get_filings(2024)` returns filings *submitted* in 2024, not filings *covering* fiscal year 2024. A March-fiscal-year 10-K filed in June 2024 is in `get_filings(2024)`, not `get_filings(2023)` — `edgar/_filings.py:1252`.

2. **Quarterly index lag**: `get_filings` uses quarterly indexes that are updated daily but typically lag 1 business day. The library detects this: `latest()` and `filter(date=today)` emit a `print_warning` suggesting `get_current_filings()` if data is >= 2 days stale — `edgar/_filings.py:636-648` and `edgar/_filings.py:711-716`.

3. **SEC API ignores form parameter for current filings**: `get_current_filings(form="10-K")` sends `type=10-K` to the browse-edgar endpoint, but the SEC API silently ignores it. `get_all_current_filings` applies a client-side filter after fetching — `edgar/current_filings.py:396-399`. Single-page `CurrentFilings` does NOT automatically apply this filter.

4. **`find()` is `lru_cache`d**: `find("AAPL")` is cached globally (maxsize=16). In long sessions with many different searches, oldest results will be evicted. — `edgar/__init__.py:142`.

5. **`obj()` for `10-D`**: Returns `TenD` only if the filing has EX-102 CMBS XML data. Non-CMBS 10-D filings return None from `obj()` — `edgar/__init__.py:334-341`.

6. **`obj()` fallback to XBRL**: If no form-specific parser matches, `obj()` tries `filing.xbrl()` and returns the `XBRL` object — `edgar/__init__.py:436-438`. This is the final fallback for forms not in the dispatch table but that happen to include XBRL.

7. **`Filings.filter(amendments=None)` vs `False`**: When `amendments=None` (default), no amendment logic runs. When `amendments=False`, `/A` variants are stripped. When `amendments=True`, `/A` variants are added to the form list — `edgar/_filings.py:700-705`.

8. **`latest()` with n=1 returns a `Filing`, not `Filings`**: If `n=1`, the method unwraps and returns the single `Filing` directly. `n > 1` returns a `Filings`. This asymmetry affects type-checking — `edgar/_filings.py:636-652`.

9. **SGML fallback to homepage**: If the full-text `.txt` submission cannot be fetched (transient HTTP error), `filing.sgml()` silently falls back to constructing a minimal `FilingSGML` from the filing's homepage. This means `filing.period_of_report` may return None even when the filing exists — `edgar/_filings.py:1916-1919`.

10. **Multi-entity enrichment**: `Filings.get_filing_at(item, enrich=True)` searches ±10 rows from the requested index for identical accession numbers to find co-filers. The ±10 window is a performance heuristic — co-filing entries are typically adjacent in the index — `edgar/_filings.py:590-617`.

11. **`get_by_accession_number` extracts filing year from accession number format**: The 11th–13th characters of the accession number encode the year (`19xx` if char 11 is `9`, else `20xx`). This drives which quarterly index to search — `edgar/_filings.py:2634`.

12. **`accession_no` vs `accession_number`**: `Filing` stores `self.accession_no` as the canonical attribute, but `self.accession_number` is a property alias. External code should prefer `accession_number` as it matches the `Filings.data` column name — `edgar/_filings.py:1438`.

13. **`CurrentFilings.next()` mutates in-place**: Unlike `Filings.next()` which returns a new `Filings` object, `CurrentFilings.next()` modifies `self.data` and `self._start` and returns `self`. Iterating via a stored reference to a `CurrentFilings` instance will lose data for the previous page — `edgar/current_filings.py:171-179`.

14. **`edgar_mode` is module-level mutable state**: Reassigning `edgar_mode = CRAWL` at runtime affects all subsequent HTTP calls. Changing it does not close existing HTTP client connections; call `edgar.httpclient.close_clients()` if needed — `edgar/core.py:150`.

15. **Identity required before any network call**: `get_identity()` prompts interactively with a 60-second timeout if `EDGAR_IDENTITY` is not set. In non-interactive environments (CI, scripts) this will raise `TimeoutError` — `edgar/core.py:212-232`.

16. **`save_parquet` / `save` stores only the index, not document content**: Saving a `Filings` object persists only the 5-column filing index. To persist a `Filing` with its content, use `filing.save(path)` (pickle) which pre-loads SGML before pickling — `edgar/_filings.py:1807`.

17. **`grep()` and `search()` work on plain-text filings**: Older filings (pre-HTML SGML era) produce empty `Attachment.text()` shells. `grep()` detects `found_any_text == False` and calls `_grep_filing_text()` which fetches via `filing.text()` as a single `"primary"` location. `search()` / `sections()` split the text on `<PAGE>` markers and double-blank-line boundaries. The `document` filter on `grep()` only narrows to `"primary"` for these filings (other document filters yield no matches since there are no usable attachments).
