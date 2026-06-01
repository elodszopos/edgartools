## Entity Facts — Statements & Query

### Overview

The `edgar.entity` statements/query layer converts a company's raw XBRL facts (fetched from the SEC Company Facts API at `data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`) into structured, display-ready financial statements. It is entirely independent of the XBRL-parsing path (`edgar.xbrl.xbrl.py`): instead of parsing filing-embedded XBRL documents, it works from the aggregated SEC CompanyFacts endpoint and maps each concept to a statement type using **learned mappings** trained from real XBRL filings. The output is a `MultiPeriodStatement` showing hierarchical rows with multiple side-by-side time periods. This path is the primary one exposed to users via `Company.facts.income_statement()` etc.

---

### Public API Surface

| Symbol | file:line | Purpose |
|---|---|---|
| `EntityFacts` | `entity_facts.py:136` | Top-level object holding all facts for one company |
| `EntityFacts.query()` | `entity_facts.py:586` | Entry point to `FactQuery` builder |
| `EntityFacts.income_statement(...)` | `entity_facts.py:1697` | Build income statement (annual/quarterly/TTM) |
| `EntityFacts.balance_sheet(...)` | `entity_facts.py:1759` | Build balance sheet (annual/quarterly/as-of date) |
| `EntityFacts.cashflow_statement(...)` | `entity_facts.py:1867` | Build cash flow statement |
| `EntityFacts.get_fact(concept, period)` | `entity_facts.py:600` | Single fact lookup |
| `EntityFacts.get_annual_fact(concept, fiscal_year)` | `entity_facts.py:653` | Annual-only fact lookup |
| `EntityFacts.time_series(concept, periods)` | `entity_facts.py:714` | Multi-period concept time series |
| `EntityFacts.search_concepts(pattern)` | `entity_facts.py:1220` | Fuzzy concept discovery |
| `EntityFacts.available_periods(concept)` | `entity_facts.py:1282` | List valid period keys |
| `EntityFacts.shares_outstanding` | `entity_facts.py:1369` | Property: most recent share count |
| `FactQuery` | `query.py:28` | Fluent filter/sort/execute builder |
| `FactQuery.pivot_by_period(...)` | `query.py:702` | Pivot to `FinancialStatement` |
| `FinancialStatement` | `statement.py:34` | DataFrame wrapper with Rich display |
| `MultiPeriodStatement` | `enhanced_statement.py:171` | Hierarchical multi-period output |
| `MultiPeriodItem` | `enhanced_statement.py:1096` | Single row with per-period values |
| `EnhancedStatementBuilder` | `enhanced_statement.py:1377` | Builds `MultiPeriodStatement` from facts |
| `StatementBuilder` | `statement_builder.py:390` | Lower-level single-period builder |
| `StructuredStatement` | `statement_builder.py:128` | Output of `StatementBuilder` |
| `StatementItem` | `statement_builder.py:30` | Single item in `StructuredStatement` |
| `FinancialFact` | `models.py:22` | Core fact dataclass (slots=True) |
| `DataQuality` | `models.py:14` | Enum: HIGH/MEDIUM/LOW |
| `UnitNormalizer` | `unit_handling.py:65` | Normalizes unit strings |
| `UnitResult` | `unit_handling.py:49` | Result dataclass for unit normalization |
| `UnitType` | `unit_handling.py:37` | Enum: CURRENCY/SHARES/RATIO/BUSINESS/TIME/AREA/OTHER |
| `load_learned_mappings()` | `mappings_loader.py:18` | lru_cache load of `statement_mappings_v1.json` |
| `load_virtual_trees()` | `mappings_loader.py:76` | lru_cache load of `virtual_trees.json` |
| `load_canonical_structures()` | `mappings_loader.py:49` | lru_cache load of `learned_mappings.json` |
| `load_industry_extension(industry)` | `mappings_loader.py:258` | Load per-industry extension JSON |
| `get_concept_statements(concept)` | `mappings_loader.py:724` | Unified concept→statement index lookup |
| `get_primary_statement(concept)` | `mappings_loader.py:743` | Single-statement assignment for concept |
| `get_concepts_for_statement(stmt_type)` | `mappings_loader.py:772` | All concepts for a statement type |
| `NoCompanyFactsFound` | `entity_facts.py:43` | Exception for missing company data |
| `get_company_facts(cik)` | `entity_facts.py:97` | Module-level factory: fetch+parse+cache |
| `clear_company_facts_cache()` | `entity_facts.py:87` | Evict all cached `EntityFacts` objects |
| `ConceptSearchResults` | `models.py:285` | Rich-display result of `search_concepts()` |
| `PeriodSummary` | `models.py:376` | Rich-display result of `available_periods()` |
| `HierarchicalFactsResult` | `query.py:1087` | Tree-structured facts from `with_hierarchy()` |
| `get_current_scheme()` | `terminal_styles.py:130` | Active Rich color scheme |

---

### Key Classes

#### `FinancialFact` (`models.py:22`)
Dataclass (slots=True) representing a single XBRL fact. All facts share this model.

Key fields:
- `concept: str` — fully-qualified or bare concept name (e.g. `us-gaap:Revenue`)
- `taxonomy: str` — `us-gaap`, `ifrs-full`, `dei`, etc.
- `label: str` — human display label
- `value / numeric_value` — raw and float forms
- `unit: str` — normalized unit (see `UnitNormalizer`)
- `scale: Optional[int]` — scale factor; parser applies this to `numeric_value`
- `period_start / period_end / period_type` — temporal span; `period_type` is `'instant'` or `'duration'`
- `fiscal_year / fiscal_period` — e.g. `2024 / 'FY'` or `2024 / 'Q3'`
- `filing_date / form_type / accession` — filing provenance
- `data_quality: DataQuality` — HIGH/MEDIUM/LOW
- `confidence_score: float` — default 0.8
- `statement_type: Optional[str]` — assigned during parsing via `_determine_statement_type()`
- `depth / parent_concept / section / is_abstract / is_total / presentation_order` — structural metadata from learned mappings
- `dimensions: Optional[Dict[str, str]]` — XBRL dimensional context; stored as `None` (not `{}`) to save ~1.5 MB per company

