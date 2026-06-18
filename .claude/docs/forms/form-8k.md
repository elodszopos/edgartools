# Form 8-K — Current Report

**SEC form codes**: `8-K`, `8-K/A`
**Python class**: `CurrentReport` (extends `CompanyReport`); `EightK = CurrentReport` (module-level alias)
**Access**: `filing.obj()` → `CurrentReport` or `EightK`
**Base fields**: See `reports-financials.md` § CompanyReport — `filing_date`, `form`, `company`, `period_of_report`, `financials`, `notes`, `reports`, `auditor`, `grep()`, `view()`
**Source**: `edgar/company_reports/current_report.py`

---

## Complete Field Reference

### From CompanyReport (inherited — do not re-read from here)

See `reports-financials.md` § CompanyReport. Key inherited fields:
- `filing_date`, `form`, `company`, `period_of_report` — immediate, no network
- `financials` (cached_property) → `None` for most 8-Ks (only DEI XBRL present)
- `notes`, `reports`, `auditor` — cached_property; require XBRL (almost always None for 8-K)
- `grep(pattern, regex, document)` → `GrepResult`
- `doc` → alias for `document`

### 8-K-Specific Fields

#### Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `document` | `Document\|None` | cached (HTML parse) | HTMLParser form='8-K'; 95% section detection rate — `current_report.py:318` |
| `sections` | `dict` | delegated to `document` | Sections dict from new parser; keys like `'item_502'`; empty dict if `document` is None — `current_report.py:339` |
| `content_type` | `str` | cached | Classifies filing: `'earnings'`, `'cybersecurity'`, `'restructuring'`, `'asset_change'`, `'auditor_change'`, `'shareholder_vote'`, `'material_agreement'`, `'director_change'`, `'governance'`, `'debt_offering'`, `'regulation_fd'`, `'other'` — `current_report.py:357` |
| `is_amendment` | `bool` | immediate | `True` when `filing.form == '8-K/A'` — `current_report.py:399` |
| `has_press_release` | `bool` | triggers `items` + `press_releases` | `True` if Item 2.02 present AND `press_releases` is not None; Item 7.01-only excluded — `current_report.py:435` |
| `has_earnings` | `bool` | triggers `items` + `earnings` | `True` if Item 2.02 present AND `earnings` is not None — `current_report.py:446` |
| `earnings` | `EarningsRelease\|None` | cached (network) | Parses EX-99.x HTML tables; None if no earnings exhibit found — `current_report.py:466` |
| `income_statement` | `FinancialTable\|None` | delegates to `earnings` | Shortcut: `earnings.income_statement`; NOT from XBRL — `current_report.py:494` |
| `balance_sheet` | `FinancialTable\|None` | delegates to `earnings` | Shortcut: `earnings.balance_sheet`; NOT from XBRL — `current_report.py:509` |
| `cash_flow_statement` | `FinancialTable\|None` | delegates to `earnings` | Shortcut: `earnings.cash_flow_statement`; NOT from XBRL — `current_report.py:525` |
| `press_releases` | `PressReleases\|None` | queries attachments | EX-99, EX-99.1, EX-99.01 `.htm` docs; EX-99.2 excluded — `current_report.py:594` |
| `items` | `List[str]` | 3-tier fallback | Returns `['Item 2.02', 'Item 9.01', ...]`; see fallback chain below — `current_report.py:626` |
| `date_of_report` | `str` | immediate (from header) | `period_of_report` formatted as `"June 30, 2025"`; empty string if not set — `current_report.py:735` |
| `chunked_document` | `ChunkedDocument\|None` | cached (HTML parse) | Legacy parser; used internally as fallback; `CurrentReport` overrides this property so no DeprecationWarning is emitted (only the base class `CompanyReport.chunked_document` warns); planned for removal in v6.0 — `current_report.py:609` |
| `doc` | `ChunkedDocument\|None` | delegated to `chunked_document` | Alias; points to legacy parser on 8-K (differs from base class which returns `document`) — `current_report.py:622` |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `__getitem__(item_name)` | `item_name: str` | `str\|None` | 3-tier lookup: new parser sections → chunked_document → text extraction; accepts `'item_502'`, `'Item 5.02'`, `'5.02'` — `current_report.py:670` |
| `get_exhibit(exhibit_type)` | `exhibit_type: str` | `Attachment\|None` | Exact `document_type` match, e.g. `'EX-99.1'` — `current_report.py:403` |
| `get_exhibits(prefix)` | `prefix: str\|None = None` | `List[Attachment]` | Non-XBRL, non-primary exhibits; filter by type prefix e.g. `'EX-99'`; skips EX-101, GRAPHIC, HTML, JS, CSS, XML, JSON, ZIP — `current_report.py:415` |
| `get_income_statement(default)` | `default=None` | `pd.DataFrame` | Safe accessor; returns empty DataFrame if no income statement; pass custom default — `current_report.py:541` |
| `get_balance_sheet(default)` | `default=None` | `pd.DataFrame` | Safe accessor; returns empty DataFrame if no balance sheet — `current_report.py:561` |
| `get_cash_flow_statement(default)` | `default=None` | `pd.DataFrame` | Safe accessor; returns empty DataFrame if no cash flow — `current_report.py:577` |
| `view(item_or_part)` | `item_or_part: str` | `None` | Prints item text to console — `current_report.py:728` |
| `text()` | — | `str` | Full text including all exhibit content (not just primary document) — `current_report.py:780` |
| `to_context(detail)` | `detail: str = 'standard'` | `str` | AI-optimized string; `'minimal'` (~100 tokens), `'standard'` (~300), `'full'` (~500+) — `current_report.py:818` |

