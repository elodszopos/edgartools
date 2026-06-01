## XBRL Rendering, Periods & Resolution

### Overview

This domain handles the complete pipeline from raw XBRL facts to rendered financial statements: resolving which presentation-linkbase role corresponds to a named statement type, selecting the right set of reporting periods (anchored to `filing.period_of_report`, with fiscal-year alignment scoring and 52/53-week drift tolerance), assembling line items into an intermediate `RenderedStatement` data model, and outputting that model as Rich console tables, Markdown, or JSON-serializable dicts. Supporting subsystems handle currency scaling for foreign filers, deduplication of synonym revenue concepts, balance-sheet accounting-equation validation, viewer-vs-XBRL cross-validation, abstract-concept detection, and per-period data-quality gating.

---

### Public API surface

| Symbol | file:line | Purpose |
|---|---|---|
| `render_statement(...)` | `rendering.py:1472` | Core function: builds a `RenderedStatement` from statement data + period list |
| `RenderedStatement` | `rendering.py:254` | Intermediate representation of a rendered statement; all output formats derive from it |
| `StatementHeader` | `rendering.py:244` | Period columns + metadata for a rendered statement |
| `StatementRow` | `rendering.py:232` | One data row with typed cells and hierarchy info |
| `StatementCell` | `rendering.py:175` | Single value cell with lazy formatter callable |
| `PeriodData` | `rendering.py:163` | Period metadata (key, label, start/end date, quarter) |
| `StatementResolver` | `statement_resolver.py:462` | Multi-strategy resolver from type name → presentation role |
| `StatementType` (dataclass) | `statement_resolver.py:38` | Registry entry with concepts, patterns, role patterns |
| `StatementCategory` (enum) | `statement_resolver.py:19` | FINANCIAL_STATEMENT / NOTE / DISCLOSURE / DOCUMENT / OTHER |
| `statement_registry` (dict) | `statement_resolver.py:91` | PascalCase → `StatementType` registry; 12 entries |
| `ESSENTIAL_CONCEPTS` (dict) | `statement_resolver.py:409` | Per-type concept groups required for validation |
| `select_periods(xbrl, statement_type, max_periods)` | `period_selector.py:31` | Primary period selection entry point |
| `determine_periods_to_display(...)` | `periods.py:298` | Legacy entry that delegates to `select_periods` with fallback |
| `get_period_views(xbrl_instance, statement_type)` | `periods.py:221` | Returns list of named period view options |
| `CurrentPeriodView` | `current_period.py:32` | Simplified single-period access for the most recent period |
| `validate_balance_sheet(...)` | `validation.py:301` | Accounting equation validation |
| `validate_statement(...)` | `validation.py:537` | Type-dispatching validator |
| `ValidationResult` | `validation.py:48` | Holds `is_valid`, `issues`, `checks_performed`, `metadata` |
| `CurrencyConverter` | `currency.py:70` | IFRS exchange-rate extraction and USD conversion |
| `ExchangeRate` | `currency.py:53` | Per-year average + closing exchange rates |
| `RevenueDeduplicator` | `deduplication_strategy.py:26` | Removes synonym revenue rows using precedence rules |
| `FilingViewer` | `viewer.py:232` | SEC Viewer equivalent; categorized report navigation + concept graph |
| `ViewerReport` | `viewer.py:80` | Wraps a `FilingSummary.Report` with concept annotations |
| `compare_viewer_to_xbrl(viewer, xbrl, tolerance)` | `viewer_validation.py:305` | Cross-validates R*.htm values against XBRL parser |
| `ComparisonResults` | `viewer_validation.py:211` | Aggregate match/mismatch summary |
| `is_abstract_concept(...)` | `abstract_detection.py:77` | Multi-tier abstract detection for concepts |
| `FundStatements` | `fund_statements.py:39` | Investment company filing detection + fund-specific statement access |

---

### Key classes

#### RenderedStatement (`rendering.py:254`)
Complete intermediate representation of a statement. Serializable and backend-agnostic.

