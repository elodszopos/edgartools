## XBRL Core

### Overview

The `edgar.xbrl` package converts raw SEC XBRL filings into a typed Python object model. The central entry point is `XBRL`, constructed via `filing.xbrl()` (or `XBRL.from_filing(filing)`). It integrates six parsed linkbases (instance, schema, label, presentation, calculation, definition) and exposes financial statements, a fluent facts query API, hierarchical notes, and dimensional data. `Statements`/`Statement` provide statement-level access; `FactsView`/`FactQuery` provide concept-level access; `Note`/`Notes` provide note-level access with drill-down into child tables.

---

### Public API Surface

| Symbol | file:line | Purpose |
|---|---|---|
| `XBRL` | `edgar/xbrl/xbrl.py:101` | Top-level parsed XBRL container |
| `XBRLFilingWithNoXbrlData` | `edgar/xbrl/xbrl.py:41` | Exception: filing has no XBRL data |
| `ExtensionArc` | `edgar/xbrl/statements.py:279` | Dataclass: filer-extension concept linked via calculation linkbase but absent from presentation tree |
| `Statements` | `edgar/xbrl/statements.py:2095` | High-level statement collection |
| `Statement` | `edgar/xbrl/statements.py:317` | Single financial statement |
| `StatementLineItem` | `edgar/xbrl/statements.py:2005` | Line item with note drill-down |
| `StitchedStatement` | `edgar/xbrl/statements.py:3066` | Multi-filing stitched statement |
| `StitchedStatements` | `edgar/xbrl/statements.py` (see stitching module) | Stitched collection |
| `StatementView` | `edgar/xbrl/presentation.py:13` | Enum: STANDARD / DETAILED / SUMMARY |
| `normalize_view` | `edgar/xbrl/presentation.py:58` | Coerce str/enum to StatementView |
| `FactsView` | `edgar/xbrl/facts.py:948` | All-facts query surface |
| `FactQuery` | `edgar/xbrl/facts.py:45` | Fluent query builder |
| `Note` | `edgar/xbrl/notes.py:35` | Single note with children |
| `Notes` | `edgar/xbrl/notes.py:317` | Notes collection with search |
| `StatementNotFound` | `edgar/xbrl/exceptions.py:10` | Custom exception for resolver failures |
| `XBRLProcessingError` | `edgar/xbrl/models.py:343` | General XBRL processing error |

---

### Key Classes

#### XBRL (`edgar/xbrl/xbrl.py:101`)

Top-level data container and operation hub. Wraps an `XBRLParser` and exposes all parsed structures as properties. All statement/fact/note access flows through this object.

**Construction:**
- `XBRL.from_filing(filing) -> Optional[XBRL]` — primary entry point; parses all 6 XBRL attachment types from a `Filing` object; also loads FilingSummary.xml for authoritative note hierarchy — `xbrl.py:497`
- `XBRL.from_directory(directory_path) -> XBRL` — parse all XBRL files from a directory — `xbrl.py:431`
- `XBRL.from_files(...) -> XBRL` — explicit file paths for each linkbase — `xbrl.py:452`

**Properties (all delegate to `self.parser`):**
- `element_catalog` — dict of element metadata (type, balance, labels) — `xbrl.py:210`
- `contexts` — dict of Context objects keyed by context_id — `xbrl.py:214`
- `footnotes` — XBRL footnotes dict — `xbrl.py:218`
- `_facts` — raw fact dict (use `facts` property for enriched access) — `xbrl.py:253`
- `units`, `presentation_roles`, `presentation_trees`, `calculation_roles`, `calculation_trees`, `definition_roles` — parsed linkbase structures — `xbrl.py:256-280`
- `tables`, `axes`, `domains` — dimensional structures from definition linkbase — `xbrl.py:280-295`
- `entity_info` — dict with entity_name, document_type, period_of_report, fiscal info — `xbrl.py:294`
- `reporting_periods` — list of period dicts with key/label/start_date/end_date — `xbrl.py:298`
- `period_of_report` — validated period end date (SGML vs XBRL discrepancy-corrected) — `xbrl.py:302`
- `entity_name`, `document_type` — convenience properties — `xbrl.py:401,407`
- `element_context_index` — lazy-built reverse index: element_name → [context_ids] — `xbrl.py:414`