Notable methods:
- `to_llm_context() -> Dict` — `models.py:84`
- `get_display_period_key() -> str` — `models.py:131`
- `get_formatted_value() -> str` — `models.py:172`

#### `EntityFacts` (`entity_facts.py:136`)
The main object users interact with. Holds `List[FinancialFact]` and pre-built six-way index.

Constructor: `__init__(cik, name, facts, sic_code=None, ticker=None)` — `entity_facts.py:145`

Indexes built at init (`_build_indices`, `entity_facts.py:183`):
- `by_concept` — keyed by concept string AND lowercased label
- `by_period` — keyed by `"YYYY-FP"` string (interned for memory)
- `by_statement` — keyed by statement_type
- `by_form` — keyed by form_type
- `by_fiscal_year` — keyed by int
- `by_fiscal_period` — keyed by `'FY'/'Q1'...`

Key query/statement methods:
- `query() -> FactQuery` — `entity_facts.py:586`
- `income_statement(periods, period_length, as_dataframe, annual, concise_format, period)` — `entity_facts.py:1697`; `period` is `'annual'|'quarterly'|'ttm'`; `annual` param is legacy override
- `balance_sheet(periods, as_of, as_dataframe, annual, concise_format, period)` — `entity_facts.py:1759`; when `as_of` is set, uses `FactQuery.latest_instant()` fallback returning a `FinancialStatement` instead of `MultiPeriodStatement`; TTM raises `ValueError`
- `cashflow_statement(periods, period_length, as_dataframe, annual, concise_format, period)` — `entity_facts.py:1867`
- `cash_flow(...)` — `entity_facts.py:1926` deprecated alias, removal at v6.0
- `_build_enhanced_statement(facts, statement_type, periods, annual, ...)` — `entity_facts.py:1669` — calls `EnhancedStatementBuilder`; also calls `_resolve_industry_info()` which lazily fetches SIC code via `_sic_resolver` callable (avoids submissions download just for raw fact access)

Properties:
- `shares_outstanding` — `entity_facts.py:1369`; tries `dei:EntityCommonStockSharesOutstanding`, falls back to `us-gaap:CommonStockSharesOutstanding`
- `public_float` — `entity_facts.py:~1400`
- `_ttm_ready_facts` — `entity_facts.py:1658`; cached_property returning an `EntityFacts` with split-adjusted, quarter-derived facts; used for quarterly/TTM statement paths

Helper methods:
- `_get_split_adjusted_facts()` — `entity_facts.py:1447`; calls `edgar.ttm.splits.detect_splits` + `apply_split_adjustments`; result is instance-cached via `_cached_split_adjusted_facts`
- `_prepare_quarterly_facts(facts)` — `entity_facts.py:1464`; uses `TTMCalculator` to derive quarter-level duration facts from annual data
- `search_concepts(pattern) -> ConceptSearchResults` — `entity_facts.py:1220`
- `available_periods(concept=None) -> PeriodSummary` — `entity_facts.py:1282`
- `time_series(concept, periods) -> pd.DataFrame` — `entity_facts.py:714`; returns columns `period_start, period_end, duration_days, numeric_value, fiscal_period, fiscal_year`
- `to_llm_context(...)` — `entity_facts.py:1986`

#### `FactQuery` (`query.py:28`)
Fluent builder. Holds `_all_facts: List[FinancialFact]`, `_indices: Dict`, `_filters: List[Callable]`, `_sort_field`, `_sort_ascending`, `_limit`.

Chaining filter methods (each returns `self`):
- `by_concept(concept, exact=False)` — `query.py:53`; exact uses index, inexact does case-insensitive substring on both concept and label
- `by_label(label, fuzzy=True)` — `query.py:78`
- `by_text(pattern)` — `query.py:96`; regex across concept/label/taxonomy/business_context/statement_type
- `by_fiscal_year(year)` — `query.py:145`
- `by_fiscal_period(period)` — `query.py:160`
- `by_period_length(months)` — `query.py:175`; allows ±1 month tolerance; requires `period_type == 'duration'` and `period_start` present
- `by_period_type(period_type)` — `query.py:203`; accepts `PeriodType` enum or string `'annual'/'quarterly'/'monthly'`; TTM/YTD raise `NotImplementedError`
- `date_range(start, end)` — `query.py:266`; filters on `fact.period_end`; accepts `date` or `'YYYY-MM-DD'` strings
- `as_of(as_of_date)` — `query.py:318`; filters `filing_date <= as_of_date`
- `high_quality_only()` — `query.py:334`; requires `DataQuality.HIGH and is_audited`
- `min_confidence(threshold)` — `query.py:346`
- `by_statement_type(statement_type)` — `query.py:360`; uses index
- `by_form_type(form_type)` — `query.py:375`; accepts string or list
- `latest_instant()` — `query.py:400`; adds post-filter keeping only max `period_end` per concept; for balance sheet snapshot
- `latest_periods(n, annual)` — `query.py:424`; when `annual=True`, uses only FY periods sorted by `fiscal_year` descending; when `annual=False`, sorts all periods by `period_end`
- `by_section(section)` — `query.py:482`
- `by_depth(max_depth)` — `query.py:498`
- `totals_only()` — `query.py:513`
- `concrete_only()` — `query.py:523`
- `abstracts_only()` — `query.py:533`
- `with_parent(parent_concept)` — `query.py:543`
- `root_items_only()` — `query.py:558`
- `sort_by(field, ascending)` — `query.py:571`

Execution methods:
- `execute() -> List[FinancialFact]` — `query.py:602`; applies all filters, then optional post_filter, then sort, then limit
- `latest(n) -> List[FinancialFact]` — `query.py:586`; sorts by filing_date desc, limits to n
- `count() -> int` — `query.py:919`
- `to_dataframe(*columns) -> pd.DataFrame` — `query.py:641`
- `to_llm_context() -> List[Dict]` — `query.py:692`
- `pivot_by_period(return_statement=True)` — `query.py:702`; deduplicates facts first (prefers 10-K over 10-Q, non-amendment over amendment, most recent filing); pivots to period-columns; detects mixed periods; returns `FinancialStatement` or raw DataFrame
- `with_hierarchy() -> HierarchicalFactsResult` — `query.py:631`

