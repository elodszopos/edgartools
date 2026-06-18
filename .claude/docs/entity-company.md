## Entity & Company Domain

### Overview

The `edgar.entity` package is the core domain model for all SEC filing entities. It provides a unified, layered abstraction for companies, funds, and individuals: a thin `SecFiler` abstract base, a concrete `Entity` class for any CIK, and a richer `Company` subclass for public companies. Entity metadata and filing history come from the SEC submissions API (`/submissions/CIK*.json`); financial facts come from the SEC company-facts XBRL API (`/api/xbrl/companyfacts/CIK*.json`). The `EntityFacts` class (in `entity_facts.py`) is the AI-optimized container for all XBRL financial data, with built-in statement builders, TTM calculation, concept discovery, and period-normalized query interfaces. Ticker/CIK resolution is handled by a reference data layer backed by a bundled parquet file with live-API fallback.

---

### Public API surface

| Symbol | file:line | Purpose |
|--------|-----------|---------|
| `Company` | `edgar/entity/core.py:570` | Public company — get facts, financials, filings |
| `Entity` | `edgar/entity/core.py:234` | Generic SEC filer by CIK |
| `SecFiler` | `edgar/entity/core.py:203` | Abstract base: `get_filings`, `get_facts`, `cik`, `data` |
| `get_entity(cik_or_identifier)` | `edgar/entity/core.py:1748` | Factory: returns `Entity` |
| `get_company(cik_or_ticker)` | `edgar/entity/core.py:1761` | Factory: returns `Company` |
| `public_companies()` | `edgar/entity/core.py:1774` | Iterable over all known public companies via ticker reference |
| `CompanyNotFoundError` | `edgar/entity/core.py:70` | Raised when ticker/CIK cannot be resolved |
| `EntityData` | `edgar/entity/data.py:291` | Parsed submissions metadata + lazy-loaded filings |
| `CompanyData` | `edgar/entity/data.py:796` | `EntityData` subclass with company-specific helpers |
| `Address` | `edgar/entity/data.py:202` | Physical address with `__slots__` and string cache |
| `EntityFacts` | `edgar/entity/entity_facts.py:136` | AI-ready XBRL facts container |
| `NoCompanyFactsFound` | `edgar/entity/entity_facts.py:43` | Raised when CIK has no XBRL facts (404 from SEC) |
| `get_company_facts(cik)` | `edgar/entity/entity_facts.py:97` | Fetch/cache EntityFacts for a CIK |
| `clear_company_facts_cache()` | `edgar/entity/entity_facts.py:87` | Flush in-memory LRU facts cache |
| `EntityFiling` | `edgar/entity/filings.py:32` | Single filing with metadata fields |
| `EntityFilings` | `edgar/entity/filings.py:176` | Paginated collection of filings backed by PyArrow table |
| `find_company(name, top_n)` | `edgar/entity/search.py:105` | Fuzzy name search → `CompanySearchResults` |
| `CompanySearchResults` | `edgar/entity/search.py:24` | Search result list with `Company` access via `[i]` |
| `CompanySearchIndex` | `edgar/entity/search.py:69` | Cached `FastSearch` index over company tickers |
| `find_cik(ticker)` | `edgar/reference/tickers.py:498` | Ticker → CIK lookup (company + mutual fund) |
| `find_ticker(cik)` | `edgar/reference/tickers.py:318` | CIK → ticker lookup |
| `get_company_tickers(as_dataframe, clean_name)` | `edgar/reference/tickers.py:104` | Full ticker/CIK/exchange table |
| `get_ticker_to_cik_lookup()` | `edgar/entity/tickers.py:16` | Cached dict: ticker → CIK |
| `get_cik_lookup_data()` | `edgar/entity/tickers.py:37` | Cached DataFrame of all CIK→name from SEC |
| `parse_entity_submissions(cjson)` | `edgar/entity/data.py:140` | Deserialize submissions JSON → `CompanyData` |
| `get_entity_submissions(cik)` | `edgar/entity/submissions.py:141` | Fetch/parse submissions (local or live) |
| `create_entity_from_submissions_json(json, entity_type)` | `edgar/entity/submissions.py:165` | Build Entity/Company from raw JSON (for testing) |
| `create_entity_from_file(file_path, entity_type)` | `edgar/entity/submissions.py:220` | Load entity from local JSON file |
| `create_company_from_file(file_path)` | `edgar/entity/submissions.py:252` | Convenience: load Company from local JSON |
| `normalize_cik(cik_or_identifier)` | `edgar/entity/utils.py:98` | Strip leading zeros → int |
| `has_company_filings(form_array, max_filings)` | `edgar/entity/utils.py:39` | Check PyArrow array for company form types |
| `COMPANY_FORMS` | `edgar/entity/constants.py:12` | Set of ~70 company-only form codes |
| `BusinessCategory` | `edgar/entity/categorization.py:40` | Enum: Operating Company, ETF, REIT, Bank, etc. |
| `FinancialFact` | `edgar/entity/models.py:21` | Slot-optimized dataclass for a single XBRL fact |
| `ConceptSearchResults` | `edgar/entity/models.py:285` | Results of `EntityFacts.search_concepts()` |
| `PeriodSummary` | `edgar/entity/models.py:376` | Results of `EntityFacts.available_periods()` |