**Statement access:**
- `statements` property → `Statements(self)` (new instance each call, not cached) — `xbrl.py:614`
- `fund_statements` property → `FundStatements(self)` (cached via `_fund_statements`) — `xbrl.py:619`
- `get_statement(role_or_type, period_filter, should_display_dimensions, view) -> List[Dict]` — raw line-item list — `xbrl.py:1035`
- `get_all_statements() -> List[Dict]` — cached list of all presentation-tree statements with type/category metadata — `xbrl.py:774`
- `get_statement_by_type(statement_type, include_dimensions) -> Optional[Dict]` — `xbrl.py:911`
- `find_statement(statement_type, is_parenthetical) -> Tuple[List, Optional[str], str]` — delegates to `StatementResolver` — `xbrl.py:2029`
- `render_statement(statement_type, ...) -> Optional[RenderedStatement]` — full rendering pipeline — `xbrl.py:2128`
- `get_statements_by_category(category) -> List[Dict]` — `xbrl.py:2008`

**Facts access:**
- `facts` property → `FactsView(self)` (cached via `_facts_view`) — `xbrl.py:729`
- `query(include_dimensions, include_contexts, include_element_info) -> FactQuery` — shortcut — `xbrl.py:758`
- `to_pandas(statement_role, standard) -> Dict[str, pd.DataFrame]` — full export — `xbrl.py:2216`

**Notes/disclosures:**
- `notes() -> List[Statement]` — delegates to `statements.notes()` — `xbrl.py:642`
- `disclosures() -> List[Statement]` — delegates to `statements.disclosures()` — `xbrl.py:656`
- `list_tables() -> Dict[str, List]` — categorized dict of all tables — `xbrl.py:670`
- `get_table(name) -> Optional[Statement]` — smart name-based lookup — `xbrl.py:685`
- `get_disclosure(role_uri) -> Optional[Statement]` — exact role URI lookup — `xbrl.py:705`

**Dimension helpers:**
- `is_dimension_valid_for_role(dimension, role_uri) -> bool` — definition-linkbase check — `xbrl.py:2528`
- `has_definition_linkbase_for_role(role_uri) -> bool` — check if tables exist for role — `xbrl.py:2568`

**Standardization:**
- `standardization` property → `StandardizationCache(self)` (lazy) — `xbrl.py:247`

**Period:**
- `get_period_views(statement_type) -> List[Dict]` — available display views — `xbrl.py:1997`

**Stitch:**
- `stitch_statements(xbrl_list, statement_type, ...) -> Dict` — class method — `xbrl.py:955`

**Calculation linkbase:**
- `calculation_linkbase(include_abstract=False) -> pd.DataFrame` — full calculation arc table; columns: `concept`, `concept_taxonomy`, `parent_concept`, `parent_taxonomy`, `weight`, `role_uri`, `role_short`, `menucat`, `is_abstract`, `label`; root nodes excluded (no arc); empty DataFrame if no cal linkbase — `xbrl.py:301`

**Footnotes:**
- `get_footnotes_for_fact(fact_id) -> List[Footnote]` — `xbrl.py:2395`
- `get_facts_with_footnotes() -> Dict[str, Fact]` — `xbrl.py:2415`

**Other:**
- `to_context(max_tokens) -> str` — AI-optimized compact text representation — `xbrl.py:2591`

---

#### Statement (`edgar/xbrl/statements.py:317`)

A single financial statement identified by role URI or canonical type. Thin wrapper around `xbrl.get_statement()` and the rendering pipeline. Does not hold data — retrieves on demand.

**Constructor:** `Statement(xbrl, role_or_type, canonical_type=None, skip_concept_check=False, include_dimensions=False, view=None)` — `statements.py:350`

- `role_or_type`: role URI, canonical type ("BalanceSheet"), or role short name
- `canonical_type`: sets specialized processing (period logic, ratio calcs, etc.)
- `view`: `StatementView` sets default for `.render()` and `.to_dataframe()`
- `_report`: set by notes.py when built from FilingSummary; gives access to HTML rendering

