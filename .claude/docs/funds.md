## Funds & Investment Products

### Overview

The `edgar/funds/` package models the SEC's three-level investment company hierarchy (Company → Series → Class) and provides typed data objects for every major fund-specific filing type. It is the authoritative domain for mutual funds, ETFs, and money market funds within EdgarTools: entity resolution (ticker/series/class to CIK), portfolio holdings (N-PORT), money market reporting (N-MFP2/N-MFP3), annual census (N-CEN), shareholder reports (N-CSR/N-CSRS), summary prospectuses (497K), and annual fee notices (24F-2NT). All objects integrate with `filing.obj()` via the central dispatch in `edgar/__init__.py`.

---

### Public API Surface

| Symbol | file:line | Purpose |
|---|---|---|
| `Fund` | `edgar/funds/core.py:335` | Unified wrapper — accepts any identifier (ticker, series ID, class ID, CIK) |
| `FundCompany` | `edgar/funds/core.py:31` | Legal entity filing with SEC; extends `Entity` |
| `FundSeries` | `edgar/funds/core.py:149` | A specific investment product/strategy under a company |
| `FundClass` | `edgar/funds/core.py:91` | A share class with its own ticker, belonging to a series |
| `find_fund(identifier)` | `edgar/funds/core.py:217` | Smart factory: returns FundClass, FundSeries, or FundCompany |
| `find_funds(name, search_type)` | `edgar/funds/core.py:319` | Name-fragment search across companies/series/classes |
| `get_fund_company(cik_or_id)` | `edgar/funds/core.py:253` | Construct FundCompany by CIK |
| `get_fund_series(series_id)` | `edgar/funds/core.py:266` | Construct FundSeries by S-ID |
| `get_fund_class(class_id_or_ticker)` | `edgar/funds/core.py:285` | Construct FundClass by C-ID or ticker |
| `FundReport` | `edgar/funds/reports.py:458` | N-PORT-P portfolio holdings object |
| `get_fund_portfolio_from_filing(filing)` | `edgar/funds/reports.py:1641` | Convenience: filing → portfolio DataFrame |
| `NPORT_FORMS` | `edgar/funds/reports.py:88` | `["NPORT-P", "NPORT-EX", "N-PORT", "N-PORT/A"]` |
| `MoneyMarketFund` | `edgar/funds/nmfp3.py:152` | N-MFP2 / N-MFP3 portfolio + yield/NAV/liquidity data |
| `MONEY_MARKET_FORMS` | `edgar/funds/nmfp3.py:32` | `NMFP2_FORMS + NMFP3_FORMS` |
| `NMFP2_FORMS` | `edgar/funds/nmfp3.py:30` | `["N-MFP2", "N-MFP2/A"]` |
| `NMFP3_FORMS` | `edgar/funds/nmfp3.py:31` | `["N-MFP3", "N-MFP3/A"]` |
| `FundCensus` | `edgar/funds/ncen.py:237` | N-CEN annual census object |
| `NCEN_FORMS` | `edgar/funds/ncen.py:31` | `["N-CEN", "N-CEN/A"]` |
| `FundShareholderReport` | `edgar/funds/ncsr.py:71` | N-CSR / N-CSRS certified shareholder report |
| `NCSR_FORMS` | `edgar/funds/ncsr.py:30` | `["N-CSR", "N-CSR/A", "N-CSRS", "N-CSRS/A"]` |
| `Prospectus497K` | `edgar/funds/prospectus497k.py:144` | 497K summary prospectus (HTML-parsed) |
| `PROSPECTUS497K_FORMS` | `edgar/funds/prospectus497k.py:32` | `["497K"]` |
| `FundFeeNotice` | `edgar/funds/twentyfourf.py:124` | 24F-2NT annual notice of securities sold |
| `FundData` | `edgar/funds/data.py:749` | Fund-specific EntityData subclass |
| `FundReferenceData` | `edgar/funds/reference.py:47` | Normalized in-memory index of SEC bulk fund CSV |
| `get_fund_reference_data()` | `edgar/funds/reference.py:521` | `@lru_cache(1)` — returns `FundReferenceData` |
| `resolve_fund_identifier(identifier)` | `edgar/funds/data.py:767` | Converts ticker/series/class ID to CIK int |
| `is_fund_ticker(identifier)` | `edgar/funds/data.py:731` | O(1) frozenset check against mf_tickers |
| `TickerSeriesResolver` | `edgar/funds/series_resolution.py:26` | Ticker → series ID resolution with ETF fallback |
| `TickerResolutionService` | `edgar/funds/ticker_resolution.py:45` | Holding-level ticker resolution (CUSIP→ticker) |