Backward compatibility aliases: `CompanyFiling = EntityFiling`, `CompanyFilings = EntityFilings`, `CompanyFacts = EntityFacts` (in `filings.py:680-682`).

---

### Key classes

#### `SecFiler` (`edgar/entity/core.py:203`)
Abstract base. Declares the four required abstract members: `get_filings(**kwargs) -> Filings`, `get_facts() -> Optional[EntityFacts]`, `cik -> int`, `data -> EntityData`. All concrete entity types must implement these.

#### `Entity(SecFiler)` (`edgar/entity/core.py:234`)
Concrete, general-purpose filer.

- `__init__(cik_or_identifier)` — accepts CIK (int or zero-padded string) or ticker string; calls `find_cik()` if non-numeric, raises `CompanyNotFoundError` with fuzzy suggestions on miss — `core.py:242`
- `cik -> int` (property) — `core.py:258`
- `name -> Optional[str]` (property) — delegates to `self.data.name` — `core.py:263`
- `display_name -> str` (`cached_property`) — reverses name for individuals (e.g., "SMITH JOHN" → "John Smith") — `core.py:270`
- `data -> EntityData` (`cached_property`) — lazily fetches via `get_entity_submissions(cik)`; on 404 fills a synthetic placeholder and sets `_data._not_found = True` — `core.py:277`
- `not_found -> bool` (property) — triggers `data` load if needed, returns `_data._not_found` — `core.py:309`
- `is_company -> bool` / `is_individual -> bool` (properties) — delegates to `data.is_company` — `core.py:324/333`
- `filer_category -> FilerCategory` (`cached_property`) — parses SEC `category` string into typed enum — `core.py:344`
- `is_large_accelerated_filer / is_accelerated_filer / is_non_accelerated_filer / is_smaller_reporting_company / is_emerging_growth_company` — convenience booleans from `filer_category` — `core.py:372-394`
- `get_filings(year, quarter, form, accession_number, file_number, filing_date, date, amendments, is_xbrl, is_inline_xbrl, sort_by, trigger_full_load) -> EntityFilings` — full filter pass-through to `EntityData.get_filings()`; `trigger_full_load=True` triggers lazy pagination — `core.py:396`
- `get_facts(period_type) -> Optional[EntityFacts]` — calls `get_company_facts(cik)`, applies `filter_by_period_type()` if requested, returns `None` on `NoCompanyFactsFound` — `core.py:466`
- `get_structured_statement(statement_type, fiscal_year, fiscal_period, use_canonical, include_missing) -> Optional[StructuredStatement]` — delegates to `StatementBuilder` — `core.py:486`
- `latest(form, n)` — gets latest n filings for a form type, with full-load fallback — `core.py:541`
- `__bool__` — returns `not self.not_found`; allows `if company:` pattern — `core.py:561`
- `mailing_address() / business_address() -> Optional[Address]` — `core.py:297/303`

#### `Company(Entity)` (`edgar/entity/core.py:570`)
Adds company-specific analytics on top of `Entity`.