---

## `items` Property — 3-Tier Fallback Chain

| Priority | Strategy | Condition | Handles |
|----------|----------|-----------|---------|
| 1 | New HTMLParser (`document.sections`) | ~95% of modern filings | Validates that items contain decimal (e.g., `'8.01'`); rejects if only non-decimal items found |
| 2 | ChunkedDocument (`chunked_document.list_items()`) | Legacy fallback | Older 8-K format |
| 3 | Text-based extraction (`_extract_items_from_text`) | All eras incl. SGML 1999-2001 | 100% accuracy on `filing.text()` output |

Returns: `['Item 2.02', 'Item 9.01']` — always `'Item X.XX'` format.

---

## All 33 8-K Items

| Item Code | Title |
|-----------|-------|
| 1.01 | Entry into a Material Definitive Agreement |
| 1.02 | Termination of a Material Definitive Agreement |
| 1.03 | Bankruptcy or Receivership |
| 1.04 | Mine Safety Disclosures |
| 1.05 | Material Cybersecurity Incidents |
| 2.01 | Completion of Acquisition or Disposition of Assets |
| 2.02 | Results of Operations and Financial Condition |
| 2.03 | Creation of a Direct Financial Obligation or Off-Balance Sheet Arrangement |
| 2.04 | Triggering Events That Accelerate or Increase a Direct Financial Obligation |
| 2.05 | Costs Associated with Exit or Disposal Activities |
| 2.06 | Material Impairments |
| 3.01 | Notice of Delisting or Failure to Satisfy Continued Listing Rule; Transfer of Listing |
| 3.02 | Unregistered Sales of Equity Securities |
| 3.03 | Material Modification to Rights of Security Holders |
| 4.01 | Changes in Registrant's Certifying Accountant |
| 4.02 | Non-Reliance on Previously Issued Financial Statements |
| 5.01 | Changes in Control of Registrant |
| 5.02 | Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers |
| 5.03 | Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year |
| 5.04 | Temporary Suspension of Trading Under Registrant's Employee Benefit Plans |
| 5.05 | Amendment to Registrant's Code of Ethics, or Waiver of a Provision |
| 5.06 | Change in Shell Company Status |
| 5.07 | Submission of Matters to a Vote of Security Holders |
| 5.08 | Shareholder Director Nominations |
| 6.01 | ABS Informational and Computational Material |
| 6.02 | Change of Servicer or Trustee |
| 6.03 | Change in Credit Enhancement or Other External Support |
| 6.04 | Failure to Make a Required Distribution |
| 6.05 | Securities Act Updating Disclosure |
| 7.01 | Regulation FD Disclosure |
| 8.01 | Other Events |
| 9.01 | Financial Statements and Exhibits |