**Key methods:**
- `render(period_filter, period_view, standard, show_date_range, view, include_dimensions) -> RenderedStatement` — `statements.py:401`; default view: STANDARD
- `to_dataframe(period_filter, period_view, standard, view, include_dimensions, include_unit, include_point_in_time, include_standardization, presentation, matrix) -> DataFrame` — `statements.py:902`; default view: DETAILED
- `get_raw_data(period_filter, view) -> List[Dict]` — underlying line-item list — `statements.py:1859`
- `text(raw_html=False) -> Optional[str]` — narrative text from TextBlock XBRL tags — `statements.py:1886`
- `html` property — raw HTML from TextBlock tags — `statements.py:1913`
- `is_note` property — True if statement has TextBlock content — `statements.py:1918`
- `extension_arcs(include_values=False) -> List[ExtensionArc]` — filer-extension concepts in the calculation linkbase that are absent from the presentation tree (i.e., do not appear in `render()` output); `include_values=True` emits one arc per fact context — `statements.py:435`
- `validate(level) -> ValidationResult` — accounting equation validation — `statements.py:1704`
- `calculate_ratios() -> Dict[str, float]` — current ratio, gross margin, net margin — `statements.py:1741`
- `analyze_trends(periods) -> Dict[str, List[float]]` — `statements.py:1801`
- `to_markdown(detail, optimize_for_llm) -> str` — GFM rendering — `statements.py:753`
- `to_context(detail) -> str` — AI-optimized text — `statements.py:762`
- `__getitem__(label) -> Optional[StatementLineItem]` — look up line item by exact label — `statements.py:1931`
- `search(keyword) -> List[StatementLineItem]` — fuzzy label search — `statements.py:1959`
- `__str__` / `__rich__` — delegates to `.render()` — `statements.py:747,465`
- `_is_matrix_statement() -> bool` — detects equity statement for matrix format — `statements.py:479`
- `_to_df(...)` — debug helper with formatted numbers — `statements.py:1336`
- `report` property — FilingSummary Report with `.to_dataframe()` / `.view()` / `.content` — `statements.py:382`

**StatementView behavior in to_dataframe:**
- DETAILED (default): all dimensional rows included
- STANDARD: breakdown dimensions filtered, face-level dimensions kept
- SUMMARY: all dimensional rows hidden

**Internal pipeline:**
`to_dataframe()` → `_build_dataframe_from_raw_data()` → `_add_metadata_columns()` → `_apply_presentation()` → (optionally) `_pivot_to_matrix()`

---

#### StatementLineItem (`edgar/xbrl/statements.py:2005`)

Single line item returned by `stmt['label']` or `stmt.search('keyword')`. Not for direct construction.

- `label` property — display label string — `statements.py:2026`
- `concept` property — XBRL concept ID (e.g., `us-gaap_LongTermDebtNoncurrent`) — `statements.py:2030`
- `values` property — list of cell values in period order — `statements.py:2034`
- `note` property — most specific `Note` for this line item (or None) — `statements.py:2039`
- `notes` property — all related `Note` objects ranked by specificity — `statements.py:2044`
- `to_markdown(include_note) -> str` — formatted with optional note reference — `statements.py:2053`

The `.note`/`.notes` drill-down uses `get_notes_for_concept(concept_id, xbrl)` from `notes.py:1162`, which uses the lazy-built concept→notes reverse index cached on `xbrl._concept_to_notes_cache`.

---

#### Statements (`edgar/xbrl/statements.py:2095`)

Collection wrapper over all statements in a filing. Accessed via `xbrl.statements`.

**Core statement accessors** (each returns `Optional[Statement]`):
- `balance_sheet(parenthetical, view, include_dimensions)` — `statements.py:2678`
- `income_statement(parenthetical, skip_concept_check, view, include_dimensions)` — `statements.py:2713`
- `cashflow_statement(parenthetical, view, include_dimensions)` / `cash_flow_statement(...)` — `statements.py:2749`
- `statement_of_equity(parenthetical, view, include_dimensions)` — defaults `include_dimensions=True` — `statements.py:2786`
- `comprehensive_income(parenthetical, view, include_dimensions)` — defaults `include_dimensions=True` — `statements.py:2823`
- `cover_page()` — `statements.py:2659`
- `schedule_of_investments(parenthetical)` — fund filing — `statements.py:2864`

**Discovery:**
- `search(keyword) -> List[Statement]` — AND search across definition/role_name/type — `statements.py:2985`
- `get(name) -> Optional[Statement]` — tiered: exact type → role_name contains → definition contains — `statements.py:3011`
- `all(category=None) -> List[Statement]` — all statements, optionally filtered — `statements.py:2944`
- `list_available(category=None) -> DataFrame` — browsable DataFrame — `statements.py:2961`
- `notes() -> List[Statement]` — all note-category statements — `statements.py:2921`
- `disclosures() -> List[Statement]` — all disclosure-category statements — `statements.py:2930`
- `get_by_category(category) -> List[Statement]` — generic — `statements.py:2902`
- `get_statements_by_category() -> dict` — returns dict with keys: statement/note/disclosure/document/other — `statements.py:2213`
- `classify_statement(stmt) -> str` — static method: tiered classification — `statements.py:2147`
- `to_context(detail) -> str` — AI-optimized text, detail='minimal'/'standard'/'full' — `statements.py:2399`
- `__getitem__(int|str) -> Optional[Statement]` — by index or type/role — `statements.py:2351`
- `__len__`, `__iter__` — standard collection protocol — `statements.py:2393,2396`