- `tickers -> List[str]` (property) — `core.py:591`
- `get_ticker() -> Optional[str]` — first ticker — `core.py:597`
- `get_exchanges() -> List[str]` — `core.py:603`
- `get_financials() -> Optional[Financials]` — latest 10-K (→ 20-F → 40-F fallback), parses via `Financials.extract()` — `core.py:609`
- `get_quarterly_financials() -> Optional[Financials]` — latest 10-Q (→ 6-K fallback) — `core.py:638`
- `fiscal_year_end -> Optional[str]` (property) — `core.py:664`
- `sic -> Optional[str]` / `industry -> Optional[str]` (properties) — `core.py:671/679`
- `is_foreign -> bool` (property) — uses `state_of_incorporation` → `is_foreign_company()` then falls back to `filer_type` — `core.py:686`
- `filer_type -> Optional[str]` (`cached_property`) — `'Domestic'`, `'Foreign'`, `'Canadian'`, or `None`; uses state of incorporation first, then form-type signals (40-F, 20-F, 10-K) — `core.py:711`
- `business_category -> str` (`cached_property`) — multi-signal classification via `categorization.classify_business_category()` — `core.py:775`
- `reit_subtype -> Optional[str]` (`cached_property`) — `'equity'` or `'mortgage'` based on `InterestIncomeExpenseNet` presence — `core.py:824`
- `is_fund() / is_financial_institution() / is_operating_company()` — convenience booleans from `business_category` — `core.py:859-904`
- `latest_tenk -> Optional[TenK]` / `latest_tenq -> Optional[TenQ]` (properties) — most recent unamended 10-K / 10-Q, no full-load trigger — `core.py:907/915`
- `proxy_season(index) -> Optional[ProxySeason]` — `core.py:922`
- `get_facts(period_type) -> Optional[EntityFacts]` — overrides Entity; injects a lazy SIC/ticker resolver (`_sic_resolver` closure) to avoid triggering submissions fetch at facts load time — `core.py:949`
- `facts -> Optional[EntityFacts]` (`cached_property`) — calls `get_facts()` — `core.py:972`
- `public_float -> Optional[float]` / `shares_outstanding -> Optional[float]` (properties) — delegate to `facts` — `core.py:983/991`
- `income_statement(periods, period, annual, as_dataframe, concise_format)` — delegates to `facts.income_statement()`, supports `'annual'/'quarterly'/'ttm'` — `core.py:998`
- `balance_sheet(periods, period, annual, as_dataframe, concise_format)` — raises `ValueError` if `period='ttm'` — `core.py:1044`
- `cashflow_statement(periods, period, annual, as_dataframe, concise_format)` — `core.py:1088`
- `cash_flow(**kwargs)` — deprecated alias for `cashflow_statement()`, emits `DeprecationWarning` — `core.py:1128`
- `list_concepts(search, statement, limit) -> ConceptList` — discovers XBRL concepts via `facts._facts` index — `core.py:1157`
- `get_ttm(concept, as_of) -> TTMMetric` — delegates to `facts.get_ttm()` — `core.py:1252`
- `get_ttm_revenue(as_of) / get_ttm_net_income(as_of) -> TTMMetric` — convenience wrappers — `core.py:1279/1298`
- `to_context(detail, max_tokens) -> str` — Markdown-KV LLM-optimized summary, three detail levels (`'minimal'`, `'standard'`, `'full'`) — `core.py:1339`
- `text(max_tokens)` — deprecated alias for `to_context()` — `core.py:1472`

#### `EntityData` (`edgar/entity/data.py:291`)
Container for parsed submissions JSON. Not normally instantiated directly; returned by `get_entity_submissions()`.

- `__init__(cik, name, tickers, exchanges, sic, sic_description, ein, entity_type, fiscal_year_end, filings, business_address, mailing_address, state_of_incorporation, **kwargs)` — accepts all extra fields via `**kwargs` and stores as attributes — `data.py:298`
- `_load_older_filings()` — lazily fetches additional paginated submissions files from SEC (`/submissions/CIK*.json` auxiliary files listed in `filings.files`) — `data.py:353`
- `get_filings(year, quarter, form, …, trigger_full_load) -> Optional[EntityFilings]` — full filter chain on the PyArrow table; calls `_load_older_filings()` on first full-load request — `data.py:384`
- `is_company -> bool` / `is_individual -> bool` (`cached_property`) — calls `_classify_is_individual()` with 9-signal priority chain — `data.py:476/481`
- `is_bdc -> bool` (`cached_property`) — checks for `814-` prefix in any `fileNumber` — `data.py:515`
- `_files` — list of auxiliary pagination file refs from `filings.files`; cleared after local merge — `data.py:351`
- `_loaded_all_filings: bool` — guards double-fetch — `data.py:350`

#### `CompanyData(EntityData)` (`edgar/entity/data.py:796`)
Adds `industry -> str` and `get_ticker() -> Optional[str]`. Otherwise delegates to `EntityData`.

#### `Address` (`edgar/entity/data.py:202`)
Uses `__slots__` for memory efficiency. Lazily caches `__str__` result in `_str_cache`. Fields: `street1`, `street2`, `city`, `state_or_country`, `zipcode`, `state_or_country_desc`. `.empty` property short-circuits on blank `street1`. `.to_json()` returns a plain dict.

