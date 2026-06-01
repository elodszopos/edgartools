## XBRL Stitching, Analysis & Synonyms

### Overview

This domain merges financial statements from multiple XBRL filings of the same company into a unified multi-period view ("stitching"), computes standardized financial ratios and alternative fraud/health metrics over the stitched or single-filing data, and manages a registry of synonym groups that map canonical concept names (e.g., `revenue`) to the set of XBRL tags a company might use for that concept. The three sub-domains work together: stitching produces the multi-period DataFrames consumed by ratio analysis, and both stitching and `EntityFacts.get_concept()` draw on the synonym/standardization layer for concept resolution.

---

### Public API Surface

| Symbol | file:line | Purpose |
|---|---|---|
| `XBRLS` | `edgar/xbrl/stitching/xbrls.py:20` | Top-level class: holds a list of `XBRL` objects, provides `statements`, `facts`, `query()`, `get_statement()`, `render_statement()`, `to_dataframe()`, `get_periods()` |
| `XBRLS.from_filings(filings, filter_amendments=True)` | `xbrls.py:49` | Factory: build from `Filings` collection or plain list |
| `XBRLS.from_xbrl_objects(xbrl_list)` | `xbrls.py:89` | Factory: build from pre-parsed `XBRL` list |
| `StatementStitcher` | `edgar/xbrl/stitching/core.py:58` | Core stitching engine; combines raw statement dicts into single multi-period dict |
| `stitch_statements(xbrl_list, ...)` | `core.py:949` | Module-level convenience function; creates `StatementStitcher` and calls stitching pipeline |
| `determine_optimal_periods(xbrl_list, statement_type, max_periods, include_quarterly)` | `edgar/xbrl/stitching/periods.py:582` | Public function: selects best-matching periods from each filing |
| `StitchedFactsView` | `edgar/xbrl/stitching/query.py:28` | Lazy view over stitched statement facts; entry point for `.query()` |
| `StitchedFactQuery` | `edgar/xbrl/stitching/query.py:249` | Fluent query builder extending `FactQuery`; multi-period filtering, trend analysis, `to_dataframe()`, `to_trend_dataframe()` |
| `render_stitched_statement(stitched_data, ...)` | `edgar/xbrl/stitching/utils.py:13` | Delegates to `edgar.xbrl.rendering.render_statement` for Rich table output |
| `to_pandas(stitched_data, presentation=True)` | `edgar/xbrl/stitching/utils.py:60` | Converts stitched dict to `pd.DataFrame` (concepts × periods) |
| `FinancialRatios` | `edgar/xbrl/analysis/ratios.py:259` | Computes all ratio groups from a single XBRL instance |
| `FinancialMetrics` | `edgar/xbrl/analysis/metrics.py:27` | Base class for score-based metrics |
| `AltmanZScore` | `edgar/xbrl/analysis/metrics.py:108` | Altman Z-Score bankruptcy prediction |
| `BeneishMScore` | `edgar/xbrl/analysis/metrics.py:186` | Beneish M-Score earnings manipulation detection |
| `PiotroskiFScore` | `edgar/xbrl/analysis/metrics.py:288` | Piotroski F-Score financial strength |
| `FraudDetector` | `edgar/xbrl/analysis/fraud.py:31` | Aggregates all three metrics + Benford's Law |
| `MetricResult` | `metrics.py:17` | Dataclass: `value`, `components`, `interpretation`, `period` |
| `BenfordResult` | `fraud.py:20` | Dataclass: digit distribution analysis result |
| `SynonymGroups` | `edgar/standardization/synonym_groups.py:858` | Registry of 40+ canonical concept → XBRL tag synonym groups |
| `SynonymGroup` | `synonym_groups.py:67` | Single group: `name`, `synonyms`, `description`, `namespace`, `priority_order`, `category` |
| `ConceptInfo` | `synonym_groups.py:171` | Result of reverse lookup: `name`, `tag`, `group`, `match_type` |
| `get_synonym_groups()` | `synonym_groups.py:1293` | Module-level singleton accessor |

---

### Key Classes

#### XBRLS (`edgar/xbrl/stitching/xbrls.py:20`)

Holds an ordered list of `XBRL` objects (newest first) for the same company.

- `from_filings(filings, filter_amendments=True) -> XBRLS` — sorts by `filing_date` desc, drops `/A` amendment forms, calls `XBRL.from_filing()` for each; silently skips failures — `xbrls.py:49`
- `from_xbrl_objects(xbrl_list) -> XBRLS` — direct constructor from pre-parsed list — `xbrls.py:89`
- `statements -> StitchedStatements` — lazy property returning `StitchedStatements(self)` — `xbrls.py:102`
- `facts -> StitchedFactsView` — lazy property, cached in `_stitched_facts_view` — `xbrls.py:113`
- `query(max_periods=8, standardize=True, statement_types=None, **kwargs) -> StitchedFactQuery` — delegates to `self.facts.query()` — `xbrls.py:124`
- `get_statement(statement_type, max_periods=8, standard=True, use_optimal_periods=True, include_dimensions=False, discrete_quarters=False, include_quarterly=False) -> Dict` — core workhorse; caches by key string; calls `stitch_statements()` — `xbrls.py:149`
- `render_statement(statement_type, ...) -> RichTable` — creates `StitchedStatement` and calls its `render()` — `xbrls.py:199`
- `to_dataframe(statement_type, max_periods=8, standardize=True) -> pd.DataFrame` — via `StitchedStatement.to_dataframe()` — `xbrls.py:224`
- `get_periods() -> List[Dict]` — unions all `xbrl.reporting_periods` across filings, de-duplicates — `xbrls.py:243`
- `get_period_end_dates() -> List[str]` — convenience method returning `YYYY-MM-DD` strings newest first — `xbrls.py:276`