**Statement type constants** (`statement_to_concepts` dict at `statements.py:277`):
IncomeStatement, BalanceSheet, CashFlowStatement, StatementOfEquity, ComprehensiveIncome, CoverPage, ScheduleOfInvestments, FinancialHighlights — each is a `StatementInfo(name, concept, title)` where `concept` is the root XBRL abstract element.

---

#### FactsView (`edgar/xbrl/facts.py:948`)

All-facts query surface, cached on `xbrl._facts_view`. Wraps raw facts with enriched context/element/dimension info.

- `get_facts() -> List[Dict]` — builds and caches enriched fact list (lazy, one-time cost) — `facts.py:975`; each fact dict includes: concept, context_ref, value, numeric_value, unit_ref, decimals, period_type, period_instant/start/end, entity_identifier, dim_* columns, dimension/member/dimension_label/dimension_member_label, full_dimension_label, is_dimensioned, label, original_label, balance, preferred_sign, statement_type, statement_role, weight, fiscal_period, fiscal_year, period_key
- `query() -> FactQuery` — start a fluent query — `facts.py:1246`
- `to_dataframe() -> pd.DataFrame` — all facts, deduped (cached in `_facts_df_cache`) — `facts.py:1255`
- `get_statement_facts(statement_type) -> DataFrame` — `facts.py:1271`
- `get_facts_by_concept(pattern, exact) -> DataFrame` — `facts.py:1283`
- `search_facts(text_pattern) -> DataFrame` — `facts.py:1296`
- `get_facts_with_dimensions() -> DataFrame` — `facts.py:1311`
- `get_facts_by_period(period_key) -> DataFrame` — `facts.py:1322`
- `get_facts_by_period_view(statement_type, period_view_name) -> DataFrame` — `facts.py:1334`
- `get_facts_by_fiscal_period(fiscal_year, fiscal_period) -> DataFrame` — `facts.py:1370`
- `summarize() -> Dict` — counts by type/statement/period plus unique dimensions/periods — `facts.py:1384`
- `get_unique_concepts() -> List[str]` — `facts.py:1436`
- `get_unique_dimensions() -> Dict[str, Set[str]]` — dimension → member values — `facts.py:1447`
- `pivot_by_period(concept_pattern, statement_type) -> DataFrame` — concept×period matrix — `facts.py:1496`
- `pivot_by_dimension(dimension, concept_pattern, period_key) -> DataFrame` — `facts.py:1537`
- `time_series(concept, exact) -> DataFrame` — sorted by date — `facts.py:1586`
- `facts_history(concept, date_col, include_dimensions) -> DataFrame` — `facts.py:1633`
- `clear_cache()` — clears `_facts_cache` and `_facts_df_cache` — `facts.py:1749`
- `get_available_period_views(statement_type) -> List[Dict]` — `facts.py:1467`

---

#### FactQuery (`edgar/xbrl/facts.py:45`)

Fluent query builder returned by `xbrl.facts.query()`. All filter methods return `self` for chaining; terminates with `.execute()` or `.to_dataframe()`.

**Filter methods:**
- `by_concept(pattern, exact=False)` — regex or exact match on concept name (normalizes `_` to `:`) — `facts.py:73`
- `by_label(pattern, exact=False)` — searches label, element_label, original_label — `facts.py:92`
- `by_value(value_filter)` — callable predicate, exact value, or (min, max) range — `facts.py:128`
- `by_period_type(period_type)` — 'instant' or 'duration' — `facts.py:166`
- `by_period_key(period_key)` — exact period key — `facts.py:183`
- `by_period_keys(period_keys)` — list of keys — `facts.py:196`
- `by_instant_date(date_str, exact=True)` — instant facts by date — `facts.py:209`
- `by_date_range(start_date, end_date, exact=False)` — duration period range — `facts.py:228`
- `by_dimension(dimension, value=None)` — flexible matching (namespace prefix, underscore/colon variants); `dimension=None` filters for no dimensions; automatically enables dimension columns in output — `facts.py:280`
- `by_statement_type(statement_type)` — `facts.py:533`
- `by_fiscal_period(fiscal_period)` — 'FY', 'Q1', 'Q2', 'Q3', 'Q4' — `facts.py:546`
- `by_fiscal_year(fiscal_year)` — `facts.py:559`
- `by_unit(unit)` — `facts.py:572`
- `by_custom(filter_func)` — arbitrary predicate — `facts.py:585`
- `by_text(pattern)` — searches concept, label, element_label, element_name, original_label — `facts.py:598`
- `from_statement(statement_type)` — alias for by_statement_type — `facts.py:707`