---

### Key Classes

#### `Fund` — `edgar/funds/core.py:335`

Unified user-facing wrapper. Resolves any identifier to the full hierarchy at construction time.

- `__init__(identifier: Union[str, int])` — Runs `TickerSeriesResolver.get_primary_series()` for tickers, then `find_fund()`; populates `_company`, `_series`, `_class` — `core.py:359`
- `company -> Optional[FundCompany]` — The parent legal entity — `core.py:399`
- `series -> Optional[FundSeries]` — The specific series — `core.py:404`
- `share_class -> Optional[FundClass]` — The specific share class — `core.py:409`
- `ticker -> Optional[str]` — Share class ticker if resolved — `core.py:431`
- `identifier -> str` — Primary ID of the innermost entity — `core.py:420`
- `get_filings(series_only=False, **kwargs) -> Filings` — Optional EFTS path for series-scoped search (max 100 results); falls back to entity's get_filings — `core.py:437`
- `get_series() -> Optional[FundSeries]` — Returns the specific series; handles synthetic `ETF_<CIK>` IDs — `core.py:482`
- `get_portfolio() -> Optional[pd.DataFrame]` — Chains: latest NPORT-P → FundReport → investment_data() — `core.py:576`
- `get_latest_report(form='NPORT-P') -> Optional[Any]` — Gets filings, returns `filings[0].obj()` — `core.py:564`
- `list_series() -> List[FundSeries]` — All series under the company — `core.py:586`
- `list_classes() -> List[FundClass]` — All share classes under the series — `core.py:606`
- `get_resolution_diagnostics() -> Dict` — Returns resolution method, status, suggestions — `core.py:520`

#### `FundCompany` — `edgar/funds/core.py:31`

Extends `edgar.entity.core.Entity`. Wraps the legal fund filer.

- `__init__(cik_or_identifier, fund_name=None, all_series=None)` — Calls `resolve_fund_identifier()` before `super().__init__()` — `core.py:39`
- `list_series() -> Optional[List[FundSeries]]` — Returns `self.all_series` — `core.py:58`
- `name -> str` — Returns `_name` or delegates to `Entity.name` — `core.py:53`

#### `FundSeries` — `edgar/funds/core.py:149`

Standalone (not an Entity subclass). Holds a list of `FundClass` instances.

- `__init__(series_id, name, fund_classes=None, fund_company=None)` — `core.py:152`
- `get_classes() -> List[FundClass]` — Returns `self.fund_classes` — `core.py:160`
- `get_filings(**kwargs) -> Filings` — Delegates to `fund_company.get_filings()` — `core.py:169`

#### `FundClass` — `edgar/funds/core.py:91`

Lowest level of the hierarchy. Carries `ticker`, `class_id`, `series` backref.

- `get_classes() -> List[FundClass]` — Fetches all classes in the same series via `get_fund_object(series_id)` — `core.py:111`

#### `FundReport` (N-PORT) — `edgar/funds/reports.py:458`

The most feature-rich filing object. Parses `NPORT-P` / `NPORT-EX` XML using lxml (10-20x faster than BeautifulSoup).

- `from_filing(cls, filing) -> FundReport` — Calls `filing.xml()` → `parse_fund_xml()` → attaches `_filing` — `reports.py:1213`
- `parse_fund_xml(cls, xml) -> Dict` — Static lxml parser; strips namespaces, walks edgarSubmission tree — `reports.py:1224`
- `investment_data(include_derivatives=True, include_ticker_metadata=False) -> pd.DataFrame` — Main holdings DataFrame; cached by `(include_derivatives, include_ticker_metadata)` tuple; sorted by `abs(value_usd)` — `reports.py:543`
- `securities_data() -> pd.DataFrame` — Alias for `investment_data(include_derivatives=False)` — `reports.py:625`
- `derivatives_data() -> pd.DataFrame` — Only derivative positions; cached — `reports.py:777`
- `swaps_data() -> pd.DataFrame` — Detailed swap data with full receive/pay leg columns — `reports.py:810`
- `swaptions_data() -> pd.DataFrame` — Swaptions with nested swap detail — `reports.py:887`
- `options_data() -> pd.DataFrame` — Options with nested forward/future/swap columns — `reports.py:962`
- `forwards_data() -> pd.DataFrame` — FX forwards with currency/amount columns — `reports.py:1097`
- `futures_data() -> pd.DataFrame` — Futures with reference entity columns — `reports.py:1125`
- `get_fund_series() -> FundSeries` — Constructs a FundSeries from general_info — `reports.py:488`
- `get_tickers_for_series() -> List[str]` — Looks up all tickers for this series from `get_mutual_fund_tickers()` — `reports.py:494`
- `to_context(detail='standard') -> str` — AI-optimized string; detail levels: 'minimal'/'standard'/'full' — `reports.py:1538`
- Key attributes: `header` (Header), `general_info` (GeneralInfo), `fund_info` (FundInfo), `investments` (List[InvestmentOrSecurity])