---

## Nested Objects

### `ItemOnlyFilingStructure` (`edgar/company_reports/_structures.py:31`)

Flat item-keyed dict — no Parts. Extends `FilingStructure` but `get_part()` always returns `None`.

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get_item(item, part)` | `item: str`, `part=None` | `dict\|None` | Looks up `item.upper()` directly; returns dict with `Title` and `Description` keys |
| `get_part(part)` | `part: str` | `None` | Always returns None — 8-K has no Parts |
| `is_valid_item(item, part)` | `item: str`, `part=None` | `bool` | True if item in structure |

Item dict schema: `{'Title': str, 'Description': str}`

---

### `PressReleases` (`edgar/company_reports/press_release.py:12`)

Wraps filtered `Attachments` of EX-99 HTML press release docs.

| Field/Method | Type | Description |
|-------------|------|-------------|
| `attachments` | `Attachments` | Underlying filtered attachments |
| `__getitem__(item)` | `PressRelease\|None` | By 0-based index; returns `PressRelease` wrapping the attachment |
| `__len__()` | `int` | Number of press release attachments |

---

### `PressRelease` (`edgar/company_reports/press_release.py:35`)

Wraps a single `Attachment` from an 8-K press release exhibit.

| Field/Method | Type | Description |
|-------------|------|-------------|
| `attachment` | `Attachment` | Underlying attachment object |
| `document` (property) | `str` | Filename from `attachment.document` |
| `description` (property) | `str` | Description from `attachment.description` |
| `url()` | `str` | URL from `attachment.url` |
| `html()` | `str\|None` | Raw HTML with instance-level cache; downloads from EDGAR on first call |
| `text()` | `str\|None` | Plain text via `HtmlDocument.from_html(html, extract_data=False).text` |
| `to_markdown()` | `MarkdownContent` | Markdown via `MarkdownContent.from_html(html, title="8-K Press Release")` |
| `view()` | — | Renders markdown to console |
| `open()` | — | Opens in browser via `attachment.open()` |

---

### `EarningsRelease` (`edgar/earnings.py:922`)

Parses HTML tables from 8-K EX-99 exhibits. Does NOT use XBRL.

| Field | Type | Description |
|-------|------|-------------|
| `attachment` | `Attachment` | Source EX-99.x attachment |

#### EarningsRelease Properties

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `document` | `Document\|None` | cached on first access | Parsed via `parse_html(html_content)` from attachment — `earnings.py:988` |
| `detected_scale` | `Scale` | cached (`_scale`) | Parenthetical patterns `(in millions)`, `(in thousands)`, `(in billions)` in document text; avoids bare-word false positives — `earnings.py:1005` |
| `tables` | `List[FinancialTable]` | cached (`_tables`) | All extracted tables incl. DEFINITIONS — `earnings.py:1029` |
| `financial_tables` | `List[FinancialTable]` | delegates to `tables` | Excludes `StatementType.DEFINITIONS` — `earnings.py:1036` |
| `income_statement` | `FinancialTable\|None` | delegates to `tables` | Largest INCOME_STATEMENT table by row count — `earnings.py:1057` |
| `balance_sheet` | `FinancialTable\|None` | delegates to `tables` | First BALANCE_SHEET table — `earnings.py:1065` |
| `cash_flow_statement` | `FinancialTable\|None` | delegates to `tables` | First CASH_FLOW table — `earnings.py:1073` |
| `segment_data` | `FinancialTable\|None` | delegates to `tables` | First SEGMENT_DATA table — `earnings.py:1081` |
| `eps_reconciliation` | `FinancialTable\|None` | delegates to `tables` | First EPS_RECONCILIATION table — `earnings.py:1089` |
| `guidance` | `FinancialTable\|None` | delegates to `tables` | First GUIDANCE table — `earnings.py:1097` |

#### EarningsRelease Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing(filing)` | `filing: Filing` | `EarningsRelease\|None` | Class method; tries EX-99.1 first; if no income statement falls back through EX-99.* exhibits — `earnings.py:952` |
| `get_financial_tables(min_rows, min_cols)` | `min_rows=3`, `min_cols=2` | `List[FinancialTable]` | `financial_tables` filtered by minimum dimensions — `earnings.py:1040` |
| `get_key_metrics(quarterly)` | `quarterly=True` | `dict` | Returns `{revenue, net_income, eps_basic, eps_diluted, period, scale}`; prefers 3-month columns when `quarterly=True` — `earnings.py:1104` |
| `to_facts_dataframe()` | — | `pd.DataFrame` | Combines all `financial_tables` into single facts DataFrame; adds `source_statement` column — `earnings.py:1210` |
| `summary()` | — | `str` | Text summary listing available statements and shapes — `earnings.py:1302` |
| `to_context(detail)` | `detail='standard'` | `str` | AI-optimized string; `'minimal'`: income only; `'standard'`: income + balance sheet; `'full'`: all statements — `earnings.py:1324` |