**Modifiers:**
- `with_dimensions()` / `exclude_dimensions()` — include/exclude dim_* columns — `facts.py:639,649`
- `exclude_contexts()` / `exclude_element_info()` — strip context/element columns — `facts.py:659,669`
- `sort_by(column, ascending)` — `facts.py:679`
- `limit(n)` — `facts.py:694`
- `scale(scale_factor)` — divide numeric_value by factor — `facts.py:734`
- `transform(transform_fn)` — custom value transformation — `facts.py:721`
- `aggregate(dimension, func='sum')` — group by dimension value — `facts.py:752`

**Terminal methods:**
- `execute() -> List[Dict]` — `facts.py:769`; applies filters, transformations, aggregations, sort, limit
- `to_dataframe(*columns) -> pd.DataFrame` — `facts.py:829`; deduplicates, columns ordered with concept/label/value/period first; result cached per `columns` argument

**DataFrame columns** (when `include_dimensions=True` and `include_contexts=True`): concept, label, balance, preferred_sign, weight, value, numeric_value, period_key, period_start, period_end, period_instant, is_dimensioned, decimals, statement_type, statement_name, context_ref, entity_identifier, entity_scheme, period_type, dim_*, dimension, member, dimension_label, member_label, dimension_member_label, full_dimension_label, element_id, element_name, element_type, element_period_type, element_balance, element_label

---

#### Note (`edgar/xbrl/notes.py:35`)

A single note to the financial statements, with hierarchical children from FilingSummary.xml.

**Constructor:** `Note(number, title, short_name, role, statement, tables, policies, details, menu_category, xbrl)` — `notes.py:43`

**Properties:**
- `table_count`, `has_tables` — `notes.py:66,70`
- `children` — tables + policies + details combined — `notes.py:74`
- `text` — narrative plain text from TextBlock XBRL tags — `notes.py:79`
- `html` — raw HTML from TextBlock tags — `notes.py:85`
- `expands` — human-readable labels of FS line items this note breaks down — `notes.py:99`
- `expands_concepts` — raw concept IDs shared with core statements — `notes.py:113`
- `expands_statements` — which statement types contain the overlapping concepts — `notes.py:118`

**Methods:**
- `to_context(detail='standard') -> str` — AI-optimized; detail: 'minimal'/'standard'/'full' — `notes.py:135`
- `to_markdown(detail, optimize_for_llm) -> str` — GFM with tables, narrative, policies — `notes.py:204`

The `expands` property is computed lazily (cached in `_expands_cache`) by `_compute_expands()` which scans the note's role + all child roles' presentation trees and intersects with core statement concept sets.

---

#### Notes (`edgar/xbrl/notes.py:317`)

Collection of all notes. Typically accessed via `ten_k.notes` (on the TenK filing object) which calls `Notes.from_xbrl(xbrl, filing_summary)`.

**Construction:**
- `Notes.from_xbrl(xbrl, filing_summary=None) -> Notes` — `notes.py:335`; if FilingSummary available, uses `_build_from_filing_summary` for authoritative parent/child hierarchy; otherwise falls back to `_build_from_xbrl_only` flat classification
- Caches result on `xbrl._notes_cache`

**Access:**
- `notes[5]` — by 1-based number — `notes.py:493`
- `notes['Debt']` — by exact short_name (case-insensitive) — `notes.py:493`
- `notes.search('share') -> List[Note]` — ranked fuzzy search: exact > starts-with > word > substring — `notes.py:517`
- `notes.grep(pattern, regex=False) -> GrepResult` — full-text search of narrative content — `notes.py:564`
- `notes.with_tables` — property: notes that have child tables — `notes.py:597`
- `len(notes)`, iteration, `'Debt' in notes` — `notes.py:479-491`
- `to_markdown(detail, focus, optimize_for_llm) -> str` — render all or focused notes — `notes.py:601`
- `to_context(detail, focus) -> str` — AI-optimized all-notes context — `notes.py:643`

**Note hierarchy from FilingSummary:**
Each FilingSummary report with `menu_category='Notes'` becomes a root `Note`. Children linked via `parent_role` field: `Tables` → `note.tables`, `Policies` → `note.policies`, `Details` → `note.details`. Orphan Details matched by name prefix as fallback.

---

### Class Hierarchy