**investment_data() columns:** `name, title, lei, cusip, ticker, isin, balance, units, desc_other_units, value_usd, pct_value, payoff_profile, asset_category, issuer_category, currency_code, investment_country, restricted, is_derivative, maturity_date, annualized_rate, is_default, cash_collateral, non_cash_collateral, derivative_type, notional_amount, counterparty`

#### `InvestmentOrSecurity` — `edgar/funds/reports.py:333`

Pydantic model for each N-PORT holding line.

- `ticker -> Optional[str]` — Calls `TickerResolutionService.resolve_ticker()` — `reports.py:359`
- `ticker_resolution_info -> TickerResolutionResult` — Full resolution metadata — `reports.py:365`
- `is_derivative -> bool` — `derivative_info is not None` — `reports.py:381`
- `derivative_type -> Optional[str]` — FWD/SWP/FUT/OPT/SWO — `reports.py:392`
- `derivative_subtype -> Optional[str]` — Human-readable (e.g., "Credit Default Swap", "FX Forward") — `reports.py:397`

#### `MoneyMarketFund` (N-MFP2/N-MFP3) — `edgar/funds/nmfp3.py:152`

Supports both N-MFP3 (June 2024+, daily time series) and N-MFP2 (2010–mid 2024, Friday snapshots).

- `from_filing(cls, filing) -> Optional[MoneyMarketFund]` — Calls `filing.xml()` → `_parse_xml()`; detects schema via `b'edgar/nmfp2' in xml_bytes` — `nmfp3.py:501`
- `portfolio_data() -> pd.DataFrame` — Holdings sorted by market_value desc; cached — `nmfp3.py:244`
- `share_class_data() -> pd.DataFrame` — Per-class NAV/shares/min investment; cached — `nmfp3.py:272`
- `yield_history() -> pd.DataFrame` — Series-level 7-day gross yield time series; cached — `nmfp3.py:288`
- `nav_history() -> pd.DataFrame` — Daily NAV per share time series; cached — `nmfp3.py:295`
- `liquidity_history() -> pd.DataFrame` — Daily/weekly liquid asset % time series; cached — `nmfp3.py:302`
- `collateral_data() -> pd.DataFrame` — All repo collateral flattened; cached — `nmfp3.py:309`
- `holdings_by_category() -> pd.DataFrame` — Grouped by investment_category; cached — `nmfp3.py:332`
- Key properties: `net_assets`, `fund_category`, `average_maturity_wam`, `average_maturity_wal`, `num_securities`, `num_share_classes`, `series_id`, `cik`

**N-MFP3 vs N-MFP2 differences:**
- N-MFP3: daily time series with dates (20 entries); `registrantFullName`, `nameOfSeries` present
- N-MFP2: Friday-based weekly snapshots (fridayWeek1–5); uses `otherUniqueId` when `CUSIPMember` absent; `couponOrYield` instead of `coupon` in collateral
- N-MFP2 lacks registrant/series name in `generalInfo`

#### `FundCensus` (N-CEN) — `edgar/funds/ncen.py:237`

Annual census with operational data across series.

- `from_filing(cls, filing) -> Optional[FundCensus]` — `filing.xml()` → `_parse_xml()` — `ncen.py:566`
- `series_data() -> pd.DataFrame` — Series overview (name, type, avg_net_assets, has_etf); cached — `ncen.py:321`
- `service_providers() -> pd.DataFrame` — All advisers/custodians/transfer agents/admins/pricing across series; cached — `ncen.py:341`
- `broker_data() -> pd.DataFrame` — Broker-dealer and broker commissions; cached — `ncen.py:360`
- `director_data() -> pd.DataFrame` — Board directors with CRD numbers; cached — `ncen.py:387`
- `etf_data() -> pd.DataFrame` — ETF-specific data (exchange, ticker, creation unit, in-kind %, APs); cached — `ncen.py:401`
- Key properties: `name`, `cik`, `lei`, `report_date`, `num_series`, `total_series`, `classification_type`, `is_etf_company`, `series_ids`