#### `EntityFacts` (`edgar/entity/entity_facts.py:136`)
Central XBRL facts container. NOT a dataclass — plain Python class.

- `__init__(cik, name, facts: List[FinancialFact], sic_code, ticker)` — builds six in-memory indices immediately: `by_concept`, `by_period`, `by_statement`, `by_form`, `by_fiscal_year`, `by_fiscal_period` — `entity_facts.py:145`
- `_sic_resolver: Optional[Callable]` — lazy closure set by `Company.get_facts()` to avoid submissions fetch at load time — `entity_facts.py:163`
- `_resolve_industry_info()` — called once before statement building; triggers the `_sic_resolver` closure — `entity_facts.py:166`
- `get_all_facts() -> List[FinancialFact]` — `entity_facts.py:237`
- `to_dataframe(include_metadata, columns, pit_mode) -> pd.DataFrame` — export; `pit_mode=True` preserves all versions for point-in-time backtesting — `entity_facts.py:246`
- `filter_by_period_type(period_type) -> EntityFacts` — builds new instance with filtered facts via `FactQuery` — `entity_facts.py:345`
- `query() -> FactQuery` — returns a chainable query builder — `entity_facts.py:586`
- `get_fact(concept, period) -> Optional[FinancialFact]` — exact or case-insensitive label match; period format `"YYYY-QN"` or `"YYYY-FY"` (also accepts `"FY YYYY"` via `normalize_period_to_entity_facts`); returns most recent by `(filing_date, period_end)` — `entity_facts.py:600`
- `get_annual_fact(concept, fiscal_year) -> Optional[FinancialFact]` — filters to `fiscal_period == 'FY'` first — `entity_facts.py:653`
- `time_series(concept, periods) -> pd.DataFrame` — sorted DataFrame with `period_start`, `period_end`, `duration_days`, `numeric_value`, `fiscal_period`, `fiscal_year` — `entity_facts.py:714`
- `dei_facts(as_of) -> pd.DataFrame` — DEI taxonomy facts (entity name, trading symbol, shares, public float) — `entity_facts.py:755`
- `entity_info() -> Dict[str, Any]` — structured dict of common DEI facts — `entity_facts.py:814`
- `get_revenue(period, unit, annual) -> Optional[float]` — tries 5 revenue concept variants — `entity_facts.py:861`
- `get_net_income / get_total_assets / get_total_liabilities / get_shareholders_equity / get_operating_income / get_gross_profit` — same pattern, each with ordered synonym list — `entity_facts.py:897–1072`
- `get_concept(concept_name, period, unit, return_metadata) -> Optional[float]` — unified synonym lookup via `SynonymGroups` registry; 40+ canonical concepts — `entity_facts.py:1078`
- `discover_concept_tags(concept_name) -> List[str]` — which tags from a synonym group exist in this company's actual facts — `entity_facts.py:1178`
- `search_concepts(pattern) -> ConceptSearchResults` — regex search over concept names and labels — `entity_facts.py:1220`
- `available_periods(concept) -> PeriodSummary` — periods with data; sorted by year descending then FY>Q4>…>Q1 — `entity_facts.py:1282`
- `list_supported_concepts(category) -> List[str]` — all canonical names in `SynonymGroups`, not company-specific — `entity_facts.py:1339`
- `shares_outstanding -> Optional[float]` (property) — tries `dei:EntityCommonStockSharesOutstanding` then `us-gaap:CommonStockSharesOutstanding` — `entity_facts.py:1368`
- `public_float -> Optional[float]` (property) — `dei:EntityPublicFloat` — `entity_facts.py:1401`
- `get_ttm(concept, as_of) -> TTMMetric` — uses `TTMCalculator`; `as_of` accepts `date`, `"YYYY-MM-DD"`, or `"YYYY-QN"` — `entity_facts.py:1612`
- `get_ttm_revenue(as_of) / get_ttm_net_income(as_of)` — multi-concept TTM convenience — `entity_facts.py:1632/1647`
- `_ttm_ready_facts -> EntityFacts` (`cached_property`) — facts prepared for quarterly/TTM (split-adjusted + derived quarter facts) — `entity_facts.py:1657`
- `income_statement(periods, period, annual, as_dataframe, concise_format) -> MultiPeriodStatement | TTMStatement | DataFrame` — `period='ttm'` uses `TTMStatementBuilder`; `'quarterly'` uses `_ttm_ready_facts` — `entity_facts.py:1697`
- `balance_sheet(periods, as_of, period, annual, as_dataframe, concise_format)` — raises `ValueError` if `period='ttm'`; `as_of` triggers point-in-time snapshot path — `entity_facts.py:1759`
- `cashflow_statement(periods, period, annual, as_dataframe, concise_format)` — same TTM/quarterly handling as income_statement — `entity_facts.py:1867`
- `cash_flow(...)` — deprecated, emits `DeprecationWarning` — `entity_facts.py:1926`
- `to_llm_context(focus_areas, time_period) -> Dict[str, Any]` — structured LLM context with optional profitability/growth/liquidity analysis — `entity_facts.py:1986`
- `to_agent_tools() -> List[Dict]` — MCP-style tool definitions for AI agents — `entity_facts.py:2033`