```
XBRL
├── .statements  →  Statements(xbrl)
│   ├── [n]          →  Statement(xbrl, role, canonical_type)
│   ├── .balance_sheet()  →  Statement
│   ├── .income_statement()  →  Statement
│   ├── .cashflow_statement()  →  Statement
│   ├── .statement_of_equity()  →  Statement
│   ├── .comprehensive_income()  →  Statement
│   ├── .cover_page()  →  Statement
│   └── (Note, Disclosure Statements also via .notes()/.disclosures())
├── .facts  →  FactsView(xbrl)
│   └── .query()  →  FactQuery(facts_view)
│       └── .to_dataframe()  →  DataFrame
├── .notes()  →  [Statement, ...]   (flat list)
│        (or filing.obj().notes  →  Notes collection)
│               └── notes['Debt']  →  Note
│                   ├── .tables  →  [Statement, ...]
│                   ├── .text / .html
│                   └── .expands / .expands_concepts
└── Statement.__getitem__('label')  →  StatementLineItem
    └── .note  →  Note
        └── .tables[0]  →  Statement (child table)

Data models (edgar/xbrl/models.py):
  Fact (Pydantic)  ←  parser.facts
  Context (Pydantic)  ←  parser.contexts
  Footnote (Pydantic)  ←  parser.footnotes
  PresentationNode (Pydantic)  ←  presentation_trees[role].all_nodes
  PresentationTree (Pydantic)
  CalculationNode (Pydantic)
  CalculationTree (Pydantic)
  Axis / Domain / Table (Pydantic)  ←  dimensional definition linkbase
  ElementCatalog (plain class)  ←  element_catalog

Data models (edgar/xbrl/statements.py):
  ExtensionArc (dataclass)  ←  Statement.extension_arcs()
    Fields: concept, concept_taxonomy, parent_concept, parent_taxonomy,
            weight, label, role_uri, element_id,
            value (Optional), period_key (Optional), context_ref (Optional)
```

---

### Configuration & Options

| Option | Type | Default | Effect |
|---|---|---|---|
| `StatementView.STANDARD` | enum | display default | Face presentation; breakdown dims filtered, face dims shown |
| `StatementView.DETAILED` | enum | to_dataframe default | All dimensional data shown |
| `StatementView.SUMMARY` | enum | explicit only | All dimensional rows hidden |
| `Statement.canonical_type` | str | None | Drives specialized period/ratio logic |
| `Statement._view` | StatementView | None | Instance-level view default |
| `Statement.render(standard=True)` | bool | True | Apply label standardization |
| `Statement.to_dataframe(presentation=True)` | bool | True | Apply preferred_sign negation |
| `Statement.to_dataframe(matrix=False)` | bool | False | Pivot equity statement to matrix |
| `FactQuery._include_dimensions` | bool | False | Include dim_* columns in output |
| `FactQuery._include_contexts` | bool | True | Include context_ref/entity/period_type |
| `FactQuery._include_element_info` | bool | True | Include element_id/type/balance/label |
| `FactQuery._limit` | int | None | Limit result rows |
| `Note.to_context(detail='standard')` | str | 'standard' | 'minimal'/'standard'/'full' |
| `Notes.to_markdown(detail='standard')` | str | 'standard' | 'minimal'/'standard'/'full' |

---

### Data Flow / Lifecycle

- `XBRL.__init__()` creates an empty `XBRLParser` and null caches. No data is loaded.
- `XBRL.from_filing(filing)` orchestrates parsing: schema → labels → presentation → calculation → definition → instance (in this order). If iXBRL instance is missing from local SGML, network fallback fetches it. SGML `period_of_report` captured for discrepancy detection. FilingSummary.xml loaded to populate `_filing_summary_categories` / `_filing_summary_menu_categories` / `_filing_summary`.
- SIC code from filing SGML header is passed to `standardization.set_industry_from_sic()` if available (zero extra network calls — only if already-loaded `_sgml`).
- `xbrl.get_all_statements()` is called lazily and cached in `_all_statements_cached`. It scans `presentation_trees` and classifies each role as IncomeStatement/BalanceSheet/etc. using root-element concept matching, IFRS concept map, FilingSummary categories, and keyword fallbacks. Builds 5 lookup indices.
- `xbrl.statements` creates a fresh `Statements` object on each access (not cached). `Statements.__init__` calls `xbrl.get_all_statements()`.
- `Statement.get_raw_data()` calls `xbrl.get_statement()` which walks the presentation tree via `_generate_line_items()` recursively, populating values from `_find_facts_for_element()`. Uses `element_context_index` (lazy) to avoid iterating all contexts per concept. Applies revenue deduplication (IncomeStatement), calculation-based reordering (BalanceSheet), and level adjustment.
- `FactsView.get_facts()` iterates all raw facts once, enriching each with context period/entity/dimension info, element catalog labels/balance, presentation preferred_label, statement_type, calculation weight, and fiscal period info. Result is cached in `_facts_cache`. Subsequent calls return the cache.
- `FactsView.to_dataframe()` calls `get_facts()` then deduplicates on (concept, context_ref, value, decimals), caches in `_facts_df_cache`.
- `FactQuery.to_dataframe()` calls `execute()` which re-runs filters on `facts_view.get_facts()` (already cached). Result cached per requested columns tuple in `_df_cache`.
- `Notes.from_xbrl()` builds the `Notes` object. If FilingSummary is attached to XBRL (`xbrl._filing_summary`), uses hierarchical build; else flat fallback. Caches on `xbrl._notes_cache`.
- `StatementLineItem.note` access triggers lazy build of `xbrl._concept_to_notes_cache` (concept→notes index), which itself triggers `Notes.from_xbrl()` if `_notes_cache` is None.
- `expands` on `Note` is computed once per `Note` instance (cached in `_expands_cache`) by intersecting the note's presentation-tree concept set with core statement concept sets (the latter cached on `xbrl._statement_concepts_cache`).
- `standardization` property (`StandardizationCache`) is lazy; `element_context_index` is lazy; `_statement_resolver` is lazy.
- `period_of_report` validation computes once and caches in `_validated_period_of_report_cache` — compares XBRL vs SGML dates against annual periods found in `reporting_periods`.