**ETF handling:** `exchangeSeriesInfo`/`exchangeTradedFund` elements are parsed separately and merged into matching management series by `series_id` — `ncen.py:614`

#### `FundShareholderReport` (N-CSR/N-CSRS) — `edgar/funds/ncsr.py:71`

Uses Inline XBRL (`oef:` taxonomy) via `filing.xbrl()`, not raw XML.

- `from_filing(cls, filing) -> Optional[FundShareholderReport]` — Calls `filing.xbrl()`, determines "Annual" vs "Semi-Annual" from "CSRS" in form name — `ncsr.py:343`
- `performance_data() -> pd.DataFrame` — Annual returns per class/period; cached — `ncsr.py:155`
- `expense_data() -> pd.DataFrame` — Expense ratios, expenses paid, advisory fees; cached — `ncsr.py:172`
- `holdings_data() -> pd.DataFrame` — Top holdings % NAV; cached — `ncsr.py:188`
- Key properties: `fund_name`, `report_type` ('Annual'/'Semi-Annual'), `net_assets`, `portfolio_turnover`, `num_share_classes`, `cik`, `series_id`
- XBRL fact queries use `oef:ClassAxis` dimension to discover share classes; falls back to undimensioned facts for single-class funds — `ncsr.py:451`

#### `Prospectus497K` (497K) — `edgar/funds/prospectus497k.py:144`

No XBRL in 497K filings. All data from HTML table parsing per N-1A mandated structure.

- `from_filing(cls, filing) -> Optional[Prospectus497K]` — `filing.html()` → `_extract_header_data()` (SGML) + `extract_fee_tables()` + `extract_performance_table()` + `extract_fund_metadata()` — `prospectus497k.py:547`
- `fees -> pd.DataFrame` — Fee table per class (management_fee, 12b-1, other, total, waiver, net); cached property — `prospectus497k.py:271`
- `expense_example -> pd.DataFrame` — $10K hypothetical expense at 1/3/5/10yr; cached property — `prospectus497k.py:291`
- `performance -> pd.DataFrame` — Average annual returns; cached property — `prospectus497k.py:308`
- `tickers -> List[str]` — All share class tickers — `prospectus497k.py:231`
- `series_id -> Optional[str]` — From SGML header — `prospectus497k.py:235`
- `class_ids -> List[str]` — C000xxxxx IDs from SGML header — `prospectus497k.py:240`
- `best_quarter -> Optional[Tuple[Decimal, str]]` — (pct, date_str) — `prospectus497k.py:257`
- `worst_quarter -> Optional[Tuple[Decimal, str]]` — (pct, date_str) — `prospectus497k.py:261`

#### `FundFeeNotice` (24F-2NT) — `edgar/funds/twentyfourf.py:124`

Extends `XmlFiling` (not a standalone parsed class like others). Uses `_form_data` from the parent.

- `from_filing()` — Inherited from `XmlFiling` — `xmlfiling.py`
- `aggregate_sales -> Optional[float]` — Summed across all `annualFilingInfo` blocks — `twentyfourf.py:284`
- `net_sales -> Optional[float]` — Same — `twentyfourf.py:305`
- `registration_fee -> Optional[float]` — Same — `twentyfourf.py:324`
- `series -> List[SeriesInfo]` — Cached; deduplicates by series_id across blocks — `twentyfourf.py:199`
- `class_fees -> List[FundClassFee]` — Cached; per-class breakdown (empty for fund-level filings) — `twentyfourf.py:353`
- `is_per_class -> bool` — True when len(blocks) > 1 — `twentyfourf.py:175`
- `fiscal_year_end -> Optional[str]` — From item4 — `twentyfourf.py:245`

**Two filing patterns:**
- Fund-level (~98%): one `annualFilingInfo` block, aggregate values in item5
- Per-class (~2%): N blocks, one per share class; typed properties sum across blocks

#### `FundReferenceData` — `edgar/funds/reference.py:47`

In-memory normalized index loaded from SEC bulk investment company CSV.

- `get_company(cik) -> Optional[FundCompanyRecord]` — CIK zero-padded to 10 digits — `reference.py:207`
- `get_series(series_id) -> Optional[FundSeriesRecord]` — Direct dict lookup — `reference.py:221`
- `get_class(class_id) -> Optional[FundClassRecord]` — Direct dict lookup — `reference.py:233`
- `get_class_by_ticker(ticker) -> Optional[FundClassRecord]` — Via `_ticker_to_class` index — `reference.py:245`
- `get_series_for_company(cik) -> List[FundSeriesRecord]` — Via `_series_by_company` set — `reference.py:260`
- `get_classes_for_series(series_id) -> List[FundClassRecord]` — Via `_classes_by_series` set — `reference.py:274`
- `get_hierarchical_info(identifier) -> Tuple[company, series, class]` — All-in-one resolve — `reference.py:357`
- `find_by_name(name_fragment, search_type='company') -> List` — Case-insensitive substring; search_type: 'company'/'series'/'class' — `reference.py:287`
- `to_dataframe() -> pd.DataFrame` — Reconstructs flat DataFrame — `reference.py:405`