Deduplication logic (`_deduplicate_facts`, `query.py:928`): groups by `(concept, period_end, 'instant')` or `(concept, period_start, period_end, 'duration')`; priority: `(filing_date, 10-K preference, non-amendment)`.

Period label formatting (`_format_period_label`, `query.py:826`): FY → `"FY YYYY"`, 3-month duration → `"Q[1-4] YYYY"`, 6-month → `"6M YYYY"`, 9-month → `"9M YYYY"`, 12-month → `"FY YYYY"`.

#### `EnhancedStatementBuilder` (`enhanced_statement.py:1377`)
Builds `MultiPeriodStatement` from a flat `List[FinancialFact]`. Instantiated with optional `sic_code` and `ticker` for industry extension merging.

Constructor: `__init__(sic_code=None, ticker=None)` — `enhanced_statement.py:1451`; immediately calls `get_industry(sic_code, ticker)` and `load_industry_extension(industry)` if industry is detected.

Main method: `build_multi_period_statement(facts, statement_type, periods, annual)` — `enhanced_statement.py:1493`

**Period selection logic (annual mode, `enhanced_statement.py:1548`):**
1. Detect `fiscal_year_end_month` from FY `period_end` dates via `detect_fiscal_year_end()`
2. Filter to FY facts only; for each, check duration > 300 days to confirm "truly annual" (fixes Issue #408 where quarterly facts are tagged `fiscal_period='FY'`)
3. Validate `fiscal_year` vs `period_end` via `validate_fiscal_year_period_end()` (Issue #452 — mislabeled comparative data)
4. Group by `period_end.year`, prefer: ≥5 facts, fiscal_year matches expected, most recent filing_date
5. For December FYE companies: use `period_end.year` for label (not SEC's `fiscal_year`); for other FYE: use SEC's `fiscal_year`
6. Select up to `periods` most recent annual years

**Period selection logic (quarterly mode, `enhanced_statement.py:1641`):**
1. Skip FY facts; validate `fiscal_year` vs `period_end` (Issue #781 — forward-looking schedule data)
2. Validate `period_end` month matches expected quarter month via `validate_quarterly_period_end()`
3. Calculate correct fiscal year label using `calculate_fiscal_year_for_label(period_end, fye_month)` (Issue #460 — SEC uses forward-looking fiscal_year for non-December FYE)
4. Deduplication: prefer "primary" data (fact's `fiscal_year` == calculated label year) over comparative disclosures; within same class, prefer most recent filing

**Hierarchy building (`_build_with_canonical`, `enhanced_statement.py:1918`):**
1. Load virtual tree with industry extension merged via `_get_merged_virtual_tree()`
2. Create per-period fact maps
3. For `IncomeStatement`: call `_build_with_promoted_concepts()` which promotes Revenue, Cost of Revenue, GrossProfit, OperatingIncomeLoss, NetIncomeLoss, EPS to flat top-level children, deduplicating synonyms
4. For other statements: iterate `virtual_tree['roots']` recursively
5. Add orphan facts not in virtual tree as "Additional Financial Items" abstract section
6. Add calculated metrics (GrossProfit = Revenue − CostOfRevenue if missing)
7. Apply smart aggregation: if parent node has no value but children sum is computable, calculate and mark with `' (Aggregated)'`
8. Deduplicate table items (`_deduplicate_table_items`) — removes Statement[Table] dimensional duplicates
9. Filter empty items
10. For IncomeStatement: reorder children by canonical concept_order list

**Revenue deduplication** (`_create_deduplicated_revenue_item`, `enhanced_statement.py:2216`): tries `_REVENUE_CONCEPTS` in priority order per period; fallback: `GrossProfit + CostOfRevenue`; always labels as "Total Revenue".

**Concept normalization** (`CONCEPT_NORMALIZATIONS`, `enhanced_statement.py:1422`): maps synonyms (e.g. `CostOfGoodsAndServicesSold` → `CostOfRevenue`, `LongTermDebtNoncurrent` → `LongTermDebt`) before matching against virtual tree.

**ESSENTIAL_CONCEPTS** (`enhanced_statement.py:1383`): per-statement sets of concepts always shown if they have data (includes `AccountsReceivable`, `LongTermDebt`, `Goodwill`, `DepreciationAndAmortization`, `PaymentsForRepurchaseOfCommonStock`, etc.).

**Industry extension merging** (`_get_merged_virtual_tree`, `enhanced_statement.py:1869`): deep-copies base tree, adds industry-specific nodes, inserts them into parent `children` lists if parent exists in merged tree.

**Linked concept flow** (`_fact_belongs_to_statement`, `enhanced_statement.py:128`; `_ACCEPTS_LINKED_FROM`, `enhanced_statement.py:87`): Income/Balance → CashFlow/Equity/ComprehensiveIncome (but not reverse). A fact from IncomeStatement can appear in CashFlow if `get_all_statements_for_concept()` confirms it.

#### `MultiPeriodStatement` (`enhanced_statement.py:171`)
Dataclass (with `__rich__`) representing the final hierarchical statement.

Fields: `statement_type, periods: List[str], items: List[MultiPeriodItem], company_name, ticker, cik, canonical_coverage: float, concise_format: bool`

Key methods:
- `__rich__()` — `enhanced_statement.py:196`; builds Rich `Panel` with centered SEC-filing-style header, dynamic label column width via `_calculate_label_width(num_periods, terminal_width)`, value columns per period; shows confidence markers (◦) for items with confidence < 0.8; always uses concise format for display
- `to_dataframe()` — `enhanced_statement.py:348`; concept as index, period values as columns
- `to_llm_context(include_metadata, include_hierarchy, flatten_values)` — `enhanced_statement.py:396`; flattened `{concept_period_key: value}` or nested; includes `key_metrics` (margins, growth rates, ratios)
- `to_llm_string()` — `enhanced_statement.py:1055`; no Rich Panel wrapper, no ANSI codes, 120-char width; minimal box style
- `to_dict(include_empty)` — `enhanced_statement.py:795`; JSON-serializable
- `to_flat_list()` — `enhanced_statement.py:855`; row-per-item with formatted values
- `get_period_comparison(period1, period2)` — `enhanced_statement.py:895`; change + change_percent per item
- `find_item(concept, label)` — `enhanced_statement.py:769`
- `__iter__` — `enhanced_statement.py:695`; depth-first traversal
- `iter_hierarchy()` — `enhanced_statement.py:713`; yields `(item, depth, parent)`
- `iter_with_values()` — `enhanced_statement.py:732`

Period argument normalization: `normalize_period_to_statement()` (`utils.py:29`) accepts both `"FY 2023"` and `"2023-FY"` formats.

#### `MultiPeriodItem` (`enhanced_statement.py:1096`)
Dataclass: `concept, label, values: Dict[str, Optional[float]], depth, parent_concept, children: List[MultiPeriodItem], is_abstract, is_total, section, confidence: float = 1.0`

`get_display_value(period, concise_format)` — `enhanced_statement.py:1113`; per-share detection by label keywords; concise format uses B/M/K suffixes.

#### `StatementBuilder` (`statement_builder.py:390`)
Older single-period builder using canonical structures. Less frequently used now — `EnhancedStatementBuilder` is the primary path.

`build_statement(facts, statement_type, fiscal_year, fiscal_period, use_canonical, include_missing)` — `statement_builder.py:410`; returns `StructuredStatement`.

When `use_canonical=True` and the statement type has a virtual tree: walks `virtual_tree['roots']` recursively, skips missing concepts with `occurrence_rate < 0.8` unless `include_missing=True`, appends unmatched facts at the end. When `use_canonical=False`: builds from `parent_concept` relationships directly.

#### `FinancialStatement` (`statement.py:34`)
Thin wrapper around a `pd.DataFrame` (concept as index, periods as columns). Used for `FactQuery.pivot_by_period()` and `balance_sheet(as_of=...)` output.

`CONCEPT_FORMATS` dict — `statement.py:46`; pattern-keyed formatting rules: EPS → 2 decimals, per-share → 2 decimals, margins → percentage, shares outstanding → no scale.

Key methods:
- `get_concept_formatting(concept_label) -> ConceptFormatting` — `statement.py:100`
- `format_value(value, concept_label) -> str` — `statement.py:120`
- `get_concept(concept_name) -> Optional[pd.Series]` — `statement.py:433`; tries exact, then case-insensitive substring
- `calculate_growth(concept_name, periods) -> Optional[pd.Series]` — `statement.py:455`; `pct_change(periods)`
- `to_numeric() -> pd.DataFrame` — `statement.py:387`; returns copy of original numeric data
- `to_llm_context() -> Dict` — `statement.py:396`

`ConceptFormatting` dataclass — `statement.py:26`; fields: `decimal_places=2, show_currency=True, scale_display=True, percentage=False`.

#### `UnitNormalizer` (`unit_handling.py:65`)
Class-level static maps: `CURRENCY_MAPPINGS`, `SHARE_MAPPINGS`, `RATIO_MAPPINGS`, `PER_SHARE_MAPPINGS`, `BUSINESS_MAPPINGS`, `TIME_MAPPINGS`, `AREA_MAPPINGS` → combined into `ALL_MAPPINGS`. Reverse mapping is lazily built and cached as `_REVERSE_MAPPING`.

Key class methods:
- `normalize_unit(unit) -> str` — `unit_handling.py:185`; upper-cases, looks up reverse map, returns original if not found
- `get_unit_type(unit) -> UnitType` — `unit_handling.py:210`
- `are_compatible(unit1, unit2) -> bool` — `unit_handling.py:241`; exact match → True; same CURRENCY type → True unless one is PER_SHARE (per-share must match exactly); SHARES → `'shares'/'shares_unit'` cross-compatible
- `get_normalized_value(fact, target_unit, apply_scale, strict_unit_match) -> UnitResult` — `unit_handling.py:278`; applies `fact.scale`, checks target_unit compatibility, returns `UnitResult` with `success, value, suggestions`

Module-level functions: `apply_scale_factor(value, scale)`, `format_unit_error(unit_result)`, `normalize_unit_legacy(unit)`, `are_units_compatible_legacy(unit1, unit2)`.

#### `EntityFactsParser` (`parser.py:20`)
Converts raw SEC company facts JSON (as loaded by `get_company_facts()`) into `EntityFacts`.

`parse_company_facts(json_data) -> Optional[EntityFacts]` — `parser.py:41`. Performance optimizations:
- `sys.intern` + local `_intern_cache` for repeated strings (taxonomy, fiscal_period, form_type, concept, unit, statement_type — deduplicating across 20K+ facts)
- Per-concept metadata (statement_type, semantic_tags, structural_info) computed once and shared across all unit × fact entries
- `structural_info` dict is shared (read-only); parent/section strings are interned

`_determine_statement_type(concept)` — `parser.py:287`; calls `get_primary_statement(concept)` which queries the unified concept-statement index in `mappings_loader.py`. Falls back to `load_learned_mappings()` then hardcoded FALLBACK/IFRS dicts.

`_get_structural_info(concept)` — returns depth, parent_concept, section, is_abstract, is_total from learned mappings (pre-computed once per concept during parse).

---

### Class Hierarchy

```
object
├── FinancialFact (dataclass, slots=True)  [models.py:22]
├── DataQuality (Enum)                      [models.py:14]
├── UnitType (Enum)                         [unit_handling.py:37]
├── UnitResult (dataclass)                  [unit_handling.py:49]
├── UnitNormalizer                          [unit_handling.py:65]
│
├── EntityFacts                             [entity_facts.py:136]
│   └── (contains List[FinancialFact] + Dict indices)
│
├── FactQuery                               [query.py:28]
│   └── returns → List[FinancialFact] | FinancialStatement | HierarchicalFactsResult
├── HierarchicalFactsResult                 [query.py:1087]
│
├── FinancialStatement                      [statement.py:34]
│   └── wraps pd.DataFrame
│
├── MultiPeriodStatement (dataclass)        [enhanced_statement.py:171]
│   └── items: List[MultiPeriodItem]
├── MultiPeriodItem (dataclass)             [enhanced_statement.py:1096]
│   └── children: List[MultiPeriodItem]    (recursive)
│
├── EnhancedStatementBuilder               [enhanced_statement.py:1377]
│   └── builds → MultiPeriodStatement
│
├── StatementBuilder                        [statement_builder.py:390]
│   └── builds → StructuredStatement
├── StructuredStatement (dataclass)         [statement_builder.py:128]
│   └── items: List[StatementItem]
├── StatementItem (dataclass)               [statement_builder.py:30]
│   └── children: List[StatementItem]
│
├── EntityFactsParser                       [parser.py:20]
│   └── parse_company_facts → EntityFacts
│
├── ConceptFormatting (dataclass)           [statement.py:26]
├── ConceptMetadata (dataclass)             [models.py:211]
├── FactCollection (dataclass)              [models.py:240]
├── ConceptMatch (dataclass)               [models.py:275]
├── ConceptSearchResults                    [models.py:285]
├── PeriodEntry (dataclass)                 [models.py:366]
├── PeriodSummary                           [models.py:376]
│
└── NoCompanyFactsFound (Exception)         [entity_facts.py:43]

training/
├── ConceptLearner                          [run_learning.py:270]
├── ConceptObservation (dataclass)          [run_learning.py:126]
├── ConceptStats (dataclass)               [run_learning.py:140]
├── CompanyStats (dataclass)               [run_learning.py:110]
└── MultiStatementInfo (dataclass)         [run_learning.py:206]
```

---

### Configuration & Options

| Option | Type | Default | Effect |
|---|---|---|---|
| `EDGAR_FINANCIALS_COLOR_SCHEME` | env var | `"professional"` | Selects Rich color scheme: `default`, `high_contrast`, `professional`, `minimal`, `accessible`, `filing` (`terminal_styles.py:130`) |
| `income_statement(periods)` | int | 4 | Number of periods in output |
| `income_statement(period)` | str | `'annual'` | `'annual'/'quarterly'/'ttm'` |
| `income_statement(annual)` | bool | None | Legacy: True→annual, False→quarterly, overrides `period` |
| `income_statement(concise_format)` | bool | False | `$1.0B` vs `$1,000,000,000` |
| `income_statement(as_dataframe)` | bool | False | Return DataFrame instead of `MultiPeriodStatement` |
| `balance_sheet(as_of)` | date | None | Point-in-time view; returns `FinancialStatement` not `MultiPeriodStatement` |
| `StatementBuilder(cik)` | str | None | CIK embedded in `StructuredStatement.cik` |
| `StatementBuilder.build_statement(use_canonical)` | bool | True | Use virtual tree vs raw fact hierarchy |
| `StatementBuilder.build_statement(include_missing)` | bool | False | Include placeholder items for missing canonical concepts |
| `EnhancedStatementBuilder(sic_code)` | str | None | Enables industry extension merging |
| `EnhancedStatementBuilder(ticker)` | str | None | Ticker-based industry lookup (payment_networks etc.) |
| `ConceptLearner(min_occurrence_rate)` | float | 0.30 | Threshold to include concept in learned_mappings output |
| `FactQuery.by_period_length(months)` | int | — | ±1 month tolerance around target |
| `FactQuery.latest_periods(n, annual)` | int, bool | 4, True | When `annual=True`, strict FY-only periods |
| `_COMPANY_FACTS_CACHE_MAXSIZE` | int | 1 | LRU cache size for `EntityFacts` objects (module constant `entity_facts.py:82`) |
| `load_learned_mappings / load_virtual_trees / load_canonical_structures / load_industry_extension` | — | `lru_cache` | Once-per-process JSON load |
| Industry `default_threshold` | float | 0.18–0.30 | Per-industry occurrence threshold (defined in `training/__init__.py:INDUSTRIES`) |

---

### Data Flow / Lifecycle

**Facts ingestion:**
1. `Company.get_facts()` → `get_company_facts(cik)` → checks in-memory LRU cache (`_company_facts_cache`, maxsize 1)
2. Cache miss: downloads `data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` or loads from local storage
3. `EntityFactsParser.parse_company_facts(json_data)` iterates `facts.us-gaap`, `facts.ifrs-full`, `facts.dei`, etc.
4. For each concept: determines `statement_type` via `_determine_statement_type()` → `get_primary_statement()` → `_build_concept_statement_index()` (which combines concept_linkages.json → learned_mappings.json → fallback dicts, with `lru_cache(maxsize=1)`)
5. `_get_structural_info()` reads depth/parent/section from learned_mappings; `_get_semantic_tags()` looks up `SEMANTIC_TAGS` dict
6. All string fields (taxonomy, unit, statement_type, concept, fiscal_period, etc.) are `sys.intern`-ed to reduce memory by deduplication across 20K+ facts
7. Each `FinancialFact` created with `dimensions=None` (not `{}`) to save ~1.5 MB
8. `EntityFacts` built with `_build_indices()` — six-way index over the full fact list (O(n) build, O(1) lookup by concept, period, etc.)
9. Unit normalization: `_clean_unit()` is called per (unit, concept) pair during parsing; `UnitNormalizer` used on-demand elsewhere

**Statement building (normal path):**
1. `facts.income_statement(periods=4)` → `_build_enhanced_statement(...)` → `_resolve_industry_info()` (lazy SIC/ticker fetch)
2. `EnhancedStatementBuilder.__init__`: loads `load_learned_mappings()`, `load_virtual_trees()` (both `lru_cache`), optionally loads `load_industry_extension(industry)` (`lru_cache(maxsize=10)`)
3. `build_multi_period_statement()`:
   - Filters facts to statement type via `_fact_belongs_to_statement()` (includes linked multi-statement concepts)
   - Groups facts into `period_info` dicts with `(fiscal_year, fiscal_period, period_end)` keys
   - Detects FYE month from FY `period_end` dates
   - Annual mode: validates each candidate period's duration (>300 days), validates fiscal_year vs period_end, groups by period_end.year, selects best
   - Quarterly mode: validates via `validate_quarterly_period_end()`, calculates correct fiscal_year for label, handles comparative data deduplication
   - Creates `period_facts_by_label` mapping labels to filtered fact lists
   - Delegates to `_build_with_canonical()` or `_build_from_facts()` based on virtual tree availability
4. `_build_with_canonical()`: merges industry extension → per-period fact maps → builds tree recursively → orphan section → calculated metrics → smart aggregation → dedup table items → filter empty → reorder (income only)
5. Returns `MultiPeriodStatement` with `company_name/ticker/cik` stamped by `_build_enhanced_statement()`

**TTM path:**
1. `income_statement(period='ttm')` → `_ttm_ready_facts` (`cached_property`) → `_prepare_quarterly_facts(_get_split_adjusted_facts())`
2. `TTMStatementBuilder(ttm_facts).build_income_statement()` (from `edgar.ttm.statement`)

**Query path:**
1. `facts.query()` returns `FactQuery(self._facts, self._fact_index)`
2. Chained filter calls accumulate lambda closures in `_filters`
3. `execute()`: linear scan (`[f for f in facts if filter(f)]`) applied sequentially; index-based filters use pre-computed sets of `id(f)` for O(1) membership testing
4. `pivot_by_period()`: deduplicates → builds records → `pd.pivot_table()` → sorts columns by date → wraps in `FinancialStatement`

**Caching:**
- `_company_facts_cache`: module-level `OrderedDict`, maxsize=1, LRU via `move_to_end`
- `load_learned_mappings / load_virtual_trees / load_canonical_structures`: `lru_cache(maxsize=1)` — process-level singletons, not invalidated between calls
- `load_industry_extension(industry)`: `lru_cache(maxsize=10)` — up to 10 industries in memory
- `_build_concept_statement_index()`: `lru_cache(maxsize=1)` — built once from all three sources
- `EntityFacts._get_split_adjusted_facts()`: stored as `_cached_split_adjusted_facts` instance attribute
- `EntityFacts._ttm_ready_facts`: `cached_property`

---

### Concept Mappings Architecture

The mapping system has four layers, consulted in priority order at parse time:

**Layer 1 — `concept_linkages.json`** (`entity/data/concept_linkages.json`): multi-statement concepts learned by the training pipeline. Each entry has `primary_statement`, `statements: List[str]`, and per-statement `occurrence_rate/label/parent`. Loaded by `load_concept_linkages()` (`mappings_loader.py:322`).

**Layer 2 — `statement_mappings_v1.json`** (`entity/data/statement_mappings_v1.json`): per-concept dict with `statement_type, confidence, label, parent, is_abstract, is_total, avg_depth, occurrence_rate, also_appears_in` (if multi-statement). Loaded by `load_learned_mappings()` (`mappings_loader.py:18`).

**Layer 3 — `learned_mappings.json`** (`entity/data/learned_mappings.json`): canonical structures loaded by `load_canonical_structures()` (`mappings_loader.py:49`) — same schema as statement_mappings_v1 content. Also used by `StatementBuilder`.

**Layer 4 — Hardcoded fallbacks** in `mappings_loader.py`: `_FALLBACK_CONCEPT_MAPPINGS` (US-GAAP, `mappings_loader.py:355`) and `_IFRS_FALLBACK_MAPPINGS` (IFRS for Foreign Private Issuers, `mappings_loader.py:395`). The IFRS dict covers ~200+ concepts for income, balance sheet, cash flow, comprehensive income, and metadata items.

**Virtual trees** (`virtual_trees.json`): per-statement hierarchical structure with `roots: List[str]`, `nodes: Dict[concept, {label, parent, depth, children, occurrence_rate, is_abstract, is_total}]`. Used as template by `EnhancedStatementBuilder` and `StatementBuilder`.

**Industry extensions** (`entity/data/industry_extensions/{industry}.json`): per-statement `nodes` dict of industry-specific concepts absent from canonical trees. 19 industries defined (banking, tech, healthcare, energy, insurance, retail, realestate, aerospace, automotive, consumergoods, hospitality, investment_companies, mining, securities, semiconductors, telecom, transportation, utilities, payment_networks). Loaded on demand and merged into the base virtual tree.

The **unified index** (`_build_concept_statement_index()`, `mappings_loader.py:652`) merges all four layers into `Dict[concept, {primary_statement, statements, statement_details}]`, cached with `lru_cache(maxsize=1)`.

---

### Training Tooling for Concept-Mapping Learning

The `edgar.entity.training` package contains offline learning pipelines that generate the data files above. Results must be deployed (copied) into `edgar/entity/data/` to take effect at runtime.

**`run_learning.py` — Canonical learning:**
Entry: `python -m edgar.entity.training.run_learning --companies 100 --exchange NYSE --min-occurrence 0.3`

`ConceptLearner` (`run_learning.py:270`) processes each company's latest 10-K XBRL via `xbrl.get_statement(stmt_type)` for 5 statement types. For each concept/filing:
- Cleans namespace prefix
- Detects `is_total` using XBRL-authoritative signals only: `preferred_label == TOTAL_LABEL` (totalLabel role) OR concept is a parent in calculation linkbase (`calculation_trees`). Label text heuristics were explicitly removed (caused false positives on dimensional segment labels)
- Tracks `ConceptStats` (per `concept:statement_type` key): labels, parents, depths, is_abstract/is_total counts, unique company CIKs
- Tracks `MultiStatementInfo` for cross-statement concept appearances

Outputs generated by `generate_outputs()` (`run_learning.py:879`):
- `learned_mappings.json` — per-concept, occurrence_rate = unique_company_count / successful_companies; multi-statement concepts get `also_appears_in` list; primary_statement = highest occurrence
- `virtual_trees.json` — tree structure per statement type, built from learned_mappings parent references
- `statement_mappings_v1.json` — same as learned_mappings with version metadata
- `canonical_structures.json` — raw statistical dump per statement
- `concept_linkages.json` — multi-statement concept categorization: `income_to_cashflow`, `balance_to_equity`, `balance_to_cashflow`, `income_to_comprehensive`, `xbrl_structural`; XBRL structural concepts (Table/Axis/Domain/Member/Abstract) separated first
- `learning_statistics.json` — coverage rates, per-company outliers, custom prefix analysis
- `structural_learning_report.md` — human-readable markdown

Parent validation (`_validate_parent_references`, `run_learning.py:632`): checks each concept's declared parent is present in learned_mappings; marks missing parents with `parent_in_mappings: False`.

**`run_industry_learning.py` — Industry learning:**
Entry: `python -m edgar.entity.training.run_industry_learning --industry banking --companies 150`

Reuses `ConceptLearner` but sources companies from SIC ranges (via `get_companies_by_industry()`) or curated ticker lists. `generate_industry_extension()` (`run_industry_learning.py:172`) explicitly excludes concepts already in canonical trees — the extension contains only additive, industry-specific concepts.

**Industries defined** (`training/__init__.py:41`):
19 industries with SIC ranges and `default_threshold` tuned per industry homogeneity:
- Homogeneous (banking, insurance): 0.25
- Moderate (tech, healthcare, semiconductors): 0.22
- Heterogeneous (retail, realestate, investment_companies): 0.18
- Payment networks: curated ticker list (V, MA, PYPL, etc.) since SIC codes don't map cleanly

**`deploy.py` — Deployment:**
`python -m edgar.entity.training.deploy --canonical` — copies `learned_mappings.json` + `virtual_trees.json` from `training/output/` to `edgar/entity/data/`
`python -m edgar.entity.training.deploy --industry banking` — copies `banking_extension.json` → `edgar/entity/data/industry_extensions/banking.json`
Supports `--dry-run`, `--force`, `--list`.

**`view.py` — Results viewer:**
`python -m edgar.entity.training.view` — Rich terminal UI showing: run summary, failure analysis by reason (no_10k_filings, no_xbrl_data, processing_error), concept counts (total/standard/custom/canonical/filtered), per-statement breakdown, custom concepts by company prefix, cross-statement linkages summary, outliers (high concept count, high custom rate, low coverage), per-company detail table.

---

### Fiscal Year / Period Date Logic

Three key validation/calculation functions in `enhanced_statement.py`:

**`calculate_fiscal_year_for_label(period_end, fiscal_year_end_month)`** (`enhanced_statement.py:1320`): implements the convention "fiscal year is named by the calendar year in which it ends". Early January (day ≤ 7) → returns `year - 1` (52/53-week calendar edge case). If `period_end.month > fiscal_year_end_month` → returns `period_end.year + 1`. Otherwise → `period_end.year`. Example: Apple (Sept FYE) Q1 ends Dec 2023 → FY2024.

**`validate_fiscal_year_period_end(fiscal_year, period_end, fiscal_year_end_month=12)`** (`enhanced_statement.py:1162`): calls `calculate_fiscal_year_for_label()` to get expected FY, then checks `year_diff == 0`. For early-January/late-December periods allows `year_diff in (0, 1)`. Handles Issues #452 (mislabeled comparatives) and #781 (forward-looking schedule data).

**`validate_quarterly_period_end(fiscal_period, period_end, fiscal_year_end_month=12)`** (`enhanced_statement.py:1233`): validates that `period_end.month` matches expected quarter month given the FYE month. Uses `±1 month` tolerance for 52/53-week calendars. Filters out comparative period reuse (Issue #452).

**`detect_fiscal_year_end(facts)`** (`enhanced_statement.py:1298`): finds most common `period_end.month` among FY facts; defaults to December.

---

### Design Patterns

- **Fluent builder / method chaining**: `FactQuery` accumulates filter closures then executes lazily; all filter methods return `self`. Terminal methods: `execute()`, `to_dataframe()`, `pivot_by_period()`, `count()`, `latest(n)`.
- **Composite / recursive tree**: `MultiPeriodItem.children: List[MultiPeriodItem]` forms the statement hierarchy. `StatementItem` has the same pattern. `MultiPeriodStatement.__iter__` does depth-first traversal.
- **Template method**: `EnhancedStatementBuilder._build_with_canonical()` defines the skeleton; calls `_build_with_promoted_concepts()` (for IncomeStatement) vs the generic root traversal for other statement types.
- **Strategy**: the statement-building path switches between canonical-tree mode and raw-facts mode based on virtual tree availability.
- **lru_cache singletons**: all JSON file loads are decorated with `@lru_cache(maxsize=1)` — process-wide singletons that must be cleared manually if data files change.
- **LRU eviction cache**: `_company_facts_cache` (OrderedDict + `move_to_end`/`popitem`) — manual LRU with `maxsize=1`; `clear_company_facts_cache()` for user-controlled eviction.
- **String interning**: `sys.intern` + local cache dict in parser — deduplicates ~10 high-frequency string fields across 20K+ facts per company to reduce memory pressure.
- **Deduplication by priority**: `_deduplicate_facts()` and quarterly deduplication prefer primary data (fact's `fiscal_year` == label year) over comparative disclosures; within same class prefer 10-K, non-amendment, most recent filing date.
- **Lazy industry resolution**: `EnhancedStatementBuilder` defers `_sic_resolver()` call until first statement build, avoiding submissions download for users who only need raw facts.

---

### Facts-Based Path vs XBRL Path

Two independent paths for financial statements exist in EdgarTools:

| Dimension | EntityFacts path | XBRL path |
|---|---|---|
| Source | SEC CompanyFacts API (`/api/xbrl/companyfacts/CIK{}.json`) | Filing XBRL documents (`filing.xbrl()`) |
| Scope | Entire history (all filings, all concepts) | Single filing instance |
| Entry point | `Company.facts.income_statement()` | `filing.xbrl().statements` or `TenK.financials` |
| Key classes | `EntityFacts`, `EnhancedStatementBuilder`, `MultiPeriodStatement` | `XBRL` (`edgar/xbrl/xbrl.py`), `Statement` (`edgar/xbrl/statements.py`) |
| Concept mapping | Learned mappings JSON + virtual trees | Presentation linkbase from XBRL filing itself |
| Period selection | Complex duration + fiscal_year validation logic | Filing's own XBRL context refs |
| Multi-period | Yes, up to N periods side-by-side | Per-filing (comparative columns in the XBRL doc) |
| Industry extension | Yes (19 industries) | No |
| TTM support | Yes (`edgar.ttm`) | No |
| Hierarchy | From virtual_trees canonical structure | From XBRL presentation linkbase |
| Used by CLAUDE.md recommended | `company.get_financials()` (uses EntityFacts) | `filing.xbrl()` (uses XBRL path) |

The two paths do NOT share code for statement building — XBRL path uses `xbrl.get_statement()` which reads from presentation linkbase in the filing, while EntityFacts path uses learned canonical templates.

---

### Cross-Domain Interactions

**Imports from other edgar.* modules:**
- `edgar.core.log` — logging
- `edgar.httprequests.download_json` — SEC API HTTP fetch
- `edgar.storage.get_edgar_data_directory`, `is_using_local_storage` — local/remote data path switching
- `edgar.richtools.repr_rich` — Rich repr helper
- `edgar.display.get_statement_styles, SYMBOLS, get_style` — unified design language constants
- `edgar.ttm.statement.TTMStatementBuilder` — TTM income/cashflow statements (lazy import)
- `edgar.ttm.splits.detect_splits, apply_split_adjustments` — stock split adjustment
- `edgar.ttm.calculator.TTMCalculator` — quarter fact derivation
- `edgar.enums.validate_period_type, PeriodType` — enum validation
- `edgar.xbrl` — ONLY in training scripts (to parse 10-K filings during learning); NOT at runtime

**Modules that consume this domain:**
- `edgar.entity.core.Company.get_facts()` — returns `EntityFacts`; `Company.get_facts()` overrides `Entity.get_facts()` to inject `sic_code` and `ticker`
- `edgar.entity.core.Entity.get_financials()` and `get_quarterly_financials()` — call `income_statement/balance_sheet/cashflow_statement`
- `edgar.company_reports` (TenK, TenQ) — call `entity.get_facts()` for the enhanced statement path
- `edgar.entity.__init__` exports: `EntityFacts, NoCompanyFactsFound, get_company_facts`

---

### Gotchas & Notable Behaviors

1. **Annual vs quarterly FY label confusion (Issues #408, #452, #460, #779)**: The SEC CompanyFacts API includes both annual and quarterly facts tagged `fiscal_period='FY'`; an annual fact may be ~363 days while a quarterly comparative is ~90 days. Duration > 300 days is the reliable annual signal. Additionally, the SEC's `fiscal_year` for a quarterly period uses a forward-looking convention (Q1 of Apple FY2025 ends Dec 2024, but is tagged `fiscal_year=2025`). `calculate_fiscal_year_for_label()` corrects this.

2. **Comparative data pollution**: When Apple files their FY2025 10-K, it restates Q3 2024 comparative data tagged with `fiscal_year=2025` but `period_end` in 2024. This creates collisions. The quarterly deduplication logic prefers "primary" entries (fiscal_year == calculated label year) over "comparative" entries (fiscal_year ahead of label year).

3. **lru_cache not invalidated**: All mapping file loads use `@lru_cache`. If `learned_mappings.json` or `virtual_trees.json` is replaced on disk, the process must be restarted (or the cache manually cleared via `load_learned_mappings.cache_clear()`) to pick up changes.

4. **Company facts LRU size = 1**: Only one company's facts are cached in memory at a time. Iterating over multiple companies (batch analysis) triggers download+parse on every access. Call `clear_company_facts_cache()` in long-running processes to control memory; each major company's facts is 40-80 MB.

5. **`balance_sheet(as_of=...)` returns `FinancialStatement` not `MultiPeriodStatement`**: When `as_of` is provided, the code falls back to `FactQuery.latest_instant()` path and wraps in the old `FinancialStatement` class, not `MultiPeriodStatement`. The API surface changes subtly.

6. **Period format dual convention**: `EntityFacts.get_fact(period=...)` uses `"2023-FY"` format. `MultiPeriodStatement.get_period_comparison(period1, period2)` and `MultiPeriodItem.get_display_value(period)` use `"FY 2023"` format. `normalize_period_to_entity_facts()` and `normalize_period_to_statement()` (`utils.py:19,29`) convert between them.

7. **`dimensions=None` not `{}`**: `FinancialFact.dimensions` defaults to `None` rather than an empty dict. Code checking `fact.dimensions` must handle `None`. The `is_dimensioned` property handles this (`bool(self.dimensions)`).

8. **Orphan facts confidence = 0.5**: Facts that have values but aren't in the canonical virtual tree are added as an "Additional Financial Items" section with `confidence=0.5`. They will display with the low-confidence marker (◦) in Rich output.

9. **`_build_with_promoted_concepts` for IncomeStatement**: revenue and cost synonyms are deduplicated at the root level (first available concept wins), and EPS items bypass their abstract parent. The abstract root's children are rebuilt from scratch — child order from the virtual tree is replaced by `concept_order` sort in `_reorder_income_statement()`.

10. **Industry extension is additive only**: `generate_industry_extension()` explicitly excludes any concept already in the canonical virtual tree. Industry extensions cannot override canonical concept placements, only add new ones.

11. **`cash_flow()` deprecated**: Alias for `cashflow_statement()`, removal planned for v6.0 (`entity_facts.py:1926`).

12. **`calculate_ratios()`, `peer_comparison()`, `detect_anomalies()` are stubs**: These methods exist on `EntityFacts` (`entity_facts.py:1940-1983`) but return placeholder dicts/DataFrames — Phase 3 placeholders.

13. **`by_period_type()` TTM/YTD raise NotImplementedError** (`query.py:256`): only `annual`, `quarterly`, `monthly` are implemented in `FactQuery.by_period_type()`.

14. **`_sic_resolver` callable**: `Company.get_facts()` can inject a lazy resolver callable for SIC code and ticker. `_resolve_industry_info()` calls it only when actually building statements — prevents unnecessary network calls for submissions data just to access raw facts.

15. **String interning memory savings**: The parser interns ~10 string fields. Without interning, 20K+ facts × repeated strings like `"us-gaap"`, `"USD"`, `"FY"`, `"10-K"` would create 20K+ separate string objects. With interning: ~5-10 shared objects.