#### `EntityFiling(Filing)` (`edgar/entity/filings.py:32`)
Extends base `Filing`. Extra attributes: `report_date`, `acceptance_datetime`, `file_number`, `items`, `size`, `primary_document`, `primary_doc_description`, `is_xbrl`, `is_inline_xbrl`.

- `related_filings()` — gets all filings sharing the same `file_number` — `filings.py:80`
- `parsed_items -> str` (property) — parses 8-K document text for item numbers; overrides unreliable SEC metadata for legacy filings — `filings.py:85`

#### `EntityFilings(Filings)` (`edgar/entity/filings.py:176`)
PyArrow-backed paginated collection.

- `__init__(data, cik, company_name, original_state)` — `filings.py:184`
- `get_filing_at(item) -> EntityFiling` — constructs `EntityFiling` from row — `filings.py:211`
- `filter(form, amendments, filing_date, date, cik, ticker, accession_number, file_number) -> EntityFilings` — extends parent `filter()` with `fileNumber` support — `filings.py:230`
- `latest(n) -> EntityFiling | EntityFilings | None` — sorts descending by `filing_date`, returns single if n=1, else slice — `filings.py:270`
- `head(n) / tail(n) / sample(n) -> EntityFilings` — `filings.py:293-330`
- `next() / previous() -> Optional[EntityFilings]` — pagination through large result sets — `filings.py:352/370`
- `to_context(detail) -> str` — LLM-optimized Markdown-KV with optional crowdfunding breakdown — `filings.py:443`
- `empty -> bool` (property) — `filings.py:208`
- `COMPANY_FILINGS_SCHEMA` — PyArrow schema with 13 columns: `accession_number`, `filing_date`, `reportDate`, `acceptanceDateTime`, `act`, `form`, `fileNumber`, `items`, `size`, `isXBRL`, `isInlineXBRL`, `primaryDocument`, `primaryDocDescription` — `filings.py:648`

There is also a legacy `EntityFacts` stub class inside `filings.py:612` (PyArrow table + fact_meta DataFrame) — this is the old format, NOT the main XBRL facts object. The canonical one is in `entity_facts.py`.

#### `EntityFactsParser` (`edgar/entity/parser.py:20`)
Converts raw SEC JSON to `EntityFacts`. Singleton class with classmethods.

- `parse_company_facts(json_data) -> Optional[EntityFacts]` — iterates all taxonomies → concepts → units → fact entries; uses `sys.intern` + local cache for string deduplication across ~24K facts per company; hoists per-concept work (statement_type, semantic_tags, structural_info, business_context) out of the per-fact loop — `parser.py:41`
- `_parse_single_fact(...)` — maps `val`, `end`/`start`, `filed`, `fy`, `fp`, `form`, `accn` to `FinancialFact`; sets `is_audited=True` when `fiscal_period == 'FY'` — `parser.py:145`
- `_determine_statement_type(concept)` — calls `get_primary_statement()` from `mappings_loader` — `parser.py:287`
- `_get_structural_info(concept)` — loads `learned_mappings.json` for depth, parent, section, is_abstract, is_total — `parser.py:317`
- `_assess_data_quality(fact_data, fiscal_period)` — `DataQuality.HIGH` for `FY` facts — `parser.py:344`

#### `CompanySearchIndex(FastSearch)` (`edgar/entity/search.py:69`)
Wraps `get_company_tickers()` with `FastSearch` fuzzy scorer. Cached via `_get_company_search_index()` (`@lru_cache(maxsize=1)`). `search(query, top_n, threshold) -> CompanySearchResults`.

`CompanySearchResults` (`edgar/entity/search.py:24`) holds results DataFrame and allows `results[i]` → `Company(cik)` direct construction.

---

### Class hierarchy