#### `TickerSeriesResolver` — `edgar/funds/series_resolution.py:26`

- `resolve_ticker_to_series(ticker) -> List[SeriesInfo]` — `@lru_cache(128)`; tries `get_mutual_fund_tickers()` first; falls back to `get_company_tickers()` for ETFs, creating synthetic `SeriesInfo(series_id="ETF_<CIK>")` — `series_resolution.py:31`
- `get_primary_series(ticker) -> Optional[str]` — Returns `series_list[0].series_id` — `series_resolution.py:92`
- `has_multiple_series(ticker) -> bool` — True if ticker maps to >1 series — `series_resolution.py:107`

#### `TickerResolutionService` — `edgar/funds/ticker_resolution.py:45`

For resolving tickers on individual N-PORT holdings.

- `resolve_ticker(ticker=None, cusip=None, isin=None, company_name=None) -> TickerResolutionResult` — `@lru_cache(128)` — `ticker_resolution.py:57`
- Resolution chain: direct ticker (confidence 1.0) → CUSIP lookup via `get_ticker_from_cusip()` (confidence 0.85) → failed (0.0)
- ISIN and name-based resolution are defined as future work (not yet implemented)

#### Derivative Models — `edgar/funds/models/derivatives.py`

All Pydantic models for N-PORT derivative instruments:

- `DerivativeInfo` — Top-level container; `derivative_category` is FWD/SWP/FUT/OPT/SWO/WAR — `derivatives.py:560`
- `ForwardDerivative` — FX forwards; currency_sold/purchased, amounts, settlement_date, unrealized_appreciation; plus `deriv_addl_*` fields from `derivAddlInfo` — `derivatives.py:119`
- `SwapDerivative` — Swaps (IRS, CDS, TRS); full receive/pay leg detail (fixed rate, floating index/spread/tenor); reference entity for CDS — `derivatives.py:178`
- `FutureDerivative` — Futures; reference entity with CUSIP/ISIN/ticker; payoff_profile, expiration, notional — `derivatives.py:374`
- `OptionDerivative` — Options; supports nested forward/future/swap; index basket reference for index options — `derivatives.py:470`
- `SwaptionDerivative` — Swaptions (derivCat="SWO"); put_or_call, exercise_price, nested_swap — `derivatives.py:425`

---

### Class Hierarchy

```
Entity (edgar.entity.core)
└── FundCompany
        └── .all_series: List[FundSeries]
                └── .fund_classes: List[FundClass]
                        └── .series -> FundSeries (backref)

Fund  (NOT a subclass — wraps whichever entity was resolved)
├── ._entity: Union[FundCompany, FundSeries, FundClass]
├── ._company: Optional[FundCompany]
├── ._series: Optional[FundSeries]
└── ._class: Optional[FundClass]

XmlFiling (edgar.xmlfiling)
└── FundFeeNotice

BaseModel (pydantic)
├── Header, GeneralInfo, FundInfo, InvestmentOrSecurity
├── DebtSecurity, SecurityLending, Identifiers
├── MonthlyTotalReturn, RealizedChange, MonthlyFlow, ReturnInfo
├── CurrentMetric, PeriodType
├── SeriesClassInfo, FilerInfo, IssuerCredentials
├── ForwardDerivative, SwapDerivative, FutureDerivative
├── OptionDerivative, SwaptionDerivative, DerivativeInfo
├── PortfolioSecurity, ShareClassInfo (nmfp3), CreditRating
├── CollateralIssuer, RepurchaseAgreement, SeriesLevelInfo
├── Director, Accountant, ServiceProvider, BrokerDealer
├── FundSeriesInfo, RegistrantInfo, ETFInfo, AuthorizedParticipant
├── AnnualReturn, Holding, ShareClassInfo (ncsr)
└── SeriesInfo (24F-2NT), ShareClassFees, PerformanceReturn

dataclass
├── FundCompanyRecord, FundSeriesRecord, FundClassRecord (reference.py)
├── SeriesInfo (series_resolution.py)
├── TickerResolutionResult
└── FundClassFee (frozen, twentyfourf.py)

Standalone (non-pydantic)
├── FundReport
├── MoneyMarketFund
├── FundCensus
├── FundShareholderReport
├── Prospectus497K
└── FundReferenceData
```