---

### Design Patterns

- **Lazy initialization with caching** — all expensive computations (`get_all_statements`, `element_context_index`, `_facts_cache`, `_notes_cache`, `_statement_concepts_cache`, `_concept_to_notes_cache`, `_validated_period_of_report_cache`) use a `None`-check pattern and store results for reuse. No explicit thread safety.
- **Fluent/builder API** — `FactQuery` builds a filter list then materializes on `execute()`/`to_dataframe()`, following the builder pattern.
- **Delegation/adapter** — `XBRL` wraps `XBRLParser` and delegates all raw data properties via thin property adapters. `XBRLAttachments` adapts `Attachments` to the XBRL doc-type model.
- **Tiered fallback resolution** — statement type classification (FilingSummary → concept-map → IFRS-map → keyword), dimension classification (definition-linkbase → explicit lists → regex patterns), find_statement (StatementResolver → legacy index lookups), label selection (preferred → terse → standard → any → element name).
- **Enum-based view control** — `StatementView` (STANDARD/DETAILED/SUMMARY) replaces the deprecated `include_dimensions: bool` parameter, providing semantic names. `normalize_view()` accepts str or enum for API flexibility.
- **Structural filtering** — `is_xbrl_structural_element()` and `is_breakdown_dimension()` separate XBRL infrastructure (Axis/Domain/Table/LineItems) from actual financial data.
- **Synthetic total computation** — when a concept has only dimensional facts (no non-dimensional total), `_compute_synthetic_total()` sums the most-populated axis to provide a roll-up value (Issue #646).
- **Complementary row merging** — `_merge_complementary_rows()` merges adjacent same-label rows that have non-overlapping period values, handling concept renames across filing years.

---

### Cross-Domain Interactions

**Imports from other `edgar.*` modules:**
- `edgar.attachments.Attachments` — for `XBRLAttachments` construction
- `edgar.config.VERBOSE_EXCEPTIONS` — controls log verbosity in statement resolution
- `edgar.core.log` — logging
- `edgar.richtools.repr_rich`, `Docs` — rich display
- `edgar.storage` — `is_using_local_storage()`, `is_network_fallback_allowed()` for iXBRL network fallback
- `edgar.markdown.process_content` — HTML→Markdown for note rendering
- `edgar.search.grep.GrepResult`, `_grep_text` — for `Notes.grep()`
- `edgar.display.get_statement_styles`, `get_style`, `SYMBOLS` — display styles

**Consumed by other `edgar.*` modules:**
- `edgar.entity` / `edgar.company` — calls `filing.xbrl()` → `XBRL.from_filing()`
- `edgar.financials` — wraps `Statement` in typed financial statement classes
- `edgar.xbrl.stitching` — `XBRLS`, `StatementStitcher`, `StitchedFactsView` import `XBRL`, `FactsView`, `Statement`
- `edgar.xbrl.rendering` — consumes `get_statement()` output and entity_info
- `edgar.xbrl.periods` / `edgar.xbrl.period_selector` — consume XBRL properties (reporting_periods, entity_info)
- `edgar.xbrl.statement_resolver.StatementResolver` — takes XBRL instance to resolve statements
- `edgar.xbrl.standardization.StandardizationCache` — takes XBRL instance
- `edgar.xbrl.fund_statements.FundStatements` — takes XBRL instance

---

### Gotchas & Notable Behaviors

- **`xbrl.statements` is not cached** — `xbrl.statements` creates a new `Statements` object on every property access. The underlying `get_all_statements()` is cached, so construction is cheap, but avoid repeated property access in tight loops.
- **`XBRL.from_filing` returns `None` on missing attachments** — if no XBRL attachments found, returns None (not raises). Callers must null-check.
- **Amended filings emit a warning** — `form.endswith("/A")` triggers a log.warning that the filing may have incomplete XBRL data.
- **iXBRL instance fallback** — for pre-Oct-2020 iXBRL filings stored locally, the instance XML is missing from the SGML bundle; the code performs a network fetch from the SEC homepage if `allow_network_fallback=True`.
- **Duplicate facts** — SEC instance documents often tag the same fact multiple times. `_deduplicate_facts()` in `FactQuery.to_dataframe()` deduplicates on (concept, context_ref, value, decimals), keeping first occurrence. Facts with identical context but different values/precision are preserved.
- **Period key format** — period keys are strings like `"instant_2024-09-28"` or `"duration_2023-10-01_2024-09-28"`. The FactQuery `by_period_key` and Statement `period_filter` use these keys directly.
- **`include_dimensions` is deprecated** — replaced by `view='standard'|'detailed'|'summary'` throughout `Statement` and `Statements`. Emits `DeprecationWarning`; will be removed in v6.0. `view` and `include_dimensions` cannot both be specified.
- **Dimension filtering is two-tiered** — Tier 1 uses definition linkbase (authoritative, `DimensionConfidence.HIGH`); Tier 2 uses `BREAKDOWN_AXES`/`FACE_AXES` explicit sets and regex patterns (`BREAKDOWN_PATTERNS`). The tiering logic is in `dimensions.py:245`.
- **`StatementEquityComponentsAxis` is context-dependent** — treated as BREAKDOWN on BalanceSheet but STRUCTURAL on Statement of Equity (see `STATEMENT_STRUCTURAL_AXES` in `dimensions.py:213`).
- **Synthetic totals** — when only dimensional members exist for a concept (no non-dimensional total fact), `_compute_synthetic_total()` sums the most-populated axis. Skipped for per-share and ratio data types.
- **StatementNotFound is a dataclass exception** — `edgar/xbrl/exceptions.py:10`. Fields: `statement_type`, `confidence`, `found_statements`, `entity_name`, `cik`, `period_of_report`, `reason`. Use `except StatementNotFound` in calling code.
- **Note.expands requires XBRL reference** — `Note._xbrl` must be set (done automatically when built via `Notes.from_xbrl()`). If a Note is constructed manually without xbrl, `expands` returns [].
- **FilingSummary dependency for rich Notes** — `Notes.from_xbrl()` uses `xbrl._filing_summary` (set during `XBRL.from_filing()`). Without it, falls back to flat XBRL-only classification (no tables/policies/details hierarchy).
- **Label priority order** — `select_display_label()` in `models.py:19`: preferred_label role → terse_label → standard_label → any_label → element_name → element_id. Standardization only applied when NOT using company-specific preferred/terse labels.
- **`Statement.text()` only for TextBlock concepts** — uses `is_textblock_concept()` to identify narrative XBRL concepts. For financial statements, returns None. Only notes/disclosures return text.
- **Statement of Equity beginning/ending balance detection** — `to_dataframe()` tracks (concept, label) occurrence counts; first occurrence gets "- Beginning balance" suffix, last occurrence gets "- Ending balance". Instant facts matched to duration periods via date arithmetic.
- **Calculation reordering (BalanceSheet)** — `_reorder_by_calculation_parent()` moves components that appear after their calculation parent to precede it, correcting incorrect presentation linkbase ordering (Issue #575).
- **XBRL date validation** — `parse_date()` in `core.py:26` validates day-of-month for February, 30-day months, and 31-day months, raising descriptive ValueError for invalid XBRL dates.
- **Deduplication on `FactsView.to_dataframe()`** but not on `FactQuery.execute()` — raw `execute()` may contain duplicates; `to_dataframe()` applies `_deduplicate_facts()`.
- **`by_dimension(None)` filters for facts with NO dimensions** — explicitly passing `dimension=None` to `FactQuery.by_dimension()` selects only undimensioned facts.
- **Dimension key/value normalization** — `by_dimension()` accepts any of: `srt_ProductOrServiceAxis`, `srt:ProductOrServiceAxis`, `ProductOrServiceAxis`; partial local-name matching is attempted. Values similarly accept colon or underscore variants.
- **Label standardization skips company-preferred labels** — `PresentationNode.is_company_preferred_label` returns True if the node uses a specific non-standard preferred_label or has a terseLabel. Standardization then does NOT override these to preserve company-specific context (e.g., "Other intangible assets, net" vs generic "Intangible Assets").
