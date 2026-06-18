# CompanyReport — Base Class Field Reference

**Python class**: `CompanyReport`
**Source**: `edgar/company_reports/_base.py:23`
**Subclasses**: `TenK`, `TenQ`, `CurrentReport`, `TwentyF`, `FortyF` — `EightK` is an alias for `CurrentReport` (`EightK = CurrentReport` at `current_report.py:943`), not a separate subclass
**Not a parent of**: `SixK` (standalone)
**Filing fields**: See `_base-filing.md` — all `Filing` fields accessible via `self._filing`

---

## Constructor

`CompanyReport(filing)` — `_base.py:25`

| Argument | Type | Description |
|----------|------|-------------|
| `filing` | `Filing` | The underlying Filing object stored as `self._filing` |

---

## Instance Attributes (set in `__init__`)

| Attribute | Type | Description |
|-----------|------|-------------|
| `_filing` | `Filing` | Underlying Filing; all Filing fields accessible via it |
| `_parser` | `None\|HTMLParser` | Lazily initialized on first `document` access |

---

## Filing Passthrough Properties (immediate — no network)

These delegate directly to `self._filing` without triggering SGML loads.

| Property | Type | Delegates to | Source |
|----------|------|-------------|--------|
| `filing_date` | `str` | `_filing.filing_date` | `_base.py:30` |
| `form` | `str` | `_filing.form` | `_base.py:34` |
| `company` | `str` | `_filing.company` | `_base.py:38` |
| `period_of_report` | `Optional[str]` | `_filing.header.period_of_report` (triggers SGML) | `_base.py:112` |

---

## Statement Shortcut Properties (lazy — trigger XBRL parse)

These call `self.financials` which triggers XBRL parsing on first access.

| Property | Type | Description | Source |
|----------|------|-------------|--------|
| `income_statement` | `Optional[Statement]` | Delegates to `financials.income_statement()` | `_base.py:42` |
| `balance_sheet` | `Optional[Statement]` | Delegates to `financials.balance_sheet()` | `_base.py:46` |
| `cash_flow_statement` | `Optional[Statement]` | Delegates to `financials.cashflow_statement()` | `_base.py:50` |

---

## Cached Properties (computed once, then stored)

| Property | Type | Description | Source |
|----------|------|-------------|--------|
| `financials` | `Optional[Financials]` | XBRL facade; `None` if no XBRL data | `_base.py:107` |
| `auditor` | `Optional[AuditorInfo]` | Auditor from DEI XBRL facts; `None` if no XBRL | `_base.py:54` |
| `notes` | `Notes` | Financial statement notes hierarchy; empty `Notes` if no XBRL | `_base.py:62` |
| `reports` | `Optional[Reports]` | XBRL report pages from FilingSummary.xml | `_base.py:102` |
| `document` | `Document` | Parsed HTML document via `HTMLParser(ParserConfig(form=...))` | `_base.py:116` |
| `chunked_document` | `ChunkedDocument` | **DEPRECATED** (v5; removed v6); use `document` instead | `_base.py:136` |

---

## Properties (computed from `document`)

| Property | Type | Description | Source |
|----------|------|-------------|--------|
| `items` | `List[str]` | Section identifiers in `'Item X'` format (e.g. `['Item 1', 'Item 1A', 'Item 7']`) | `_base.py:157` |
| `doc` | `Document` | Alias for `document` | `_base.py:153` |

---

## Methods

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `__getitem__(item_or_part)` | `str` | `Optional[str]` | Section text lookup by `'Item 1'`, `'1A'`, `'Part I'`; delegates to `document.sections` | `_base.py:190` |
| `view(item_or_part)` | `str` | `None` | Print section text to console | `_base.py:217` |
| `grep(pattern, regex, document)` | `str, bool=False, Optional[str]=None` | `GrepResult` | Case-insensitive search; delegates to `_filing.grep()` | `_base.py:81` |
| `to_context(detail, focus)` | `str='standard', Optional=None` | `str` | AI-optimized context string; implemented per subclass | per subclass |
| `_focused_context(focus, detail)` | `Union[str, list], str='standard'` | `str` | Cross-cutting note + statement line item context for a topic | `_base.py:223` |
| `_append_expands_with_values(lines, note)` | `list, Note` | `None` | Internal: appends note expanded line items with formatted values | `_base.py:281` |

---

## Nested Object: `Financials` (`edgar/financials.py:13`)

Accessed via `report.financials`. Thin facade over `XBRL`.

### `Financials` Constructor / Factory

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `Financials.extract(filing)` | `Filing` | `Optional[Financials]` | Calls `XBRL.from_filing(filing)`; returns `None` if no XBRL | `financials.py:18` |