```
SecFiler (ABC)  edgar/entity/core.py:203
├── Entity       edgar/entity/core.py:234
│   └── Company  edgar/entity/core.py:570
└── (Fund/FundCompany — edgar/funds, not in this scope)

EntityData       edgar/entity/data.py:291
└── CompanyData  edgar/entity/data.py:796

Filings (edgar._filings)
└── EntityFilings  edgar/entity/filings.py:176

Filing (edgar._filings)
└── EntityFiling  edgar/entity/filings.py:32

FastSearch (edgar.search.datasearch)
└── CompanySearchIndex  edgar/entity/search.py:69

EntityFacts      edgar/entity/entity_facts.py:136   (standalone, composition of FinancialFact list)
FinancialFact    edgar/entity/models.py:21           (slots dataclass)

# Aliases (backward compatibility)
CompanyFiling  = EntityFiling    (filings.py:680)
CompanyFilings = EntityFilings   (filings.py:681)
CompanyFacts   = EntityFacts     (filings.py:682)
```

---

### Configuration & options

| Option | Type | Default | Effect |
|--------|------|---------|--------|
| `trigger_full_load` | `bool` | `True` | `get_filings()` / `EntityData.get_filings()` — fetches all paginated submissions files |
| `amendments` | `bool` | `True` | Include amended forms in `get_filings()` |
| `period` | `str` | `'annual'` | `income_statement()`, `cashflow_statement()`: `'annual'`, `'quarterly'`, or `'ttm'` |
| `periods` | `int` | `4` | Number of periods in statement methods |
| `as_dataframe` | `bool` | `False` | Return `pd.DataFrame` instead of `MultiPeriodStatement` |
| `concise_format` | `bool` | `False` | Format values as `$1.0B` instead of `$1,000,000,000` |
| `annual` | `bool` | `None` | Legacy override for `period`; `True`→`'annual'`, `False`→`'quarterly'` |
| `pit_mode` | `bool` | `False` | `to_dataframe()`: include filing_date/form_type, preserve all versions |
| `include_metadata` | `bool` | `False` | `to_dataframe()`: add accession, quality, audit cols |
| `_COMPANY_FACTS_CACHE_MAXSIZE` | `int` | `1` | Max entries in `_company_facts_cache` (LRU OrderedDict) |
| `entity_type` param | `str` | `'auto'` | `create_entity_from_submissions_json()`: `'company'`, `'fund'`, `'entity'` |
| `EDGAR_USE_LOCAL_DATA` | env var | — | When set, reads submissions and companyfacts from local `~/.edgar/` directory |
| `detail` | `str` | `'standard'` | `to_context()`: `'minimal'`, `'standard'`, `'full'` |
| `max_filings` | `int` | `50` | `has_company_filings()`: how many forms to scan in the PyArrow array |

---

### Data flow / lifecycle

**Ticker/CIK resolution (construction time):**
- `Company("AAPL")` → `Entity.__init__()` → detects non-numeric string → calls `find_cik("AAPL")` from `edgar.reference.tickers` → checks `get_cik_tickers()` (bundled parquet → local → SEC live) → returns int CIK → stored as `self._cik`
- CIK as string/int → `normalize_cik()` strips leading zeros

**Entity metadata load (lazy):**
- First access to `entity.data` or `entity.name` triggers `cached_property data`
- Calls `get_entity_submissions(cik)` → checks `EDGAR_USE_LOCAL_DATA`:
  - If local: `load_company_submissions_from_local()` reads `~/.edgar/submissions/CIK*.json`; calls `_merge_additional_local_filings()` to inline pagination files and clear `filings.files`
  - Otherwise: `download_entity_submissions_from_sec()` → `download_json(build_submissions_url(cik))` (30-second TTL via `HttpxThrottleCache`)
- `parse_entity_submissions(cjson)` → `CompanyData(...)` with embedded `EntityFilings` from `create_company_filings()` (only `filings.recent` initially)
- On 404: creates `create_default_entity_data(cik)` placeholder with `_not_found = True`

**Filings lazy-load:**
- `EntityData._files` holds the list of auxiliary paginated file refs from `cjson['filings']['files']`
- First call to `get_filings(trigger_full_load=True)` (the default) triggers `_load_older_filings()`: downloads each file, extends the PyArrow table, sets `_loaded_all_filings = True`
- Local storage path skips network by merging local pagination files at construction time (clearing `_files`) — so `_load_older_filings()` is a no-op

**Facts load:**
- `company.get_facts()` or `company.facts` → `get_company_facts(cik)`:
  - Checks `_company_facts_cache` (LRU, maxsize=1)
  - If local: `load_company_facts_from_local()` reads `~/.edgar/companyfacts/CIK*.json` via `orjson`
  - Otherwise: `download_company_facts_from_sec()` → HTTP GET
  - `EntityFactsParser.parse_company_facts()` builds `List[FinancialFact]` with string interning
  - Result stored in `_company_facts_cache[cik]`; oldest entry evicted when size > 1