Cache: `_statement_cache` dict keyed by `f"{statement_type}_{max_periods}_{standard}_{use_optimal_periods}_{include_dimensions}_{discrete_quarters}_{include_quarterly}"`.

---

#### StatementStitcher (`edgar/xbrl/stitching/core.py:58`)

Stateful engine that stitches a list of raw statement dicts (one per filing period) into one unified dict.

Inner class:
- `PeriodType(str, Enum)` — `RECENT_PERIODS`, `RECENT_YEARS`, `THREE_YEAR_COMPARISON`, `THREE_QUARTERS`, `ANNUAL_COMPARISON`, `QUARTERLY_TREND`, `ALL_PERIODS` — `core.py:70`

Constructor: `__init__(self, industry=None)` — `industry` is a Fama-French 48 code used for industry-specific standardization overrides — `core.py:80`

Primary method:
- `stitch_statements(statements, period_type, max_periods, standard=True, discrete_quarters=False) -> Dict` — full pipeline: reset state → extract+sort periods → select by period_type → per-statement standardize+integrate → merge duplicates → merge renames → optionally unaccumulate YTD cash flows → format output with ordering — `core.py:99`

Internal pipeline steps:
- `_extract_periods(statements) -> List[(period_id, end_date)]` — builds `unique_periods` dict keyed by normalized period key (`instant_YYYY-MM-DD` or `duration_YYYY-MM-DD_YYYY-MM-DD`), de-duplicates favouring more recent filing index — `core.py:187`
- `_select_periods(all_periods, period_type, max_periods) -> List[str]` — routes by `PeriodType` enum; `ALL_PERIODS` returns top `max_periods` newest; `THREE_QUARTERS` filters durations 80-95 days; `ANNUAL_COMPARISON` filters 350-380 days — `core.py:269`
- `_standardize_statement_data(statement) -> List[Dict]` — calls `standardize_statement(data, None, industry=self.industry)` from `edgar.xbrl.standardization` — `core.py:376`
- `_integrate_statement_data(statement_data, period_map, relevant_periods)` — merges items into `self.data[concept_key][period_id]`; uses concept as primary key (not label); skips `[Axis]`/`[Domain]`/`[Member]`/`[Abstract]` structural items, skips `is_dimension=True` rows; stores `latest_label` from most recent filing — `core.py:396`
- `_merge_duplicate_standard_concepts()` — groups concepts by `standard_concept`; pairwise merges where bare names are variants (one contains the other) AND overlapping period values agree within 0.1% tolerance; handles `_EQUIVALENT_STANDARD_CONCEPTS` (e.g., `CashAndCashEquivalents` + `CashAndMarketableSecurities`) — `core.py:593`
- `_merge_known_concept_renames()` — merges concept pairs in `_KNOWN_CONCEPT_RENAMES` (currently: PG FY2024 pre-tax income rename); same value-agreement safety check — `core.py:662`
- `_unaccumulate_cashflow_ytd()` — derives discrete quarter values from YTD cumulative cash flow periods; groups durations by `start_date`; subtracts adjacent shorter from longer (Q2=6M-Q1, Q3=9M-6M, Q4=12M-9M); updates period labels from `"Q2 YTD"` to `"Q2"` — `core.py:705`
- `_format_output_with_ordering(statements) -> Dict` — calls `StatementOrderingManager.determine_ordering()`, builds `VirtualPresentationTree`, flattens to ordered concepts list; output format: `{periods: [(pid, label), ...], statement_data: [...]}` — `core.py:869`

Module-level constants:
- `_EQUIVALENT_STANDARD_CONCEPTS` — list of tuples declaring economically-equivalent standard concepts — `core.py:24`
- `_KNOWN_CONCEPT_RENAMES` — list of `(old_bare_name, new_bare_name)` pairs for company-specific cross-year renames — `core.py:43`

Module-level function:
- `stitch_statements(xbrl_list, statement_type, period_type, max_periods=3, standard=True, use_optimal_periods=True, include_dimensions=False, industry=None, discrete_quarters=False, include_quarterly=False) -> Dict` — auto-detects industry from first XBRL's `standardization.industry`; if `use_optimal_periods=True`, calls `determine_optimal_periods()` and builds filtered one-period-per-statement dicts with enriched period labels (`"FY 2024-09-28"`, `"Q2 YTD 2024-06-30"`, etc.) — `core.py:949`

---

#### Period Optimization (`edgar/xbrl/stitching/periods.py`)

Clean class-based architecture coordinated by `PeriodOptimizer`:

- `PeriodSelectionConfig` (dataclass) — duration ranges for annual (350-380d), quarterly (80-100d), Q2 YTD (175-190d), Q3 YTD (260-285d); target days (365/90/180/270); flags `require_exact_matches`, `allow_fallback_when_no_doc_date`; `max_periods_default=8` — `periods.py:24`
- `PeriodMatcher` — exact instant/duration matching by date; `filter_by_duration_range()` with proximity sort — `periods.py:46`
- `FiscalPeriodClassifier` — classifies annual/quarterly/YTD periods by duration range — `periods.py:101`
- `StatementTypeSelector` — `select_balance_sheet_periods()` (instant only, exact doc_period_end_date match, no fallback); `select_income_statement_periods()` / `select_cash_flow_periods()` (duration, exact end-date match, then `_select_appropriate_durations()`); when `include_quarterly=True` surfaces both Q period and YTD period — `periods.py:185`
- `PeriodMetadataEnricher` — adds `xbrl_index`, `period_key`, `display_date`, `duration_days` to each period — `periods.py:370`
- `PeriodDeduplicator` — exact date dedup (instant: same date; duration: same start AND end); sort by `date` (BalanceSheet) or `end_date` (others); limit to `max_periods` — `periods.py:402`
- `PeriodOptimizer` — orchestrates all five components; `determine_optimal_periods(xbrl_list, statement_type, max_periods, include_quarterly)` — `periods.py:448`