| Attribute | Type | Description |
|-----------|------|-------------|
| `xb` | `Optional[XBRL]` | Underlying XBRL object; direct access for low-level operations |

### Statement Accessors

All accept `include_dimensions: bool = None` and `view: ViewType = None`.

| Method | Returns | Description | Source |
|--------|---------|-------------|--------|
| `balance_sheet(include_dimensions, view)` | `Optional[Statement]` | Balance sheet | `financials.py:27` |
| `income_statement(include_dimensions, view)` | `Optional[Statement]` | Income statement | `financials.py:46` |
| `cashflow_statement(include_dimensions, view)` | `Optional[Statement]` | Cash flow statement | `financials.py:65` |
| `cash_flow_statement(**kwargs)` | `Optional[Statement]` | Alias for `cashflow_statement()` | `financials.py:84` |
| `statement_of_equity(include_dimensions, view)` | `Optional[Statement]` | Statement of stockholders' equity | `financials.py:88` |
| `comprehensive_income(include_dimensions, view)` | `Optional[Statement]` | Comprehensive income statement | `financials.py:107` |
| `cover()` | `Optional[Statement]` | DEI cover page | `financials.py:126` |

`ViewType` values (from `edgar.xbrl.presentation`):

| Value | Description |
|-------|-------------|
| `ViewType.STANDARD` | Face presentation matching SEC Viewer (display default) |
| `ViewType.DETAILED` | All dimensional data (to_dataframe default) |
| `ViewType.SUMMARY` | Non-dimensional totals only |

### Metric Accessors

All accept `period_offset: int = 0` (0 = most recent, 1 = prior period, etc.).
All return `Optional[Union[int, float]]`. Strategy: concept-based first, label-based fallback.

| Method | Source Statement | Source |
|--------|-----------------|--------|
| `get_revenue(period_offset)` | income | `financials.py:326` |
| `get_net_income(period_offset)` | income | `financials.py:367` |
| `get_operating_income(period_offset)` | income | `financials.py:419` |
| `get_total_assets(period_offset)` | balance | `financials.py:452` |
| `get_total_liabilities(period_offset)` | balance | `financials.py:474` |
| `get_stockholders_equity(period_offset)` | balance | `financials.py:491` |
| `get_current_assets(period_offset)` | balance | `financials.py:576` |
| `get_current_liabilities(period_offset)` | balance | `financials.py:593` |
| `get_operating_cash_flow(period_offset)` | cashflow | `financials.py:510` |
| `get_capital_expenditures(period_offset)` | cashflow | `financials.py:547` |
| `get_free_cash_flow(period_offset)` | cashflow (derived) | `financials.py:529` |
| `get_shares_outstanding_basic(period_offset)` | income (concept) | `financials.py:677` |
| `get_shares_outstanding_diluted(period_offset)` | income (concept) | `financials.py:710` |

`get_free_cash_flow()` = `get_operating_cash_flow() - abs(get_capital_expenditures())`. Returns `None` if either component is `None`.

### Composite Accessor

| Method | Returns | Description | Source |
|--------|---------|-------------|--------|
| `get_financial_metrics()` | `Dict[str, Any]` | 13 named metrics + `current_ratio`, `debt_to_assets` | `financials.py:743` |

`get_financial_metrics()` keys: `revenue`, `operating_income`, `net_income`, `total_assets`, `total_liabilities`, `stockholders_equity`, `current_assets`, `current_liabilities`, `operating_cash_flow`, `capital_expenditures`, `free_cash_flow`, `shares_outstanding_basic`, `shares_outstanding_diluted`, `current_ratio`, `debt_to_assets`

### Utility Methods

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `get_currency_symbol()` | — | `str` | ISO 4217 symbol from XBRL units; defaults to `'$'` | `financials.py:827` |
| `to_context()` | — | `str` | AI-optimized string listing available actions and statements | `financials.py:853` |

---

## Nested Object: `AuditorInfo` (`edgar/company_reports/auditor.py:14`)

Accessed via `report.auditor` (cached_property). Returns `None` if no XBRL.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Auditor firm name (from `dei_AuditorName`) |
| `location` | `str` | Auditor office city/state (from `dei_AuditorLocation`) |
| `firm_id` | `int` | PCAOB firm ID (from `dei_AuditorFirmId`); `0` on parse error |
| `icfr_attestation` | `bool` | True if ICFR attestation present (from `dei_IcfrAuditorAttestationFlag`) |

---

## Nested Object: `Notes` (`edgar/xbrl/notes.py`)

Accessed via `report.notes` (cached_property). Hierarchical collection of `Note` objects.

| Operation | Description |
|-----------|-------------|
| `notes[5]` | Access by note number |
| `notes['Debt']` | Access by note title |
| `notes.search('topic')` | Fuzzy search returning matching `Note` objects |
| `for note in notes:` | Iterate all notes |