---

### `FinancialTable` (`edgar/earnings.py:449`)

Dataclass. Single parsed financial table from earnings release HTML.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dataframe` | `pd.DataFrame` | required | Parsed table; index = row labels; columns = period headers |
| `scale` | `Scale` | `Scale.UNITS` | Detected scale factor applied to AMOUNT rows |
| `title` | `Optional[str]` | `None` | Table title if detected from header |
| `statement_type` | `StatementType` | `StatementType.UNKNOWN` | Classified type |
| `periods` | `List[str]` | `[]` | Column headers containing year patterns (period labels) |
| `raw_index` | `int` | `0` | Original table position in document |
| `row_types` | `list\|dict` | `[]` | Positional `List[RowType]` (preferred) or legacy `dict[label, RowType]` |

#### FinancialTable Properties

| Property | Type | Description |
|----------|------|-------------|
| `per_share_rows` | `pd.DataFrame` | Slice of rows classified as `RowType.PER_SHARE` |
| `scaled_dataframe` | `pd.DataFrame` | Copy with AMOUNT rows multiplied by `scale.value`; PER_SHARE/SHARES/PERCENTAGE rows unchanged |

#### FinancialTable Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get_row_type(label, position)` | `label: str`, `position: int = -1` | `RowType` | Positional lookup when `row_types` is list (handles duplicate labels e.g., two 'Basic' rows) — `earnings.py:478` |
| `get_raw_labels()` | — | `List[str]` | Raw row label strings for AI standardization |
| `to_html(include_title, classes)` | `include_title=True`, `classes="financial-table"` | `str` | XSS-safe HTML with optional caption — `earnings.py:536` |
| `to_json(include_metadata)` | `include_metadata=True` | `str` | JSON with `data` dict + optional `metadata` dict — `earnings.py:573` |
| `to_markdown(include_context)` | `include_context=True` | `str` | Markdown for AI input; includes scale and period context — `earnings.py:607` |
| `to_context(detail)` | `detail='standard'` | `str` | AI-optimized string; `'minimal'`: top 10 rows key metrics; `'standard'`: 15 rows; `'full'`: all rows — `earnings.py:634` |
| `to_csv()` | — | `str` | CSV string via clean column names — `earnings.py:689` |
| `to_facts_dataframe()` | — | `pd.DataFrame` | Facts schema compatible with `EntityFacts.to_dataframe()` — `earnings.py:703` |
| `with_standardized_labels(label_mapping)` | `label_mapping: dict\|None` | `FinancialTable` | New table with renamed index labels; original unchanged — `earnings.py:774` |
| `with_clean_columns(column_names)` | `column_names: List[str]\|None` | `FinancialTable` | New table with cleaned/renamed columns; auto-cleans period headers to 'Q4 2025', 'FY 2025' if None — `earnings.py:804` |
| `__bool__()` | — | `bool` | `True` if `not self.dataframe.empty` |

---

### `Scale` (`edgar/earnings.py:60`)

| Member | Value | Description |
|--------|-------|-------------|
| `UNITS` | 1 | Raw values (no scaling) |
| `THOUSANDS` | 1,000 | Values in thousands |
| `MILLIONS` | 1,000,000 | Values in millions |
| `BILLIONS` | 1,000,000,000 | Values in billions |

| Class method | Parameters | Returns | Description |
|-------------|-----------|---------|-------------|
| `Scale.detect(text)` | `text: str` | `Scale` | Word-boundary regex match; priority: BILLIONS > MILLIONS > THOUSANDS > UNITS |