Key design decision (GH#475): For quarterly filings where both 90-day and YTD periods exist, the default (no `include_quarterly`) selects the YTD period (longer = more likely to have full tagging data, e.g., PYPL); `include_quarterly=True` (GH#780) surfaces both.

---

#### Ordering (`edgar/xbrl/stitching/ordering.py`)

Three-strategy layered ordering with section-integrity enforcement:

- `FinancialStatementTemplates` — canonical XBRL concept templates for `INCOME_STATEMENT_TEMPLATE` (10 sections, 0-999 range: revenue→cost→gross profit→opex→op income→non-operating→pretax→tax→net income→per share) and `BALANCE_SHEET_TEMPLATE` (5 sections: current assets/non-current assets/current liabilities/non-current liabilities/equity); `get_template_position(item_concept, item_label, statement_type)` — concept-match first (using `_normalize_xbrl_concept()`), label fuzzy-match fallback — `ordering.py:32`
- `ReferenceOrderingStrategy` — uses most-recent filing's natural order as fallback for non-template concepts — `ordering.py:358`
- `SemanticPositioning` — keyword-based section classification then section-end insertion; `infer_position()` cascades: rule-based → parent-child → similarity → default 999.0 — `ordering.py:384`
- `StatementOrderingManager` — orchestrates: (1) template → (2) reference → (3) semantic → (4) section-aware consolidation that prevents cross-section hierarchies (per-share items forced to 950+) — `ordering.py:556`

Uses `rapidfuzz.fuzz.ratio` (or `difflib.SequenceMatcher` fallback) for fuzzy label matching with 0.7 threshold.

---

#### VirtualPresentationTree (`edgar/xbrl/stitching/presentation.py`)

Preserves parent-child indentation hierarchy while applying semantic ordering within sibling groups.

- `PresentationNode` (dataclass) — `concept`, `label`, `level`, `metadata`, `semantic_order`, `original_index`; `add_child()`, `sort_children()` (recursive), `flatten_to_list()` — `presentation.py:13`
- `VirtualPresentationTree.build_tree(concept_metadata, concept_ordering, original_statement_order)` — pipeline: create nodes → build hierarchy via parent stack (pops stack on same/deeper level) → apply semantic ordering within sibling groups → flatten — `presentation.py:57`
- `_should_be_hierarchical_child(parent, child)` — prevents cross-section hierarchies: section gap >200 → reject; per-share items (900+) not children of early items (<800); non-operating (500-599) not children of operating; interest expense not child of non-interest — `presentation.py:193`

---

#### StitchedFactsView and StitchedFactQuery (`edgar/xbrl/stitching/query.py`)

- `StitchedFactsView(xbrls)` — lazy fact extraction from stitched statements; `get_facts(max_periods=8, standard=True, statement_types=None) -> List[Dict]` iterates over 5 statement types, calls `xbrls.get_statement()`, converts to fact records; each fact record includes `concept`, `label`, `original_label`, `standard_concept`, `value`, `numeric_value`, `period_key/type/start/end/instant/label`, `level`, `is_abstract`, `is_total`, `filing_count`, `standardized=True`, `source_filing_index` — `query.py:28`; cache keyed by `(max_periods, standard, tuple(statement_types))`
- `StitchedFactQuery(StitchedFactsView, **kwargs)` — extends `FactQuery`; stores `_max_periods`, `_standard`, `_statement_types`; extra filter methods:
  - `by_standardized_concept(concept_name)` — case-insensitive substring on `label` or `concept` — `query.py:289`
  - `by_original_label(pattern, exact=False)` — regex on `original_label` — `query.py:307`
  - `across_periods(min_periods=2)` — post-filter to concepts in ≥N periods — `query.py:327`
  - `by_fiscal_period(fiscal_period)` — filter on `fiscal_period` field — `query.py:341`
  - `by_filing_index(filing_index)` — filter on `source_filing_index` — `query.py:356`
  - `trend_analysis(concept)` — sets `_trend_analysis=True` + concept filter; results sorted by `period_end` — `query.py:371`
  - `complete_periods_only()` — only concepts present in ALL periods — `query.py:385`
  - `to_trend_dataframe()` — pivots on `(label, concept)` × `period_end` — `query.py:518`

---

#### FinancialRatios (`edgar/xbrl/analysis/ratios.py:259`)

Operates on a single `XBRL` instance; converts rendered statements to DataFrames at construction.

Constructor: `__init__(self, xbrl)` — calls `xbrl.statements.balance_sheet()`, `.income_statement()`, `.cashflow_statement()`, renders each, stores `balance_sheet_df`, `income_stmt_df`, `cash_flow_df`; computes union of `periods` across all three — `ratios.py:262`

Internal infrastructure:
- `ConceptEquivalent` (dataclass) — fallback calculation: `target_concept`, `required_concepts`, `calculation: Callable[[pd.DataFrame, str], float]`, `description` — `ratios.py:98`
- `RatioData` (dataclass) — `calculation_df`, `periods`, `equivalents_used`, `required_concepts`, `optional_concepts`; `has_concept(concept)`, `get_concept(concept, default_value=None)`, `get_concepts(concepts)` — `ratios.py:139`
- `RatioAnalysis` (dataclass) — `name`, `description`, `calculation_df`, `results: pd.Series`, `components: Dict[str, pd.Series]`, `equivalents_used`; `__rich__()` renders Rich panel — `ratios.py:222`
- `RatioAnalysisGroup` (dataclass) — groups related `RatioAnalysis` objects; `__rich__()` renders table panel — `ratios.py:107`

`_initialize_concept_equivalents()` — builds fallback chains for `GROSS_PROFIT` (4 fallbacks: CostOfRevenue, COGS, CostOfSales, CostsAndExpenses), `OPERATING_INCOME` (1: GrossProfit-OpEx), `REVENUE` (3: Product+Service, ContractRevenue, ProductRevenue), `COST_OF_REVENUE` (3: COGS, CostOfSales, mixed) — `ratios.py:415`

`_prepare_ratio_df(required_concepts, statement_dfs, optional_concepts)` — searches by `MappingStore` mappings first, then direct concept match, then label substring match, then `_concept_equivalents`; returns `(calc_df, equivalents_used)` — `ratios.py:294`

`get_ratio_data(ratio_type)` — pre-defined configs for `'current'`, `'operating_margin'`, `'return_on_assets'`, `'gross_margin'`, `'leverage'`, `'profitability'`, `'efficiency'`; returns `RatioData` — `ratios.py:607`

Ratio calculation methods (all return `RatioAnalysis` unless noted):
- `calculate_current_ratio()` — Current Assets / Current Liabilities — `ratios.py:739`
- `calculate_quick_ratio()` — (Current Assets - Inventory) / Current Liabilities; inventory defaults to 0 if missing — `ratios.py:881`
- `calculate_cash_ratio()` — Cash / Current Liabilities — `ratios.py:932`
- `calculate_working_capital()` — Current Assets - Current Liabilities — `ratios.py:967`
- `calculate_return_on_assets()` — Net Income / Average Total Assets (uses shifted average) — `ratios.py:772`
- `calculate_operating_margin()` — Operating Income / Revenue — `ratios.py:810`
- `calculate_gross_margin()` — Gross Profit / Revenue — `ratios.py:844`
- `calculate_profitability_ratios() -> RatioAnalysisGroup` — gross_margin, operating_margin, net_margin, return_on_assets, return_on_equity — `ratios.py:1004`
- `calculate_efficiency_ratios() -> RatioAnalysisGroup` — asset_turnover, inventory_turnover (if inventory present), receivables_turnover, days_sales_outstanding (if receivables present) — `ratios.py:1111`
- `calculate_leverage_ratios() -> RatioAnalysisGroup` — debt_to_equity, debt_to_assets, interest_coverage (if interest expense present), equity_multiplier — `ratios.py:1216`
- `calculate_liquidity_ratios() -> RatioAnalysisGroup` — bundles current, quick, cash, working_capital — `ratios.py:1320`
- `calculate_all() -> Dict` — calls all four group methods — `ratios.py:1341`

Helper functions (module level): `_clean_series_data(series)` — replaces empty strings with NaN, coerces to numeric — `ratios.py:25`; `_safe_divide(num, denom)` — NaN/zero-safe division — `ratios.py:54`; `_safe_subtract(a, b)` — NaN-safe subtraction — `ratios.py:76`

---

#### FinancialMetrics base class (`edgar/xbrl/analysis/metrics.py:27`)

`__init__(self, xbrl)` — initializes `_balance_sheet_df`, `_income_stmt_df`, `_cash_flow_df` from `xbrl.statements.*` using `to_dataframe(presentation=False)`; stores first period label in `_bs_period`, `_is_period`, `_cf_period`; creates `MappingStore()` — `metrics.py:30`

`_get_value(label: StandardConcept, statement_type="BalanceSheet", period_offset=0) -> Optional[float]` — uses `MappingStore.get_company_concepts(label)` to get possible tags; iterates `df.loc[concept, target_period]`; `period_offset=-1` accesses prior year column — `metrics.py:59`

**AltmanZScore** (`metrics.py:108`): Z = 1.2X₁ + 1.4X₂ + 3.3X₃ + 0.6X₄ + 1.0X₅ where X₁=WorkingCapital/TotalAssets, X₂=RetainedEarnings/TotalAssets, X₃=EBIT/TotalAssets, X₄=Equity/TotalLiabilities, X₅=Sales/TotalAssets. Thresholds: >2.99 Safe, 1.81-2.99 Grey, <1.81 Distress. Returns None if any input missing.

**BeneishMScore** (`metrics.py:186`): 8-variable model requiring current AND prior year data. M = -4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI. Threshold: > -2.22 = high manipulation probability. Returns None if any of 16 inputs missing.

**PiotroskiFScore** (`metrics.py:288`): Sum of 9 binary signals: ROA>0, CFO>0, ROA improving, CFO>ROA, leverage decreasing, current ratio improving, no share dilution, gross margin improving, asset turnover improving. Score 8-9 = Strong, 5-7 = Moderate, 0-4 = Weak. Gracefully skips signals when prior-year data unavailable.

---

#### FraudDetector (`edgar/xbrl/analysis/fraud.py:31`)

Composes all three metric classes plus Benford analysis.

`__init__(self, xbrl)` — instantiates `AltmanZScore`, `BeneishMScore`, `PiotroskiFScore` — `fraud.py:34`

`analyze_digit_distribution(values: List[float], significance=0.05) -> Optional[BenfordResult]` — extracts leading digits; chi-square test against `log10(1 + 1/d)` expected distribution; 8 degrees of freedom; requires `scipy.stats.chi2`; returns None if <10 values — `fraud.py:41`

`analyze_all() -> Dict` — collects numeric values for 7 standard concepts across all 3 statements; returns `{'altman_z': MetricResult, 'beneish_m': MetricResult, 'piotroski_f': MetricResult, 'benford': BenfordResult}` — `fraud.py:86`

---

#### SynonymGroups (`edgar/standardization/synonym_groups.py:858`)

Registry manager for 40+ canonical concept → XBRL tag synonym groups.

`__init__(self, load_builtin=True)` — populates `_groups: Dict[str, SynonymGroup]`, `_tag_index: Dict[str, List[str]]` (reverse lookup; tag lowercase → list of group names for multi-group membership), `_user_groups` — `synonym_groups.py:897`

Core methods:
- `get_group(name) -> Optional[SynonymGroup]` — normalizes name (lowercase + underscores), O(1) dict lookup — `synonym_groups.py:943`
- `get_synonyms(name) -> List[str]` — returns `group.synonyms` or `[]` — `synonym_groups.py:962`
- `identify_concept(tag) -> Optional[ConceptInfo]` — reverse lookup returning first match — `synonym_groups.py:983`
- `identify_concepts(tag) -> List[ConceptInfo]` — reverse lookup returning ALL matching groups (multi-group membership support) — `synonym_groups.py:1025`
- `register_group(name, synonyms, description, namespace, priority_order, category) -> SynonymGroup` — registers user-defined group, marks as user-defined — `synonym_groups.py:1073`
- `unregister_group(name) -> bool` — only user-defined groups can be removed — `synonym_groups.py:1119`
- `list_groups(category=None) -> List[str]` — alphabetically sorted group names, optional category filter — `synonym_groups.py:1156`
- `list_categories() -> List[str]` — unique category strings — `synonym_groups.py:1179`
- `export_to_json(path, include_builtin=False)` — JSON export; user-defined only by default — `synonym_groups.py:1189`
- `import_from_json(path) -> int` — imports as user-defined groups, can override built-ins — `synonym_groups.py:1222`
- `from_file(path) -> SynonymGroups` — classmethod; loads builtin then overlays file — `synonym_groups.py:1256`

**SynonymGroup** (`synonym_groups.py:67`): `__post_init__` strips namespace prefixes (`us-gaap:`, `ifrs-full:`, `dei:`, underscore variants), deduplicates while preserving order, builds internal `_synonym_set` (lowercase) for O(1) `contains_tag()`. `get_tags_with_namespace(namespace)` prepends namespace prefix.

Built-in groups catalog (40+ groups; module-level cache `_builtin_groups_cache`):

| Category | Groups |
|---|---|
| `income_statement` | revenue, cost_of_revenue, gross_profit, operating_expenses, research_and_development, sga_expense, operating_income, interest_expense, interest_income, income_before_tax, income_tax_expense, net_income, earnings_per_share_basic/diluted, depreciation_and_amortization, ebitda |
| `balance_sheet` | cash_and_equivalents, short_term_investments, accounts_receivable, inventory, prepaid_expenses, total_current_assets, property_plant_equipment, goodwill, intangible_assets, long_term_investments, deferred_tax_assets, total_assets, accounts_payable, accrued_liabilities, short_term_debt, deferred_revenue, total_current_liabilities, long_term_debt, deferred_tax_liabilities, total_liabilities, common_stock, additional_paid_in_capital, retained_earnings, treasury_stock, accumulated_other_comprehensive_income, stockholders_equity, common_shares_outstanding, operating_lease_liability, operating_lease_right_of_use_asset, finance_lease_liability |
| `cash_flow` | operating_cash_flow, investing_cash_flow, financing_cash_flow, capex, dividends_paid, share_repurchases, debt_repayment, debt_proceeds, free_cash_flow, operating_lease_payments |
| `metrics` | book_value_per_share, return_on_equity, return_on_assets |

`get_synonym_groups() -> SynonymGroups` — module-level singleton; `_default_instance` cached after first call; `reset_synonym_groups()` clears for testing — `synonym_groups.py:1293`

---

#### How SynonymGroups is consumed by EntityFacts.get_concept

`EntityFacts.get_concept(concept_name, period=None, unit=None, return_metadata=False)` (`entity_facts.py:1080`):
1. Calls `get_synonym_groups().get_group(concept_name)` to get the `SynonymGroup`.
2. If group not found, emits `warnings.warn` with hint to call `list_supported_concepts()`.
3. Iterates `group.synonyms` in listed priority order; for each tag tries `concept`, `us-gaap:{concept}`, `ifrs-full:{concept}` via `self.get_fact(tag, period)`.
4. On first match with non-None `numeric_value`, calls `UnitNormalizer.get_normalized_value()` with `strict_unit_match` only when user explicitly specified `unit`.
5. If `return_metadata=True`, returns dict with `value`, `tag_used`, `period`, `unit`, `concept_name`, `synonyms_tried`.
6. Suppresses inner `get_fact()` warnings during synonym iteration.

`EntityFacts.list_supported_concepts(category=None)` — delegates to `get_synonym_groups().list_groups(category)` — `entity_facts.py:1339`

`EntityFacts.discover_concept_tags(concept_name)` — uses `get_synonym_groups().get_group()` to get synonyms, then checks which tags actually exist in this company's facts — `entity_facts.py:1178`

---

### Class Hierarchy

```
# Stitching
XBRLS
├── xbrl_list: List[XBRL]              # raw filings, newest-first
├── _statement_cache: Dict             # keyed by param string
└── _stitched_facts_view: StitchedFactsView (lazy)

StatementStitcher
├── ordering_manager: StatementOrderingManager
│   ├── templates: FinancialStatementTemplates
│   ├── reference_strategy: ReferenceOrderingStrategy
│   └── semantic_positioning: SemanticPositioning
└── (uses) VirtualPresentationTree
    └── nodes: List[PresentationNode]

PeriodOptimizer
├── matcher: PeriodMatcher
├── classifier: FiscalPeriodClassifier
├── selector: StatementTypeSelector
├── enricher: PeriodMetadataEnricher
└── deduplicator: PeriodDeduplicator

StitchedFactsView (xbrls: XBRLS)
└── query() → StitchedFactQuery(FactQuery)

# Analysis
FinancialMetrics (base)
├── AltmanZScore
├── BeneishMScore
└── PiotroskiFScore

FraudDetector
├── altman: AltmanZScore
├── beneish: BeneishMScore
└── piotroski: PiotroskiFScore
    (+ Benford analysis inline)

FinancialRatios (standalone, not extending FinancialMetrics)

# Synonyms
SynonymGroups
├── _groups: Dict[str, SynonymGroup]
├── _tag_index: Dict[str, List[str]]   # reverse index
└── _user_groups: Dict[str, SynonymGroup]

SynonymGroup
└── _synonym_set: Set[str]             # O(1) contains_tag

ConceptInfo
└── group: SynonymGroup
```

---

### Configuration & Options

| Option | Type | Default | Effect |
|---|---|---|---|
| `XBRLS.get_statement(max_periods)` | `int` | `8` | Max periods included in stitched output |
| `XBRLS.get_statement(standard)` | `bool` | `True` | Apply `standardize_statement()` to each filing's data |
| `XBRLS.get_statement(use_optimal_periods)` | `bool` | `True` | Use `determine_optimal_periods()` vs naive period extraction |
| `XBRLS.get_statement(include_dimensions)` | `bool` | `False` | Include dimensional (segment) rows |
| `XBRLS.get_statement(discrete_quarters)` | `bool` | `False` | Convert YTD cash flow to discrete quarter values |
| `XBRLS.get_statement(include_quarterly)` | `bool` | `False` | Surface both Q and YTD columns per 10-Q filing (GH#780) |
| `XBRLS.from_filings(filter_amendments)` | `bool` | `True` | Drop `/A` amendment forms before stitching |
| `StatementStitcher(industry)` | `Optional[str]` | `None` (auto-detected) | Fama-French 48 code for standardization overrides |
| `PeriodSelectionConfig.annual_duration_range` | `Tuple[int,int]` | `(350, 380)` | Days range for annual period classification |
| `PeriodSelectionConfig.quarterly_duration_range` | `Tuple[int,int]` | `(80, 100)` | Days range for quarterly period classification |
| `PeriodSelectionConfig.q2_ytd_range` | `Tuple[int,int]` | `(175, 190)` | Days for Q2 YTD |
| `PeriodSelectionConfig.q3_ytd_range` | `Tuple[int,int]` | `(260, 285)` | Days for Q3 YTD |
| `PeriodSelectionConfig.max_periods_default` | `int` | `8` | Default max_periods |
| `SynonymGroups(load_builtin)` | `bool` | `True` | Load the 40+ pre-built groups at construction |
| `SynonymGroup.priority_order` | `str` | `"listed"` | `"listed"` / `"frequency"` / `"specificity"` |
| `FraudDetector.analyze_digit_distribution(significance)` | `float` | `0.05` | Chi-square significance threshold for Benford anomaly |

---

### Data Flow / Lifecycle

**Stitching pipeline:**
1. `XBRLS.from_filings(filings)` sorts filings newest-first, calls `XBRL.from_filing()` for each (failures silently skipped), stores list in `xbrl_list`.
2. `XBRLS.get_statement(statement_type)` checks `_statement_cache`; on miss calls `stitch_statements(xbrl_list, ...)`.
3. `stitch_statements()`: if `use_optimal_periods=True`, calls `determine_optimal_periods()` which runs `PeriodOptimizer` to select exactly one (or two with `include_quarterly=True`) period per filing. This uses `xbrl.entity_info` (`document_period_end_date`, `fiscal_period`) for exact date matching. Creates filtered one-period statement dicts with enriched labels.
4. `StatementStitcher.stitch_statements(filtered_statements)`: iterates statements, for each calls `_standardize_statement_data()` (via `standardize_statement()` from XBRL standardization layer), then `_integrate_statement_data()` which merges into `self.data[concept_key][period_id]`.
5. After all statements: `_merge_duplicate_standard_concepts()` (handles XBRL concept-name drift within same company), then `_merge_known_concept_renames()` (handles hard-coded company-specific renames), then optionally `_unaccumulate_cashflow_ytd()`.
6. `_format_output_with_ordering()`: `StatementOrderingManager` computes float positions, `VirtualPresentationTree` builds and flattens hierarchy, produces final `{periods, statement_data}` dict.
7. Result cached in `XBRLS._statement_cache`.

**Facts query pipeline:**
- `XBRLS.facts` → lazy `StitchedFactsView`; `.query()` → `StitchedFactQuery`; `.execute()` pulls from `StitchedFactsView.get_facts()` (which calls `get_statement()` for 5 statement types and extracts per-period fact records), then applies filter chain.

**Ratio analysis:**
- `FinancialRatios(xbrl)` renders statements at construction (eager); ratio methods call `get_ratio_data(type)` which uses `_prepare_ratio_df()` to build a concepts × periods DataFrame by searching MappingStore then direct match then label then ConceptEquivalent fallbacks; ratio is then computed as vectorized pandas operations.

**Metric/fraud analysis:**
- `FinancialMetrics(xbrl)` calls `to_dataframe(presentation=False)` on statements (no sign adjustment); `_get_value(StandardConcept, period_offset)` looks up via `MappingStore.get_company_concepts()` and `df.loc[concept, period]`.
- All metric `calculate()` methods fail gracefully with `None` when required inputs are missing.

**Synonym lookup:**
- `get_synonym_groups()` returns singleton (cached via `_default_instance`); built-in groups cached via `_builtin_groups_cache` at module level (double-layer caching).
- `SynonymGroup.__post_init__` strips namespaces and builds `_synonym_set` (lowercase) for O(1) membership testing.
- Reverse index `_tag_index` is a `Dict[str, List[str]]` supporting multi-group membership.

---

### Design Patterns

- **Façade** (`XBRLS`) — single entry point hiding the complexity of `StatementStitcher`, `PeriodOptimizer`, `StatementOrderingManager`, and `VirtualPresentationTree`.
- **Template Method** (`StatementStitcher.stitch_statements`) — fixed pipeline; individual steps are overridable internal methods.
- **Chain of Responsibility** (`_prepare_ratio_df`, `_get_concept_value`) — concept lookup tries MappingStore → direct match → label match → ConceptEquivalent fallbacks in sequence.
- **Strategy** (`StatementOrderingManager`) — three ordering strategies (template, reference, semantic) applied sequentially; earlier strategies take precedence.
- **Composite + Visitor** (`VirtualPresentationTree`) — tree of `PresentationNode`s built then flattened; semantic ordering applied via visitor-style recursive `sort_children()`.
- **Singleton** (`get_synonym_groups()`) — module-level `_default_instance` with separate `_builtin_groups_cache`; `reset_synonym_groups()` for test isolation.
- **Registry** (`SynonymGroups`) — pre-built groups loaded at init; user groups registered at runtime; `export_to_json`/`import_from_json` for sharing.
- **Dataclass value objects** (`MetricResult`, `BenfordResult`, `RatioData`, `RatioAnalysis`, `RatioAnalysisGroup`, `SynonymGroup`, `ConceptInfo`) — immutable result containers with `__repr__` and `__rich__` for display.
- **Lazy property with cache** (`XBRLS.facts`, `XBRLS._statement_cache`) — expensive operations deferred and memoized.

---

### Cross-Domain Interactions

**Stitching imports from:**
- `edgar.xbrl.xbrl.XBRL` — individual filing parser (`periods.py`, `xbrls.py`)
- `edgar.xbrl.standardization.standardize_statement` — applies concept label normalization per statement (`core.py:394`)
- `edgar.xbrl.exceptions.StatementNotFound` — raised by `xbrl.get_statement_by_type()`, caught in `stitch_statements()` (`core.py:1016`)
- `edgar.xbrl.facts.FactQuery` — base class for `StitchedFactQuery` (`query.py:4`)
- `edgar.xbrl.rendering.render_statement` — Rich table rendering (`utils.py:34`)
- `edgar.xbrl.statements.StitchedStatements`, `StitchedStatement` — consumer of `XBRLS` (imported lazily in `xbrls.py:109,221`)
- `edgar.xbrl.core.format_date`, `parse_date` — date utilities (`periods.py`, `core.py`)

**Analysis imports from:**
- `edgar.xbrl.standardization.MappingStore`, `StandardConcept` — concept resolution (`metrics.py:13`, `ratios.py:22`)
- `edgar.standardization.StandardConcept` — re-exported for `fraud.py:15`

**Standardization (synonym_groups) is consumed by:**
- `edgar.entity.entity_facts.EntityFacts.get_concept()` — uses `get_synonym_groups()` to resolve canonical name → tag list → fact value (`entity_facts.py:1127`)
- `edgar.entity.entity_facts.EntityFacts.list_supported_concepts()` — delegates to `synonyms.list_groups()` (`entity_facts.py:1362`)
- `edgar.entity.entity_facts.EntityFacts.discover_concept_tags()` — uses synonyms to find which tags exist for a company (`entity_facts.py:1197`)

---

### Gotchas & Notable Behaviors

- **Amendment filtering is on by default** in `XBRLS.from_filings()`. Passing `filter_amendments=False` is needed when amended filings are intentionally included. Plain lists are filtered by `form.endswith('/A')` check (not `Filings.filter()`).

- **Dimension rows are silently dropped** in `_integrate_statement_data()`: `is_dimension=True` rows are skipped even when `include_dimensions=True` is passed to `XBRLS.get_statement()`. The stitcher uses concept as a dict key and cannot differentiate segment rows from total rows.

- **XBRL pre-2009 filings** are None in xbrl_list; `PeriodOptimizer._extract_all_periods()` explicitly skips None XBRLs.

- **Period label precedence**: The stitcher uses the label from the most recent filing when the same concept appears across multiple filings. This means older filings' labels may be superseded.

- **YTD vs. quarterly period selection** (GH#475): Default behavior selects YTD over quarterly for Q2/Q3 because many companies (e.g., PYPL) tag full detail to YTD periods. Use `include_quarterly=True` (GH#780) to get both columns.

- **Cash flow YTD unaccumulation** (`discrete_quarters=True`): Only applies to `CashFlowStatement`. Requires at least 2 periods sharing the same fiscal year start date. Non-numeric values are skipped. YTD period labels are updated in-place (e.g., `"Q2 YTD 2024-06-30"` → `"Q2 2024-06-30"`).

- **Concept merge safety**: `_merge_duplicate_standard_concepts()` only merges when bare names have a containment relationship (one is a substring of the other) AND overlapping period values agree within 0.1%. This prevents unrelated sub-items that share a standard_concept from being merged (Issue #642).

- **Known concept renames** (`_KNOWN_CONCEPT_RENAMES`): Currently contains one entry (PG FY2024 pre-tax income concept swap). This list must be manually maintained as companies switch taxonomy concepts across years.

- **`FinancialRatios` vs `FinancialMetrics`**: These are separate class hierarchies. `FinancialRatios` uses rendered DataFrames (with standard labels as index); `FinancialMetrics` uses `to_dataframe(presentation=False)` (raw XBRL values, no sign adjustment). `FinancialRatios` does NOT extend `FinancialMetrics`.

- **BeneishMScore requires prior-year data**: Both current and prior period data are needed for all 8 variables (16 inputs total). Returns `None` if any are missing — a common failure for companies with limited filing history in the XBRLS.

- **Benford analysis requires scipy**: `analyze_digit_distribution()` imports `from scipy.stats import chi2` at call time. This is a conditional optional dependency.

- **SynonymGroups singleton is NOT thread-safe**: `_default_instance` is a module-level global; concurrent writes from `register_group()` on the singleton could race. Use `SynonymGroups()` directly for isolated instances.

- **Multi-group tag membership**: Tags like `DepreciationAndAmortization` can belong to multiple groups (e.g., both `depreciation_and_amortization` and a hypothetical cash-flow group). `identify_concept()` returns only the first match; `identify_concepts()` returns all. Filter by `category` to disambiguate.

- **Namespace normalization in SynonymGroup**: At `__post_init__`, all namespace prefixes are stripped and stored bare. `get_tags_with_namespace()` re-adds them. The `_tag_index` keys are lowercase bare tag names. Lookups strip namespace before matching.

- **`to_pandas(presentation=True)` sign behavior**: When `presentation=True` (default), values are multiplied by `preferred_sign` from the stitched item's `preferred_signs` dict. This matches SEC HTML display convention (e.g., cash outflows shown as negative). Use `presentation=False` for raw XBRL instance values.

- **Duplicate period column names** in `to_pandas()`: When `include_quarterly=True` causes two periods with the same end date, column names fall back to the full `period_label` instead of the `YYYY-MM-DD` date string (GH#780).

- **`StatementStitcher.stitch_statements()` resets state** on each call. The class is not thread-safe for concurrent stitching but is safe for sequential reuse.