Each `Note` object has:

| Field | Type | Description |
|-------|------|-------------|
| `number` | `int` | Note number (e.g. 5 for "Note 5") |
| `title` | `str` | Note title |
| `short_name` | `str` | Short display name |
| `role` | `str` | XBRL presentation role URI |
| `statement` | `Optional[Statement]` | Top-level Statement for narrative text; `None` if unavailable |
| `tables` | `List[Statement]` | Child table Statements within this note |
| `policies` | `List[Statement]` | Accounting policy Statements within this note |
| `details` | `List[Statement]` | Detail Statements within this note |
| `menu_category` | `str` | Category for display grouping (default `'Notes'`) |
| `text` | `Optional[str]` | Note text content; `None` when `statement` is absent |
| `html` | `Optional[str]` | Raw HTML content from TextBlock tags; `None` when `statement` is absent |
| `table_count` | `int` | Number of child tables |
| `has_tables` | `bool` | Whether this note contains tables |
| `children` | `List[Statement]` | All child Statements (tables + policies + details) |
| `expands` | `List[str]` | Statement line item labels this note expands |
| `expands_concepts` | `List[str]` | Raw XBRL concept IDs that overlap with core financial statements |
| `to_context(detail)` | `str` | AI-optimized note content string |

---

## Nested Object: `Document` (`edgar/documents/`)

Accessed via `report.document` (cached_property). Parsed HTML structure.

| Field/Method | Type | Description |
|-------------|------|-------------|
| `sections` | `dict` | Keyed by part-qualified names (e.g. `'part_i_item_1'`) |
| `sections.get(key)` | `Optional[Section]` | Exact key lookup |
| `sections.get_item(key)` | `Optional[Section]` | Flexible lookup (`'Item 1'`, `'1A'`, `'1'`) |
| `text()` | `str` | Full document plain text |
| `tables` | `list` | All tables in document |
| `is_empty` | `bool` | True if no content parsed |

Each `Section` has `.text()` → `str`, `.item` → item number string.

---

## Nested Object: `Reports` (`edgar/sgml/filing_summary.py`)

Accessed via `report.reports` (cached_property). XBRL viewer report pages from FilingSummary.xml.

| Method | Returns | Description |
|--------|---------|-------------|
| `statements` | `Optional[Statements]` | Financial statement reports |
| `get_by_filename(filename)` | `Report` | Look up report by HTML filename |

---

## `MultiFinancials` (`edgar/financials.py:907`)

Wraps multiple XBRL instances for cross-period comparison.

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `MultiFinancials.extract(filings)` | iterable of `Filing` | `MultiFinancials` | Builds XBRLS from multiple filings | `financials.py:916` |
| `balance_sheet(view)` | `ViewType=None` | `Optional[StitchedStatement]` | Multi-period balance sheet | `financials.py:919` |
| `income_statement(view)` | `ViewType=None` | `Optional[StitchedStatement]` | Multi-period income statement | `financials.py:922` |
| `cashflow_statement(view)` | `ViewType=None` | `Optional[StitchedStatement]` | Multi-period cash flow statement | `financials.py:925` |
| `cash_flow_statement(**kwargs)` | — | `Optional[StitchedStatement]` | Alias for `cashflow_statement()` | `financials.py:928` |

No metric getters (`get_revenue()`, etc.) — use `StitchedStatement` objects directly.

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| No XBRL in filing | `financials` is `None`; all statement shortcuts return `None` |
| `financials` is `None` | `auditor` returns `None`; `notes` returns empty `Notes` |
| No DEI `dei_AuditorName` fact | `auditor` returns `None` |
| `document` parse fails | Subclasses may fall back to `chunked_document` internally |
| `get_free_cash_flow()` with missing component | Returns `None` |
| `period_offset` beyond available periods | All metric getters return `None` |
| `chunked_document` accessed | Emits `DeprecationWarning` (v5); removed in v6 |

---

## Access Patterns

- Standard entry: `filing.obj()` → `TenK(filing)` → all fields available
- Financial statements: `tenk.income_statement` → `Statement` → `.to_dataframe()`
- Quick metrics: `tenk.financials.get_revenue()`, `.get_net_income()`
- All metrics dict: `tenk.financials.get_financial_metrics()`
- Notes: `tenk.notes['Revenue']` or `tenk.notes[1]`
- Section text: `tenk['Item 1']` or `tenk['business']` (subclass-specific shortcuts)
- Search: `tenk.grep("going concern")` or `tenk.grep("impairment", document="primary")`
- AI context: `tenk.to_context('standard')` or `tenk.to_context('full', focus='debt')`
- Auditor: `tenk.auditor.name`, `tenk.auditor.firm_id`