---

### `StatementType` (`edgar/earnings.py:87`)

| Member | Value | Description |
|--------|-------|-------------|
| `INCOME_STATEMENT` | `"income_statement"` | P&L / results of operations |
| `BALANCE_SHEET` | `"balance_sheet"` | Financial position |
| `CASH_FLOW` | `"cash_flow"` | Cash flow statement |
| `SEGMENT_DATA` | `"segment_data"` | Business unit breakdown |
| `EPS_RECONCILIATION` | `"eps_reconciliation"` | GAAP to Non-GAAP EPS bridge |
| `GAAP_RECONCILIATION` | `"gaap_reconciliation"` | GAAP to non-GAAP reconciliation |
| `KEY_METRICS` | `"key_metrics"` | Summary metrics table |
| `GUIDANCE` | `"guidance"` | Forward-looking outlook |
| `DEFINITIONS` | `"definitions"` | Non-GAAP definitions (excluded from `financial_tables`) |
| `UNKNOWN` | `"unknown"` | Unclassified |

---

### `RowType` (`edgar/earnings.py:101`)

| Member | Value | Description | Scaling |
|--------|-------|-------------|---------|
| `AMOUNT` | `"amount"` | Dollar amounts (revenue, expenses, income) | Scaled by `Scale.value` |
| `PER_SHARE` | `"per_share"` | EPS, dividends per share | Not scaled |
| `SHARES` | `"shares"` | Share counts, weighted average | Not scaled |
| `PERCENTAGE` | `"percentage"` | Ratios, margins, rates | Not scaled |
| `OTHER` | `"other"` | Labels, headers, unclassifiable | Not scaled |

---

## DataFrame Schemas

### `FinancialTable.dataframe` columns

| Column | Type | Description |
|--------|------|-------------|
| (index) | `str` | Row label (line item name, e.g. `"Net revenue"`) |
| (period headers) | `float\|str\|None` | One column per detected period; values are numeric (float) or None for missing/dash cells |

Column names are raw period strings, e.g. `"Three Months Ended - December 28, 2024"`. Use `.with_clean_columns()` or `._display_dataframe()` to get shortened names.

---

### `FinancialTable.to_facts_dataframe()` columns

| Column | Type | Description |
|--------|------|-------------|
| `concept` | `str` | XBRL concept name from `concept_mappings.json` reverse lookup, or PascalCase label |
| `label` | `str` | Original row label as appears in filing |
| `value` | `str` | String representation of raw cell value |
| `numeric_value` | `float` | Parsed numeric value; AMOUNT rows scaled by `Scale.value` |
| `unit` | `str` | `'USD'`, `'USD/shares'`, `'shares'`, or `'pure'` (from RowType) |
| `period_type` | `str\|None` | `'duration'` or `'instant'`; None if header unparseable |
| `period_start` | `date\|None` | Start date for duration periods; None for instant |
| `period_end` | `date\|None` | End/as-of date |
| `fiscal_year` | `int\|None` | Calendar year of period end |
| `fiscal_period` | `str\|None` | `'Q1'`–`'Q4'`, `'H1'`, `'H2'`, `'9M'`, `'FY'`, or None |

---

### `EarningsRelease.to_facts_dataframe()` columns

Same as `FinancialTable.to_facts_dataframe()` plus:

| Column | Type | Description |
|--------|------|-------------|
| `source_statement` | `str` | `StatementType.value` of the originating table |

---

### `EarningsRelease.get_key_metrics()` return dict

| Key | Type | Description |
|-----|------|-------------|
| `revenue` | `float\|None` | First revenue-pattern match, scaled to actual USD |
| `net_income` | `float\|None` | First net income match, scaled to actual USD |
| `eps_basic` | `float\|None` | Basic EPS (not scaled — per-share value) |
| `eps_diluted` | `float\|None` | Diluted EPS (not scaled) |
| `period` | `str\|None` | Column header string of selected period |
| `scale` | `Scale\|None` | `Scale` enum of income statement |

---