- `__rich__() -> Panel` — renders a Rich `Panel` with centered SEC-style header, `box.SIMPLE` table, and subtitle footer. `rendering.py:422`
- `__str__() -> str` — calls `rich_to_text(..., width=150)` for terminal/plain output. `rendering.py:574`
- `to_dataframe(include_unit, include_point_in_time) -> pd.DataFrame` — column names are `end_date` strings from `PeriodData.end_date`, optionally suffixed with quarter. `rendering.py:579`
- `to_markdown(detail, optimize_for_llm) -> str` — GFM pipe table; `optimize_for_llm=True` drops abstract rows with no values. `rendering.py:659`
- `to_dict() -> Dict` — JSON-safe dict; pre-applies cell formatters so no callables remain. `rendering.py:286`
- `from_dict(data) -> RenderedStatement` — reconstructs from dict; replaces formatters with `PreformattedValue` passthrough. `rendering.py:362`
- `__getitem__(label) -> Optional[StatementRow]` — case-insensitive row lookup by exact label. `rendering.py:272`

#### render_statement() (`rendering.py:1472`)
The core rendering function. Call flow:

1. Filters XBRL structural elements and dimensional items (view-controlled).
2. Calls `_filter_empty_string_periods()` for major statements to drop all-empty periods (Issue #408).
3. Calls `standardization.standardize_statement_data()` if `standard=True`.
4. Calls `_format_period_labels()` → list of `PeriodData` + `fiscal_period_indicator` string.
5. Calls `determine_dominant_scale()` and `_create_units_note()`.
6. Optionally builds `comparison_data` (percent change between consecutive periods).
7. Iterates items: skips structural/axis/empty-abstract rows; for `StatementOfEquity` adds "Beginning balance" / "Ending balance" suffixes on repeated concepts and resolves instant facts from `instant_{day_before_start}` or `instant_{end_date}`.
8. Creates `StatementRow` with `CellFormatter` (picklable closure) for each period cell.
9. Returns populated `RenderedStatement`.

Key parameters: `standard`, `show_date_range`, `show_comparisons`, `include_dimensions`, `role_uri`, `view` (StatementView enum).

#### StatementResolver (`statement_resolver.py:462`)
Multi-layered statement matching. Builds five lookup indices at init: by role URI, role name, primary concept, statement type, and role definition.

- `find_statement(statement_type, is_parenthetical, category_filter) -> (stmts, role, canonical_type, conf)` — runs 6-step cascade: `_match_by_standard_name` (0.9) → `_match_by_primary_concept` (0.8) → `_match_by_concept_pattern` (0.8) → `_match_by_role_pattern` (0.7) → `_match_by_content` (0.6) → `_match_by_role_definition` (0.5). Results cached by `(type, parenthetical, category)`. `statement_resolver.py:1085`
- `_score_statement_quality(stmt, statement_type) -> int` — scores candidates; penalizes "details/table/schedule" (-50), parentheticals (-80), pure ComprehensiveIncome for IncomeStatement search (-100), tax disclosures (-100); boosts "consolidated" (+30), "condensed" (+20), exact primary names (+50). `statement_resolver.py:732`
- `_validate_statement(stmt, statement_type) -> (bool, float, reason)` — checks ESSENTIAL_CONCEPTS groups present in the presentation tree; `VALIDATION_THRESHOLD = 0.5`. `statement_resolver.py:551`

Special fallbacks (`statement_resolver.py:1173`):
- `IncomeStatement` not found → try `ComprehensiveIncome` candidates validated against IncomeStatement essential concepts (Issue #518/#608).
- `ComprehensiveIncome` not found → try `StatementOfEquity` candidates containing CI indicator concepts (Issue #706; handles pre-2015 filings like IBM/GE/Apple 2010-2012).

#### CurrentPeriodView (`current_period.py:32`)
Lazy wrapper exposing the most-recent period only, no comparative columns.

- `period_key -> str` — lazily calls `_detect_current_period()`. `current_period.py:59`
- `_detect_current_period() -> str` — strategy: (1) `instant_` period matching `xbrl.period_of_report`; (2) `duration_` period ending on `period_of_report`; (3) most-recent by end date; (4) first available. `current_period.py:87`
- `_get_appropriate_period_for_statement(statement_type) -> str` — maps instant statements (`BalanceSheet`, `StatementOfEquity`) to the instant period key; maps duration statements to the best-matching annual duration ending on the same date. `current_period.py:186`
- `balance_sheet(raw_concepts, as_statement, include_dimensions)` — dispatches to `_get_statement_object` or `_get_statement_dataframe`. `current_period.py:279`
- Same pattern for `income_statement`, `cashflow_statement`, `statement_of_equity`, `comprehensive_income`. `current_period.py:312–414`

#### select_periods() (`period_selector.py:31`)
The single authoritative period selector. Three-step pipeline:

1. `_filter_by_document_date()` — drops any period ending after `xbrl.period_of_report`. Prevents future-date bugs. `period_selector.py:93`
2. Statement-type branch: `BalanceSheet/ScheduleOfInvestments/FinancialHighlights` → `_select_balance_sheet_periods()`; EQUITY_STATEMENT_TYPES → `_select_equity_statement_periods()` (which delegates to `_select_duration_periods()`); everything else → `_select_duration_periods()`.
3. `_filter_periods_with_sufficient_data()` — data-quality gate; returns candidates if gate passes, otherwise returns unfiltered candidates with a debug log (Issue #585).

Annual vs quarterly determination (`period_selector.py:246`): considers `fiscal_period == 'FY'` OR `annual_report` flag OR `document_type` in a list of annual form types (10-K, 20-F, 40-F, etc.).

- `_get_annual_periods()` — filters to 300 < days <= 400. `period_selector.py:457`
- `_score_fiscal_alignment()` — scores 100/75/50/25 for exact FY end / same-month ±15 days / adjacent month / other. `period_selector.py:492`
- `_select_quarterly_periods()` — Issue #822: if `period_of_report` available, anchors current quarter to the period whose `end_date` exactly matches it (handles irregular 16-week Q1s, 52/53-week drift); seeds prior-year comparatives using `±10-day duration tolerance + 300-400 day year gap`; standard buckets 80-100 day quarterly / 150-285 day YTD used as fallback. `period_selector.py:270`
- `_select_balance_sheet_periods()` — Issue edgartools-2sn: explicitly seeks fiscal year end dates (month+day ±5 days) to avoid them being displaced by many mid-period instants; checks up to 20 candidates. `period_selector.py:127`

#### _filter_periods_with_sufficient_data() (`period_selector.py:758`)
Data quality gate. Gets all facts once (`xbrl.facts.get_facts()`), groups by `period_key`, then for each candidate:
- Equity statements: passes with ≥ 3 statement-typed facts.
- Others: dynamic threshold = `max(10, min(richest_period * 0.4, ceiling))` where ceilings are 40/25/20 for BS/IS/CF.
- BalanceSheet also requires concept diversity ≥ `max(5, max_concepts * 0.3)`.
- Flexible essential-concept check: passes if ≥ `ceil(required_groups / 2)` pattern groups match.
- Fund statements with no defined patterns: passes with ≥ 10 facts.

#### determine_periods_to_display() (`periods.py:298`)
Legacy orchestrator that first checks for an explicit `period_filter` or named `period_view`, then delegates to `select_periods()` from `period_selector.py` (with legacy fallback logic for balance sheet date-matching). `periods.py:343`

#### CurrencyConverter (`currency.py:70`)
Dataclass initialized from an XBRL instance.

- `_detect_home_currency() -> str` — counts `iso4217:XXX` measures across all facts; returns the most common. `currency.py:101`
- `_extract_exchange_rates() -> Dict[int, ExchangeRate]` — queries `ifrs-full:AverageForeignExchangeRate` (for income statement) and `ifrs-full:ClosingForeignExchangeRate` (for balance sheet); auto-detects scale: rate > 10 → "per 100 USD" format, rate < 10 → direct. `currency.py:127`
- `to_usd(value, year, rate_type) -> Optional[float]` — `value / (rate / _rate_scale)`. `currency.py:220`
- `from_usd(value, year, rate_type) -> Optional[float]` — `value * (rate / _rate_scale)`. `currency.py:261`
- `__rich__()` — Rich table with year/average/closing columns. `currency.py:358`

#### RevenueDeduplicator (`deduplication_strategy.py:26`)
All methods are `@classmethod`.

- `deduplicate_statement_items(statement_items) -> List[Dict]` — groups by `(period, value, dim_key)` tuple; if multiple revenue concepts share the same value+dimensions, applies precedence: `RevenueFromContractWithCustomerExcludingAssessedTax`(100) > `Revenues`(90) > `SalesRevenueNet`(80) > `Revenue`(70) > `TotalRevenuesAndGains`(60). `deduplication_strategy.py:52`
- Exclusions: items with segment labels (geographic names, product category terms) are never deduplicated. `deduplication_strategy.py:182`
- Issue #604: parent items with `has_dimension_children=True` are never deduplicated against their dimensional children. `deduplication_strategy.py:239`

#### validate_balance_sheet() (`validation.py:301`)
- Two methods: (1) `Assets == TotalLiabilitiesAndEquity` combined line; (2) `Assets == Liabilities + Equity ± NCI`.
- `tolerance=1.0` absolute; `tolerance_pct=0.001` (0.1%) relative; either alone is not enough to trigger an error.
- `ValidationLevel.SECTIONS` additionally checks current+noncurrent subtotals roll up to totals.

#### FilingViewer (`viewer.py:232`)
Wraps `FilingSGML` + `FilingSummary` + `MetaLinks`.

- `financial_statements -> List[ViewerReport]` — union of `MenuCategory='Statements'` and MetaLinks `groupType='statement'`; deduped by `html_file_name`. `viewer.py:257`
- `compare(xbrl, tolerance) -> ComparisonResults` — delegates to `compare_viewer_to_xbrl()`. `viewer.py:341`
- `_resolve_currency_scaling(cr, role) -> int` — GH #807: uses XBRL `decimals` attribute on monetary facts as canonical source; falls back to R*.htm header text match. `viewer.py:618`
- `_enrich_levels_from_presentation_tree(cr, role)` — GH #799: sets `ConceptRow.level` from `presentation_trees[role].all_nodes[concept_id].depth`; normalizes minimum depth to 0. `viewer.py:679`

---

### Class hierarchy

```
RenderedStatement
  ├── header: StatementHeader
  │     └── periods: List[PeriodData]
  ├── rows: List[StatementRow]
  │     └── cells: List[StatementCell]
  │           └── formatter: CellFormatter | PreformattedValue
  └── metadata: dict

StatementResolver
  └── _cache: dict  (keyed by "type_parenthetical_category")
  └── _statement_by_*: dict indices

CurrentPeriodView
  └── xbrl: XBRL  (back-reference)

FilingViewer
  └── _filing_summary: FilingSummary
  └── _metalinks: MetaLinks
  └── _viewer_reports_cache: dict
  └── concepts: ConceptGraph  (lazy cached_property)

ViewerReport
  └── _report: FilingSummary.Report
  └── _meta: Optional[MetaLinksReport]
  └── _concept_report: Optional[ConceptReport]
  └── _viewer: Optional[FilingViewer]  (back-ref for lazy enrichment)

ValidationResult
  └── issues: List[ValidationIssue]

ComparisonResults
  └── results: List[ComparisonResult]

CurrencyConverter (dataclass)
  └── exchange_rates: Dict[int, ExchangeRate]

FundStatements
  └── xbrl: XBRL
```

**Enums/registries:**
```
StatementCategory(Enum): FINANCIAL_STATEMENT | NOTE | DISCLOSURE | DOCUMENT | OTHER
ValidationLevel(str, Enum): FUNDAMENTAL | SECTIONS | DETAILED
ValidationSeverity(str, Enum): ERROR | WARNING | INFO
EQUITY_STATEMENT_TYPES (frozenset): StatementOfEquity, ComprehensiveIncome + aliases
```

---

### Configuration & options

| Option | Type | Default | Effect |
|---|---|---|---|
| `render_statement(..., standard)` | bool | `True` | Applies concept-label standardization via `standardization` module |
| `render_statement(..., show_date_range)` | bool | `False` | Shows "Jan 1 - Mar 31, 2024" instead of "Mar 31, 2024" for duration columns |
| `render_statement(..., show_comparisons)` | bool | `True` | Adds ▲/▼/• percent-change indicators (IncomeStatement + CashFlowStatement only) |
| `render_statement(..., include_dimensions)` | bool | `False` | When True passes all dimensional items through; when False filters breakdown dimensions |
| `render_statement(..., view)` | `StatementView` | None | SUMMARY=no dimensions, STANDARD=no breakdowns, DETAILED=all dimensions |
| `COMPARISON_CONFIG['threshold']` | float | `0.01` | Min 1% change to show a comparison indicator |
| `COMPARISON_CONFIG['enabled_types']` | list | `['IncomeStatement', 'CashFlowStatement']` | Only these types get comparison arrows |
| `EDGAR_FINANCIALS_COLOR_SCHEME` (env var) | str | `"filing"` | Selects terminal color scheme from `edgar.entity.terminal_styles` |
| `select_periods(..., max_periods)` | int | `4` | Maximum periods returned |
| `validate_balance_sheet(..., tolerance)` | float | `1.0` | Absolute dollar tolerance for equation check |
| `validate_balance_sheet(..., tolerance_pct)` | float | `0.001` | Percentage tolerance for equation check |
| `compare_viewer_to_xbrl(..., tolerance)` | float | `1.0` | Max allowed difference in display units |
| `CurrentPeriodView.balance_sheet(raw_concepts)` | bool | `False` | Preserves `us-gaap:Assets` names instead of standardized "Assets" |
| `CurrentPeriodView.*.include_dimensions` | bool | `False` | Pass-through to dimension filter |
| `CurrencyConverter(xbrl, target_currency)` | str | `"USD"` | Target currency for conversion |
| `VALIDATION_THRESHOLD` (module constant) | float | `0.5` | Min fraction of essential concept groups required for statement validation |
| Annual period bucket | — | 300 < days ≤ 400 | `_is_annual_period()` in `period_selector.py:472` |
| Quarterly period bucket | — | 80–100 days | `_select_quarterly_periods()` in `period_selector.py:334` |
| YTD period bucket | — | 150–285 days | `_select_quarterly_periods()` in `period_selector.py:337` |
| Prior-year quarterly match | — | Same month ±15 days, prior year | `period_selector.py:413` |
| Fiscal year end ±5 days | — | 5 days | Balance sheet fiscal-end seeking in `period_selector.py:159` |

---

### Data flow / lifecycle

**Statement rendering pipeline:**

1. Caller invokes `xbrl.statements.income_statement()` (or similar). `Statement` calls `XBRL.get_statement(type, period_filter)` to obtain raw statement data (`List[Dict]`).
2. `Statement.render()` calls `render_statement(statement_data, periods_to_display, ...)`. Periods are determined by `determine_periods_to_display()` → `select_periods()`.
3. `render_statement()` filters structural elements, applies view-based dimension filtering, optionally standardizes labels, computes `dominant_scale` (most common `decimals` attribute value across monetary facts), assembles `RenderedStatement`.
4. `RenderedStatement.__rich__()` / `to_markdown()` / `to_dataframe()` / `to_dict()` produce the final output.

**Period selection pipeline:**

1. `select_periods(xbrl, statement_type)` immediately calls `_filter_by_document_date()` — always, unconditionally.
2. For balance sheets: `_select_balance_sheet_periods()` builds up to 20 instant-period candidates, prioritizing FY-end dates by `(month == FY_month and |day - FY_day| ≤ 5)`.
3. For income/cash flow: `_select_duration_periods()` checks `is_annual` flag; if annual, collects durations 300-400 days and scores by fiscal alignment; if quarterly, uses `period_of_report` anchor logic + bucket fallback.
4. `_filter_periods_with_sufficient_data()` gates candidates using dynamic thresholds (40% of richest period, capped). Returns candidates if gate passes; falls back to candidates on complete failure.
5. Legacy `determine_periods_to_display()` in `periods.py` first handles explicit `period_filter`/`period_view` overrides, then delegates to `select_periods()`.

**Viewer pipeline:**

1. `Filing.viewer()` constructs `FilingViewer(sgml, filing_summary, metalinks)`.
2. `financial_statements` (cached_property) merges `FilingSummary` Statements category with MetaLinks `groupType='statement'`.
3. Each `ViewerReport.concept_rows` access lazily triggers `_enrich_levels_from_presentation_tree()` to fix HTML hierarchy from XBRL linkbase.
4. Each `ViewerReport.currency_scaling` access lazily triggers `_resolve_currency_scaling()` using XBRL `decimals` attribute, falling back to R*.htm header text.

**Currency detection:**
`CurrencyConverter.__post_init__()` → `_detect_home_currency()` (count `iso4217:XXX` across all facts) → `_extract_exchange_rates()` (query IFRS average/closing rate concepts) → auto-detect scale.

**Deduplication:** Called on statement data before rendering. Groups items by `(period, value, dim_key)`. Only fires on revenue concepts; preserves segment-labeled items and parent+dimensional-child pairs.

---

### Design patterns

- **Cascade/Strategy (StatementResolver)**: 6 ordered matching strategies with minimum confidence thresholds. Each strategy returns `(stmts, role, confidence)`. The cascade short-circuits at first strategy that clears its threshold and passes essential-concept validation. `statement_resolver.py:1143`
- **Registry + factory (statement_registry)**: 12 `StatementType` entries keyed by PascalCase name, each carrying primary concepts, alternative concepts, regex patterns, key concepts, role patterns, and weight maps. Used by all matching strategies.
- **Picklable formatter callables (CellFormatter, PreformattedValue)**: Replaces lambda closures to allow `RenderedStatement` to be pickled. `CellFormatter.__slots__` holds all parameters; `PreformattedValue` holds a pre-computed string. `rendering.py:187–228`
- **Lazy + cached properties (FilingViewer)**: `@cached_property` for `financial_statements`, `notes`, `policies`, `tables`, `details`, `cover`, `all_reports`, `concepts`. XBRL parsing is separately lazy via `_xbrl_loaded` guard. `viewer.py:257–307`
- **Dynamic thresholds (period_selector.py)**: Adaptive data-quality thresholds derived from the filing's own richest-period fact counts (40% of richest, bounded). Prevents both over-restriction on small companies and under-restriction on large ones. `period_selector.py:560`
- **Anchor-first + bucket-fallback (quarterly selection)**: `period_of_report` is the canonical anchor; bucket-based (80-100 day) logic is a fallback. Anchored prior-year matching uses duration-±10-day tolerance instead of the fixed bucket. Issue #822. `period_selector.py:296`
- **Fallback deduplication (StatementResolver special cases)**: `IncomeStatement → ComprehensiveIncome` and `ComprehensiveIncome → StatementOfEquity` fallbacks handle pre-2015 filing conventions where these statements were combined. `statement_resolver.py:1173`

---

### Cross-domain interactions

**Imports from other edgar.* modules:**
- `edgar.xbrl.core`: `determine_dominant_scale`, `format_date`, `format_value`, `parse_date`, `get_currency_symbol`, `get_unit_display_name`, `is_point_in_time`
- `edgar.xbrl.standardization`: `standardize_statement_data`, `get_default_mapper`, `standardize_statement`
- `edgar.xbrl.dimensions`: `is_breakdown_dimension`
- `edgar.xbrl.presentation`: `StatementView`
- `edgar.xbrl.statements`: `is_xbrl_structural_element`, `statement_to_concepts`, `Statements`
- `edgar.xbrl.exceptions`: `StatementNotFound`
- `edgar.xbrl.models`: `ElementCatalog`
- `edgar.xbrl.facts`: `FactsView` (via `xbrl.facts`)
- `edgar.sgml.metalinks`: `MetaLinks`, `MetaLinksReport`
- `edgar.sgml.concept_extractor`: `ConceptReport`, `extract_concepts_from_report`, `parse_numeric`
- `edgar.sgml.filing_summary`: `FilingSummary`, `Report`
- `edgar.entity.terminal_styles`: `get_color_scheme` (optional; falls back gracefully)
- `edgar.display`: `get_statement_styles`, `get_style`, `SYMBOLS`
- `edgar.documents`: `HTMLParser`, `ParserConfig`
- `edgar.config`: `VERBOSE_EXCEPTIONS`

**Consumed by:**
- `edgar.xbrl.xbrl.XBRL`: calls `StatementResolver`, `render_statement`, `select_periods`/`determine_periods_to_display`, `CurrentPeriodView`, `FundStatements`
- `edgar.xbrl.statements.Statement`: calls `render_statement`
- `edgar.financials.*`: wraps `Statement` objects produced here
- `edgar.entity.*`: accesses `RenderedStatement` for display

---

### Gotchas & notable behaviors

**Period selection:**

- **Future-date bug (fixed)**: Without the mandatory `_filter_by_document_date()` call, filings with restated or amended data could select periods from 2026-2029. `period_selector.py:43` now always applies this filter first.
- **Quarterly fiscal-year detection**: GE 2015 10-K reports `fiscal_period='Q4'` even for an annual report. The selector handles this via the `annual_report` boolean flag and `document_type` check in addition to `fiscal_period`. `period_selector.py:246`
- **Irregular quarters (52/53-week fiscal years)**: AAPL's fiscal year ends on the last Saturday of September, creating quarters of 91, 91, 91, 92 days — outside the 80-100 day bucket. Issue #822 anchor logic handles this; prior-year matching uses duration ±10 days instead of month/day. `period_selector.py:354`
- **Balance sheet mid-period instants**: Companies like VENU (10-Q) file with 10+ interim instant dates that push the prior FY-end beyond the initial candidate pool. Issue edgartools-2sn raised the candidate pool from 10 to 20 and added explicit FY-end seeking. `period_selector.py:169`
- **Equity statement periods**: SEC Regulation S-X Rule 3-04 requires 3 years of equity analysis. Equity statements use duration-period selection (same as income statements) but the rendering layer merges instant facts (beginning/ending balances) into the duration columns. `period_selector.py:199`

**Statement resolution:**

- **ESSENTIAL_CONCEPTS validation in cascade**: Every cascade step that passes confidence runs `_validate_statement()` against the presentation tree's actual nodes. A role can have the right abstract concept name but wrong content (Issue #659: MTD has `StatementOfFinancialPositionAbstract` but only contains Schedule II). `statement_resolver.py:1158`
- **IncomeStatement vs ComprehensiveIncome**: Many filings have only a combined P&L+OCI statement. The resolver falls back and validates the ComprehensiveIncome candidate against IncomeStatement essential concepts (requires Revenue). Issue #608 prevents picking a pure-OCI statement. `statement_resolver.py:1176`
- **Pre-2015 OCI in equity**: IBM 2010, GE 2010, Apple 2010-2012 embed OCI in their equity statements using roll-forward concepts. The resolver detects CI indicator concepts (`us-gaap_ComprehensiveIncomeNetOfTax`, etc.) in StatementOfEquity candidates. `statement_resolver.py:1208`
- **Tax disclosure false positives**: `IncomeTaxBenefitProvisionFromContinuingOperationsDetails` can match IncomeStatement role patterns. The scoring function applies -100 penalty to `incometax`/`taxbenefit`/`taxprovision`/`taxexpense`/`deferredtax` in role definitions. `statement_resolver.py:793`
- **_ENUM_TO_REGISTRY**: `xbrl.get_statement(StatementType.INCOME_STATEMENT)` (enum value `"income_statement"` snake_case) is normalized to `"IncomeStatement"` at the resolver's entry point. `statement_resolver.py:1104`

**Rendering:**

- **preferred_sign**: Applied to `IncomeStatement`, `CashFlowStatement`, and `BalanceSheet` (Issue #568 extended it for contra accounts like Treasury Stock). Negates values where `preferredLabel` in the presentation linkbase demands it. `rendering.py:1342`
- **Statement of Equity instant/duration merge**: Instant facts (beginning/ending stockholders' equity) are looked up using `instant_{day_before_start_date}` for beginning and `instant_{end_date}` for ending. `rendering.py:1886`
- **Roll-forward balance rendering (edgartools-0609)**: General roll-forward rows (e.g., cash flow's "Cash, beginning/ending balances") now correctly resolve instant facts against duration columns. Beginning balance = `instant_{day_before_period_start}`; ending balance = `instant_{period_end_date}`. Only fires for non-dimensional rows with a `periodStart`/`periodEnd` preferred label. `rendering.py:1921`
- **Empty string periods**: A period may have contexts but all fact values are empty strings (Issue #408). `_filter_empty_string_periods()` removes such periods before building the header. `rendering.py:1421`
- **fiscal_period_indicator**: Dynamically generated from duration lengths in the selected periods: "Three Months Ended", "Year Ended", "Three and Nine Months Ended", etc. `rendering.py:932`

**Currency:**

- `CurrencyConverter` only works for IFRS filers that report `ifrs-full:AverageForeignExchangeRate` or `ifrs-full:ClosingForeignExchangeRate`. US-GAAP filers will always return `home_currency="USD"`.
- Rate scale auto-detection: rates > 10 assumed to be "per 100 USD" (DKK pattern); rates < 10 assumed direct (EUR pattern). `currency.py:207`

**Viewer validation:**

- The viewer is treated as ground truth (SEC's authoritative rendering). Signs may differ between viewer and XBRL (presentation sign vs. stored sign); the match check accepts `abs(viewer) ≈ abs(xbrl)` to avoid sign-flip false mismatches. `viewer_validation.py:432`
- Only the first occurrence of each concept per report is compared (subsequent occurrences are dimensional breakdowns sharing the same concept ID). `viewer_validation.py:394`
- Currency scaling is resolved from XBRL `decimals` attributes (GH #807) rather than R*.htm header text parsing, which silently fails on non-Apple formatting.

**Deduplication:**

- Only fires on revenue-family concepts. Detected via `REVENUE_RELATED_CONCEPTS` set + label keywords. `deduplication_strategy.py:42`
- Geographic/product segment items with the same value as total revenue are explicitly preserved via `_has_segment_labels()` check. `deduplication_strategy.py:182`

**Presentation arc deduplication (GH-825):**

- `PresentationParser._build_presentation_subtree()` now deduplicates sibling arcs pointing to the same concept. When a filer emits two arcs from the same parent to the same child (different `order` values), only the first (lowest order) arc is kept. `parsers/presentation.py:243`
- **Roll-forward exemption**: `periodStart`/`periodEnd` preferred-label arcs are never deduplicated — the same concept appears twice intentionally (beginning and ending balance). `parsers/presentation.py:250`

**Abstract detection:**

- Standard taxonomy schemas are not parsed by edgartools (only company-specific XSD). `is_abstract_concept()` uses: schema flag → `KNOWN_ABSTRACT_CONCEPTS` set → regex patterns (`*Abstract`, `*RollForward`, `*Table`, `*Axis`, `*Domain`, `*LineItems`) → structural heuristic (has children + no values). `abstract_detection.py:77`

**Fund statements:**

- `FundStatements.is_fund_filing()` checks for `financialhighlights` or `consolidatedscheduleofinvestments` in role URIs, then checks element catalog for `us-gaap_NetAssetValuePerShare`. Caches result. `fund_statements.py:70`
- `ScheduleOfInvestments` facts are properly tagged with `statement_type`; `FinancialHighlights` facts are not — the period selector uses concept-based gathering for `FinancialHighlights` as a fallback. `period_selector.py:688`