- `Company.get_facts()` additionally attaches a `_sic_resolver` closure (not called until statement-building time) to inject SIC/ticker without triggering a second submissions fetch

**Statement building:**
- `income_statement(period='annual')` → `_build_enhanced_statement()` → `_resolve_industry_info()` (calls the closure) → `EnhancedStatementBuilder.build_multi_period_statement()`
- `period='quarterly'` → uses `_ttm_ready_facts` (cached) which applies `_prepare_quarterly_facts()`: split-adjustment + TTM quarterlization
- `period='ttm'` → `TTMStatementBuilder`

**Period key formats:**
- `EntityFacts` internal: `"2023-FY"`, `"2024-Q3"`
- `MultiPeriodStatement` display: `"FY 2023"`, `"Q3 2024"`
- `normalize_period_to_entity_facts()` / `normalize_period_to_statement()` convert between them (`utils.py:19/29`)

---

### Design patterns

- **Lazy property / cached_property**: `Entity.data`, `Entity.filer_category`, `Company.business_category`, `Company.filer_type`, `Company.facts`, `EntityData.is_individual`, `EntityData.is_bdc`, `EntityFacts._ttm_ready_facts` — avoids network calls until data is actually needed.
- **Deferred SIC resolution (closure)**: `Company.get_facts()` stores a `lambda: (company.sic, company.tickers[0])` as `facts._sic_resolver`; the closure is invoked only when building a statement, not on facts access. This prevents a submissions-fetch chain when the caller only needs raw facts or shares_outstanding.
- **LRU in-memory cache (size=1)**: `_company_facts_cache` is an `OrderedDict` used as a manual LRU. The small maxsize (1) is intentional — each company's facts can be 40–80 MB. `clear_company_facts_cache()` is the public API for flushing it.
- **String interning in parser**: `sys.intern` + `_intern_cache` dict during `EntityFactsParser.parse_company_facts()` deduplicates ~1000 repeating strings (taxonomy, concept, unit, fiscal_period, form_type) across 20K+ facts per company, saving significant memory.
- **PyArrow for filings table**: Column-oriented storage enables O(1) filter operations across thousands of filings without materializing Python objects. Rows are only converted to `EntityFiling` objects on demand via `get_filing_at(i)`.
- **9-signal priority chain for entity classification**: `_classify_is_individual()` in `constants.py:226` uses an ordered priority chain (issuer flag → tickers → state of incorporation → entity_type → company forms → EIN → name keywords → owner flag → default). Hard-coded exceptions for Warren Buffett (CIK 315090) and Reed Hastings (CIK 1033331).
- **Factory functions over constructors**: `get_entity()`, `get_company()`, `get_company_facts()` are the preferred entry points; direct construction of `Entity`/`Company` is also supported.
- **Graceful degradation**: 404 from submissions → synthetic placeholder entity (`create_default_entity_data`), not exception. 404 from company-facts → `NoCompanyFactsFound` raised inside `get_company_facts()`, caught in `Entity.get_facts()` → returns `None`.

---

### Cross-domain interactions

**Imports from other `edgar.*` modules:**
- `edgar.httprequests` — `download_json`, `download_text` (HTTP layer with throttling/caching)
- `edgar.reference.tickers` — `find_cik`, `find_ticker`, `get_company_tickers`, `get_cik_tickers` (reference data)
- `edgar.storage` — `get_edgar_data_directory()`, `is_using_local_storage()` (local storage flags)
- `edgar.financials` — `Financials` (Company.get_financials() return type)
- `edgar.company_reports` — `TenK`, `TenQ` (Company.latest_tenk/tenq)
- `edgar._filings` — `Filing`, `Filings`, `PagingState` (base classes)
- `edgar.filtering` — `filter_by_date`, `filter_by_form`, `filter_by_year_quarter`
- `edgar.ttm.calculator` — `TTMCalculator`, `TTMMetric`
- `edgar.ttm.statement` — `TTMStatement`, `TTMStatementBuilder`
- `edgar.ttm.splits` — `detect_splits`, `apply_split_adjustments`
- `edgar.entity.enhanced_statement` — `EnhancedStatementBuilder`, `MultiPeriodStatement`
- `edgar.entity.statement_builder` — `StatementBuilder` (structured statement path)
- `edgar.entity.query` — `FactQuery` (query builder for EntityFacts)
- `edgar.entity.mappings_loader` — `load_learned_mappings`, `get_primary_statement`
- `edgar.standardization` — `get_synonym_groups` (SynonymGroups registry for `get_concept()`)
- `edgar.search.datasearch` — `FastSearch` (underlying search engine for CompanySearchIndex)
- `edgar.proxy.season` — `ProxySeason` (Company.proxy_season())
- `edgar.enums` — `FilerCategory`, `FormType`, `PeriodType`
- `edgar.funds` — `FundCompany`, `FundData`, `FundSeries` (re-exported from `__init__`)