---

### Configuration & Options

| Option | Type | Default | Effect |
|---|---|---|---|
| `get_fund_object` maxsize | lru_cache | 16 | Max cached FundCompany/Series/Class objects in data.py:632 |
| `_fund_ticker_set` maxsize | lru_cache | 1 | Single cached frozenset of all mutual fund tickers |
| `TickerSeriesResolver.resolve_ticker_to_series` maxsize | lru_cache | 128 | Ticker→series resolution cache |
| `TickerResolutionService.resolve_ticker` maxsize | lru_cache | 128 | Holding-level ticker resolution cache |
| `get_fund_reference_data()` maxsize | lru_cache | 1 | Full SEC bulk fund CSV in-memory |
| `get_bulk_fund_data()` maxsize | lru_cache | 1 | Raw DataFrame from SEC bulk CSV |
| `investment_data(include_derivatives)` | bool | True | Include derivative positions in holdings DataFrame |
| `investment_data(include_ticker_metadata)` | bool | False | Add ticker_resolution_method/confidence columns |
| `Fund.get_filings(series_only)` | bool | False | Use EFTS search (capped at 100) vs entity get_filings |
| `MoneyMarketFund` schema detection | bytes check | auto | `b'edgar/nmfp2'` in XML → is_v2=True |
| `FundReport._investment_data_cache` | dict | {} | Keyed by (include_derivatives, include_ticker_metadata) |

---

### Data Flow / Lifecycle

**Entity resolution (Fund("VFINX")):**
1. `Fund.__init__` detects ticker → calls `TickerSeriesResolver.get_primary_series("VFINX")`
2. Resolver hits `get_mutual_fund_tickers()` (cached DataFrame), finds matching row → returns `seriesId`
3. Stores `_target_series_id`; calls `find_fund("VFINX")`
4. `find_fund` → `is_fund_class_ticker` → True → `get_fund_class("VFINX")`
5. `get_fund_class` → `get_fund_object("VFINX")` (lru_cache maxsize=16)
6. Fast path: `_resolve_from_mf_tickers("VFINX")` gets CIK → `_build_hierarchy_from_mf_tickers()`
7. Builds full `FundCompany` with all series and classes; enriches names from `FundReferenceData` (0 extra HTTP calls)
8. Returns `FundClass` with backref `series` → `series.fund_company`
9. `Fund._entity = FundClass`, `_company`, `_series`, `_class` all populated

**N-PORT filing → holdings DataFrame:**
1. `filing.obj()` dispatched via `edgar/__init__.py:409` → `FundReport.from_filing(filing)`
2. `from_filing` calls `filing.xml()` → `parse_fund_xml(xml_bytes)`
3. lxml parses; `_strip_namespaces()` removes all namespace prefixes
4. Navigates `edgarSubmission/headerData`, `formData/genInfo`, `formData/fundInfo`, `formData/invstOrSecs`
5. Each `invstOrSec` → `InvestmentOrSecurity`; `derivativeInfo` child → `DerivativeInfo.from_xml()`
6. Sets `report._filing = filing`
7. User calls `report.investment_data()` → builds list of row dicts, constructs DataFrame, sorts by abs(value_usd), caches

**Ticker resolution on holdings:**
- `InvestmentOrSecurity.ticker` property calls `TickerResolutionService.resolve_ticker(ticker, cusip, isin, name)`
- If direct ticker present: returns it (confidence 1.0)
- Else: `_resolve_via_cusip()` → `get_ticker_from_cusip(cusip)` dict lookup (confidence 0.85)
- Placeholder CUSIPs (`000000000`, empty, N/A) are silently skipped

**N-MFP2 vs N-MFP3 parsing:**
- `MoneyMarketFund._parse_xml()` detects schema version from `b'edgar/nmfp2' in xml_bytes` before namespace stripping
- V3: `sevenDayGrossYield` elements with date children; `dailyNetAssetValuePerShareSeries` elements
- V2: scalar `sevenDayGrossYield`; NAV in `netAssetValue/fridayWeek1-5`; liquidity in parallel `fridayDay1-4`/`fridayWeek1-5` structures

**N-CSR parsing:**
- Unlike all others, uses `filing.xbrl()` not `filing.xml()`
- `_parse_xbrl()` queries `oef:` namespace facts via `FactQuery` API
- Share class discovery: `facts.query().by_dimension("oef:ClassAxis")` → collects member IDs
- Single-class funds: falls back to undimensioned facts via `_parse_undimensioned_share_class()`