## Module-Level Functions (`edgar/earnings.py`)

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `get_earnings_tables(filing)` | `filing: Filing` | `List[FinancialTable]` | Convenience: `EarningsRelease.from_filing(filing).financial_tables` or `[]` — `earnings.py:1365` |
| `find_earnings_exhibit(attachments)` | `attachments: Attachments` | `Attachment\|None` | First EX-99.* HTML attachment — `earnings.py:1417` |
| `find_earnings_exhibits(attachments)` | `attachments: Attachments` | `List[Attachment]` | All EX-99.* HTML attachments sorted by exhibit number — `earnings.py:1381` |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form` not in `['8-K', '8-K/A']` | `AssertionError` raised in `__init__` |
| No HTML in filing | `document` is `None`; `sections` returns `{}`; `items` falls through to text extraction |
| No EX-99.x attachment | `earnings` is `None`; `has_earnings` is `False`; `income_statement/balance_sheet/cash_flow_statement` are all `None` |
| EX-99.x has no parseable income statement | `earnings` returns first exhibit anyway; `income_statement` is `None` |
| `get_income_statement()` with no earnings | Returns empty `pd.DataFrame()` (not None) |
| `press_releases` with no matching attachments | Returns `None` |
| `has_press_release` on Item 7.01-only filing | Returns `False` even if EX-99.1 present |
| `date_of_report` with no `period_of_report` | Returns empty string `""` |
| `EarningsRelease.document` attachment content is None | Returns `None`; logs warning |
| `FinancialTable.__bool__()` | `False` if `dataframe.empty` — always check truthiness before accessing |
| `financials` (inherited) | `None` for virtually all 8-Ks (only DEI XBRL present); `auditor` and `notes` also `None` |

---

## Access Patterns

- `filing.obj()` → `EightK` instance
- Check if earnings 8-K: `'2.02' in eight_k.items` (semantic) or `eight_k.has_earnings` (parseable data confirmed)
- Access item text: `eight_k['Item 5.02']` or `eight_k['5.02']` or `eight_k['item_502']`
- Earnings drill-down: `eight_k.earnings.income_statement.dataframe`
- Safe earnings access: `eight_k.get_income_statement()` → `pd.DataFrame` (empty if missing)
- Scale-correct values: `eight_k.earnings.income_statement.scaled_dataframe`
- Facts schema merge: `eight_k.earnings.to_facts_dataframe()` for EntityFacts-compatible output
- Press release text: `eight_k.press_releases[0].text()`
- Exhibit access: `eight_k.get_exhibit('EX-10.1')` → `Attachment`
- All exhibits: `eight_k.get_exhibits('EX-99')` → `List[Attachment]`
- content_type routing: `eight_k.content_type == 'earnings'` before accessing earnings subsystem

---

## Key Gotchas

| Gotcha | Detail |
|--------|--------|
| Financial statements are NOT from XBRL | `income_statement`, `balance_sheet`, `cash_flow_statement` come from `EarningsRelease` (HTML table parse), not XBRL. `eight_k.financials` is `None` for most filings. |
| `doc` alias differs from base class | Base `CompanyReport.doc` returns `document` (new parser). 8-K overrides `doc` to return `chunked_document` (legacy parser) — `current_report.py:622` |
| `scaled_dataframe` vs `dataframe` | `dataframe` has raw values (e.g., `395` for $395M). `scaled_dataframe` multiplies AMOUNT rows by scale. Always check `scale` before interpreting raw values. |
| `get_key_metrics` scaling | `revenue` and `net_income` are already scaled to actual USD. `eps_basic`/`eps_diluted` are NOT scaled (per-share values). |
| Duplicate row labels | Two rows can have identical labels (e.g., `'Basic'` for EPS and for shares). Use `get_row_type(label, position)` with the positional index, not just the label. |
| Item 7.01 + EX-99 ≠ press release | `has_press_release` returns `False` for Item 7.01-only filings even when EX-99.1 is present — investor presentations excluded. |
| Amendment detection | `eight_k.is_amendment` checks `filing.form == '8-K/A'`. Both `8-K` and `8-K/A` instantiate `CurrentReport`. |
| Legacy SGML items (1999-2001) | Item list uses integer format `'Item 1'`, `'Item 4'` not decimal `'Item 1.01'` — validated by checking for dot in item string |