**Modules that import from `edgar.entity`:**
- `edgar.financials` — uses `Company`, `Entity`
- `edgar.xbrl` — accesses filings from `EntityFilings`
- `edgar.funds` — `FundCompany` extends entity patterns
- `edgar.proxy` — `ProxySeason.for_company()` takes a `Company`
- Top-level `edgar/__init__.py` — re-exports `Company`, `Entity`, `get_entity`, `get_company`, `find_company`

---

### Gotchas & notable behaviors

**Facts cache is maxsize=1.** Loading facts for company B evicts company A. In loops over multiple companies, call `clear_company_facts_cache()` or batch carefully. Each set of facts can be 40–80 MB.

**Annual vs quarterly facts both can carry `fiscal_period='FY'`.** The SEC Facts API issues this inconsistently. The `EnhancedStatementBuilder` applies duration-based filtering (annual: 300+ days) to distinguish true annuals from quarterly data mistakenly marked FY. Do NOT rely solely on `fiscal_period` for period classification (see CLAUDE.md bug #408).

**`get_fact()` returns most recent by `(filing_date, period_end)`.** If the same concept is in multiple comparative filings, the latest filing wins. This is the preferred fact but not necessarily the first-filed value.

**Submissions pagination is transparent but lazy.** Initial load only includes `filings.recent` (~1000 most recent filings). Historical filings require `get_filings(trigger_full_load=True)` (the default). Using `trigger_full_load=False` skips this for performance (used by `latest_tenk`, `filer_type`).

**Local storage bypasses the network entirely.** When `EDGAR_USE_LOCAL_DATA` is set, `_merge_additional_local_filings()` inlines all pagination files at construction time and clears `_files`, so subsequent `_load_older_filings()` calls are no-ops.

**`Company.__bool__` returns `False` for CIKs that 404.** A valid `Company` object can evaluate to falsy if the CIK exists syntactically but returns no submissions data. Pattern: `company = Company(cik); if company: ...`

**`CompanyNotFoundError` includes fuzzy suggestions.** When `Company("APPL")` fails, the error message lists up to 3 similar tickers from the `CompanySearchIndex`. Suggestions come from `_get_suggestions()` with fuzzy threshold 40.

**`get_company_facts()` returns `None` (not raises) if the JSON payload is empty.** A `NoCompanyFactsFound` is raised on HTTP 404, but an empty JSON response produces a `warnings.warn` and returns `None`. `Entity.get_facts()` catches `NoCompanyFactsFound` and also returns `None`, so callers always see `None` on failure.

**Period format duality.** `EntityFacts` internal keys use `"2024-Q3"` format; `MultiPeriodStatement` column headers use `"Q3 2024"`. Both formats are accepted by `get_fact(concept, period=...)` via `normalize_period_to_entity_facts()`.

**`is_individual` classification has hard-coded CIK exceptions.** CIK 315090 (Warren Buffett) and 1033331 (Reed Hastings) are forced to `True` (individual) despite having EIN or state_of_incorporation, because they would otherwise be misclassified as companies.

**`filer_type` check order matters.** `Company.filer_type` checks `40-F` before `20-F`/`6-K` because Canadian filers also file `6-K`; without the 40-F guard, all Canadian filers would return `'Foreign'`.

**`_ttm_ready_facts` is cached as a property on `EntityFacts`.** The first quarterly or TTM statement build triggers split detection + quarterly derivation for all concepts, then caches the expanded fact list. Subsequent builds reuse the cache, but the initial build can be slow for large companies.

**`CompanyFacts = EntityFacts` in `filings.py`** is a legacy stub class (PyArrow table, not the main XBRL object). The real `EntityFacts` is in `entity_facts.py`. They share the same exported name; imports from `edgar.entity` will get the correct one from `entity_facts.py` via `__init__.py`.

**`create_entity_from_submissions_json()` sets `_loaded_all_filings = True`** so test entities do not trigger network calls for paginated filings.