**SEC bulk CSV reference data:**
1. `get_bulk_fund_data()` calls `_find_latest_fund_data_url()` → scrapes SEC opendatasets page for latest CSV link
2. Downloads CSV; returns raw DataFrame
3. `get_fund_reference_data()` wraps in `FundReferenceData(df)` → normalizes into `_companies`, `_series`, `_classes` dicts with cross-reference indexes
4. `_build_hierarchy_from_mf_tickers()` calls `get_fund_reference_data()` for name enrichment (0 HTTP calls after first call)

---

### Design Patterns

- **Lazy hierarchy construction**: `get_fund_object()` builds the full Company→Series→Class tree in one pass and returns only the target node — `data.py:632`
- **Fast path / slow path fallback**: All resolution first tries cached `get_mutual_fund_tickers()` (0 HTTP); only falls back to SEC browse-edgar (2 HTTP calls) if not found — `data.py:656`
- **Sentinel for "not computed"**: `_SENTINEL = object()` distinguishes "not yet computed" from None/empty DataFrame in FundReport caches — `reports.py:29`
- **lxml for performance**: N-PORT and N-MFP XML parsing uses lxml directly (10-20x faster than BeautifulSoup); namespace stripping applied once via `_strip_namespaces()` — `reports.py:74`
- **ETF synthetic series IDs**: ETF company tickers that have no mutual fund series ID get `series_id = "ETF_<CIK>"` as a synthetic marker to distinguish them from unresolved failures — `series_resolution.py:75`
- **Multi-block aggregation (24F-2NT)**: `FundFeeNotice` aggregates per-class `annualFilingInfo` blocks transparently; all typed financial properties call `_sum_item5()` which iterates blocks — `twentyfourf.py:276`
- **XBRL dimension-driven discovery (N-CSR)**: Share classes discovered dynamically via `oef:ClassAxis` query rather than hard-coded structure — `ncsr.py:451`
- **HTML table parsing for 497K**: Two layout patterns handled (multi-column vs repeated-section) in `_497k_tables.py`; SGML header parsed separately for series/class/ticker IDs — `prospectus497k.py:547`
- **Pydantic for filing sub-models**: All structured N-PORT sub-objects use Pydantic BaseModel for validation/serialization; top-level `FundReport` is a plain class with explicit caching — `reports.py:91+`

---

### Cross-Domain Interactions

**This domain imports from:**
- `edgar.entity.core.Entity` — `FundCompany` base class
- `edgar.entity.data.EntityData` — `FundData` base class
- `edgar._filings.Filings` — Returned from `get_filings()`
- `edgar.httprequests.download_text` — HTTP fetches for browse-edgar and bulk CSV
- `edgar.reference.tickers.get_mutual_fund_tickers` — Primary mf ticker DataFrame (cached)
- `edgar.reference.tickers.get_company_tickers`, `find_cik` — ETF fallback
- `edgar.reference.tickers.get_ticker_from_cusip` — CUSIP→ticker dict lookup
- `edgar.datatools.drop_duplicates_pyarrow` — Dedup when paginating browse-edgar
- `edgar.search.efts.search_filings` — Optional EFTS search in `Fund.get_filings(series_only=True)`
- `edgar.xmlfiling.XmlFiling` — Base for `FundFeeNotice`
- `edgar.core.get_bool` — Boolean parsing utility
- `edgar.display.formatting.moneyfmt`, `format_currency_short` — Rich display formatting
- `edgar.richtools.repr_rich`, `df_to_rich_table` — Display helpers

**Other modules that consume this domain:**
- `edgar/__init__.py` — Central `filing.obj()` dispatch (lines 397–423) routes 497K/N-CEN/N-CSR/N-MFP/NPORT-P/24F-2NT to their respective `from_filing()` methods
- `edgar/funds/__init__.py` — Re-exports all public symbols; defines `get_fund_with_filings()` backward compat wrapper and legacy `FundSeriesAndContracts`
- `edgar/thirteenf.py` — Referenced via `edgar/funds/thirteenf.py` lazy import wrapper (`get_ThirteenF()`)

---

### Gotchas & Notable Behaviors

**Ticker resolution:**
- `is_fund_ticker()` uses an O(1) frozenset (`_fund_ticker_set`) — but only covers mutual funds; ETF company tickers are NOT in this set and return False, leading `find_fund()` to call `get_fund_company()` instead of `get_fund_class()`. `Fund.__init__` compensates by running `TickerSeriesResolver` separately before `find_fund()` — `core.py:370`
- ETFs resolved via company tickers get synthetic `series_id = "ETF_<CIK>"` and synthetic `class_id = "ETF_CLASS_<CIK>"`. These are NOT real SEC series IDs. `Fund.get_series()` detects them and constructs a `FundSeries` from `get_company_tickers()` instead — `core.py:502`
- `TickerSeriesResolver.get_primary_series()` always returns `series_list[0]` for multi-series tickers (no smarter disambiguation) — `series_resolution.py:102`

**N-PORT:**
- `parse_fund_xml()` uses `etree.XMLParser(recover=True)` as fallback for malformed XML — `reports.py:1237`
- Both `N-PORT` and `N-PORT/A` and `NPORT-EX` are in `NPORT_FORMS` but `edgar/__init__.py` only dispatches `["NPORT-P", "NPORT-EX"]` — `N-PORT` and `N-PORT/A` forms are in the constant but NOT dispatched
- The `_SENTINEL` object (not None) is used for `_derivatives_data_cache`, `_investments_table_cache`, `_derivatives_table_cache` to allow caching of empty DataFrames
- `investment_data()` cache key is the tuple `(include_derivatives, include_ticker_metadata)` — calling with different combos creates separate cache entries — `reports.py:553`
- Holdings sorted by `abs(value_usd)` descending — short positions appear high in the table

**N-MFP2 (legacy):**
- `registrant_name` and `series_name` are empty strings (not None) for N-MFP2 because the XML lacks those tags — `nmfp3.py:546`
- `couponOrYield` tag (N-MFP2) vs `coupon` tag (N-MFP3) in collateral — `nmfp3.py:799`
- `dialyShareholderFlowReported` is a typo in the SEC schema (should be "daily") — the code matches the misspelling intentionally — `nmfp3.py:674`

**N-CSR:**
- `_cik` and `_series_id` are set post-construction in `from_filing()` since they come from the filing, not the XBRL — `ncsr.py:352`
- Single-class funds with no `ClassAxis` dimension facts will have `_parse_undimensioned_share_class()` called, but that only returns a class if at least one of expense_ratio, annual_returns, or holdings is non-empty — `ncsr.py:386`

**497K:**
- No XBRL at all. Series/class/ticker identity comes from SGML header `<SERIES-AND-CLASSES-CONTRACTS-DATA>` block, not from HTML content — `prospectus497k.py:86`
- Two HTML layout patterns (multi-column / repeated-section) handled in `_497k_tables.py`; ~20,000 filings/year with very consistent structure but edge cases exist

**FundFeeNotice (24F-2NT):**
- `FundFeeNotice` inherits `from_filing()` from `XmlFiling` — it does NOT define its own — `xmlfiling.py`
- `class_fees` returns empty list for fund-level (single-block) filings; callers must check `is_per_class` first — `twentyfourf.py:357`
- `_parse_float()` handles accounting-parentheses negatives: `(123.45)` → `-123.45` — `twentyfourf.py:97`
- `series` property deduplicates by series_id across blocks (all per-class blocks typically reference the same parent series) — `twentyfourf.py:203`

**FundReferenceData / reference.py:**
- `get_bulk_fund_data()` scrapes the SEC opendatasets page to find the current CSV URL; if the page structure changes, `_find_latest_fund_data_url()` raises `ValueError` — `reference.py:496`
- CIK keys are always zero-padded to 10 digits in `_companies` dict. Input CIKs may arrive as `float` (e.g., `225323.0` from the SEC bulk CSV) — `_normalize_cik()` coerces through `int` before `zfill(10)` so `225323.0`, `225323`, and `"225323"` all resolve to the same key. Without this, `str(225323.0).zfill(10)` produces `"00225323.0"` which never matches any key and causes `get_company()` to silently return `None` — `reference.py:19`

**General:**
- `get_fund_object()` has `lru_cache(maxsize=16)` — in scripts processing many different funds, this may evict entries and trigger re-fetching — `data.py:632`
- `resolve_fund_identifier()` short-circuits for integers and purely-numeric strings (already a CIK) — `data.py:782`
- `FundSeriesAndContracts` and `get_fund_with_filings()` in `__init__.py` are legacy backward-compat wrappers and should not be used in new code — `__init__.py:87`
- The `parse_series_and_classes_from_html()` function in `data.py` is a secondary HTML parser used only when the fast `_parse_series_table()` fails; it has more complex parsing logic for edge-case SEC page layouts — `data.py:888`
