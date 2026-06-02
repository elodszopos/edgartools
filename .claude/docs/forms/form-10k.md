# Form 10-K — Annual Report

**SEC form codes**: 10-K, 10-K/A
**Python class**: `TenK` (extends `CompanyReport`)
**Access**: `filing.obj()` → `TenK`
**Base fields**: See `_base-filing.md` (Filing fields), `_base-company-report.md` (CompanyReport fields)
**Source**: `edgar/company_reports/ten_k.py`

---

## Complete Field Reference

### From Filing (inherited)

See `_base-filing.md` — `cik`, `company`, `form`, `filing_date`, `accession_no`, `period_of_report`, `html()`, `xbrl()`, `attachments`, and all Filing methods.

### From CompanyReport (inherited)

See `_base-company-report.md` — `financials`, `income_statement`, `balance_sheet`, `cash_flow_statement`, `auditor`, `notes`, `reports`, `grep()`, `view()`, `to_context()`, `_focused_context()`.

### TenK-Specific Fields

#### Class-level attributes

| Field | Type | Description |
|-------|------|-------------|
| `structure` | `FilingStructure` | Parts I-IV with Items 1–16; class-level, shared by all instances. See `ten_k.py:63` |

#### Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `document` | `Document\|None` | cached/network | `HTMLParser(ParserConfig(form='10-K'))` parse of filing HTML; returns `None` on parse failure, triggering `chunked_document` fallback. See `ten_k.py:181` |
| `sections` | `Sections\|{}` | no (plain @property, recomputes each access via `document.sections`) | Dict of section keys → `Section` objects from `document.sections`; empty dict if `document` is None. Keys are part-qualified (e.g., `part_i_item_1`) or friendly names (e.g., `business`, `mda`, `risk_factors`). See `ten_k.py:213` |
| `items` | `List[str]` | no (plain @property, recomputes each access) | Section names in `"Item X"` format in canonical SEC order (1, 1A, 1B, 1C, 2, 3 … 15, 16); deduplicated and sorted by `_item_sort_key` (numeric then full token); falls back to `chunked_document.list_items()` when sections is empty. See `ten_k.py:248` |
| `business` | `str\|None` | no (plain @property, delegates to `__getitem__`) | Shortcut for `self['Item 1']` — Part I Item 1 Business. See `ten_k.py:293` |
| `risk_factors` | `str\|None` | no (plain @property, delegates to `__getitem__`) | Shortcut for `self['Item 1A']` — Part I Item 1A Risk Factors. See `ten_k.py:296` |
| `management_discussion` | `str\|None` | no (plain @property, delegates to `__getitem__`) | Shortcut for `self['Item 7']` — Part II Item 7 MD&A. See `ten_k.py:299` |
| `directors_officers_and_governance` | `str\|None` | no (plain @property, delegates to `__getitem__`) | Shortcut for `self['Item 10']` — Part III Item 10. See `ten_k.py:303` |
| `subsidiaries` | `SubsidiaryList\|None` | cached/network | Scans `_filing.attachments` for first `EX-21*` exhibit; parses HTML via `parse_subsidiaries()`; returns `None` if no EX-21 exhibit. See `ten_k.py:308` |
| `chunked_document` | `ChunkedDocument` | cached/network | Legacy HTML parser; used as fallback by `items` and `__getitem__`; planned for removal in v6.0 but TenK override does NOT emit `DeprecationWarning` (only base class version does). See `ten_k.py:328` |
| `_cross_reference_index` | `CrossReferenceIndex\|None` | cached/network | Detects Cross Reference Index format (GE, Henry Schein style); `None` if not present. See `ten_k.py:331` |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `__getitem__` | `item_or_part: str` | `str\|None` | 5-priority lookup chain (see below). See `ten_k.py:505` |
| `get_item_with_part` | `part: str`, `item: str`, `markdown: bool = True` | `str\|None` | Explicit part+item lookup; for 10-K items are unique across parts so `part` is largely ignored. Delegates to `__getitem__` then falls back to `chunked_document.get_item_with_part()`. See `ten_k.py:674` |
| `get_structure` | — | `rich.tree.Tree` | Rich tree of Parts/Items with presence indicators (green=found, grey=absent). See `ten_k.py:709` |
| `id_parse_document` | `markdown: bool = False` | `dict` | HTML ID-based parse via `ParsedHtml10K`; result cached in `_id_parse_cache`. See `ten_k.py:352` |
| `to_context` | `detail: str = 'standard'`, `focus: str\|list[str]\|None = None` | `str` | AI-optimized string; `'minimal'`/`'standard'`/`'full'`; `focus` triggers `_focused_context()`. See `ten_k.py:365` |
| `__str__` | — | `str` | `"TenK('CompanyName')"`. See `ten_k.py:362` |
| `__rich__` | — | `rich.Panel` | Rich panel with periods, structure tree, and financials. See `ten_k.py:745` |

---

## __getitem__ Lookup Chain

Applied in order; returns on first match.

| Priority | Strategy | Example input → key tried |
|----------|----------|--------------------------|
| 1 | Part-canonical key (`part_{roman}_item_{n}`) | `'Item 1'` → `part_i_item_1` |
| 1.5 | Combined-items keys (e.g., `items_1_and_2`) | `'Item 1'` → `part_i_items_1_and_2` |
| 2 | Direct key in `sections` | `'business'` |
| 3 | Friendly name → Item mapping | `'business'` → `'Item 1'` |
| 4 | `'Item X'` → friendly name lookup | `'Item 7'` → `'mda'` |
| 5 | Short format `'1'`/`'1A'` → `'Item X'` | `'7'` → `'Item 7'` |
| fallback | Cross Reference Index (if detected) | for GE/Henry Schein style |
| fallback | `chunked_document[item_or_part]` (planned for removal in v6.0, no DeprecationWarning emitted) | last resort |

Item-to-Part mapping (`_ITEM_TO_PART_10K`) constrains lookup to SEC-canonical Part, preventing wrong-Part fallback (GH #821).

---

## Item Structure (Parts I-IV)

| Part | Items | Key topics |
|------|-------|------------|
| Part I | 1, 1A, 1B, 1C, 2, 3, 4 | Business, Risk Factors, Unresolved Staff Comments, Cybersecurity, Properties, Legal Proceedings, Mine Safety |
| Part II | 5, 6, 7, 7A, 8, 9, 9A, 9B, 9C | Market for Equity, Selected Financial Data, MD&A, Market Risk, Financial Statements, Controls and Procedures, Other Information, Foreign Jurisdictions |
| Part III | 10, 11, 12, 13, 14 | Directors/Officers/Governance, Executive Compensation, Security Ownership, Related Transactions, Accounting Fees |
| Part IV | 15, 16 | Exhibits/Financial Statement Schedules, Form 10-K Summary |

---

## Nested Objects

### SubsidiaryList (`edgar/company_reports/subsidiaries.py:63`)

Accessed via `tenk.subsidiaries`. Iterable container over `Subsidiary` objects.

| Field/Method | Type | Description |
|-------------|------|-------------|
| `__len__` | `int` | Count of subsidiaries |
| `__iter__` | `Iterator[Subsidiary]` | Iterate subsidiaries |
| `__getitem__(item)` | `Subsidiary` | Index access |
| `to_dataframe()` | `pd.DataFrame` | See schema below |
| `__rich__` | `rich.Table` | Rich table display |

### Subsidiary (`edgar/company_reports/subsidiaries.py:50`)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Legal entity name (footnote markers stripped) |
| `jurisdiction` | `str` | State or country of incorporation |
| `ownership_pct` | `Optional[float]` | Ownership percentage; `None` if not in EX-21 table |

### FilingStructure (`edgar/company_reports/_structures.py:7`)

Class-level (`TenK.structure`); not per-instance.

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get_part(part)` | `part: str` | `dict\|None` | Returns items dict for part (case-insensitive) |
| `get_item(item, part=None)` | `item: str`, `part: Optional[str]` | `dict\|None` | Returns item metadata dict with `Title` and `Description` keys |
| `is_valid_item(item, part=None)` | `item: str`, `part: Optional[str]` | `bool` | True if item exists in structure |

Item metadata dict keys: `Title` (str), `Description` (str).

---

## DataFrame Schemas

### `subsidiaries.to_dataframe()` columns

| Column | Type | Notes |
|--------|------|-------|
| `name` | `str` | Always present |
| `jurisdiction` | `str` | Always present |
| `ownership` | `float` | Only present if at least one subsidiary has `ownership_pct` set |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form` not in `['10-K', '10-K/A']` | `AssertionError` raised in `__init__` |
| `document` parse failure | `RuntimeWarning` emitted; `document` returns `None`; falls back to `chunked_document` |
| No EX-21 attachment | `subsidiaries` returns `None` |
| EX-21 exists but no parseable tables | `subsidiaries` returns empty `SubsidiaryList` |
| `financials` is `None` (no XBRL) | `income_statement`, `balance_sheet`, `cash_flow_statement` return `None`; `auditor` returns `None` |
| `__getitem__` finds no match | Returns `None` |
| `_cross_reference_index` HTML parse | Never raises; returns `None` if format not detected |

---

## TOC Analyzer Behavior for 10-K

| Behavior | Detail |
|----------|--------|
| Part inference from item number | When TOC lacks explicit Part headers, `_make_section_key` infers part from `TEN_K_SCHEMA.item_part_ranges`: 1–4→Part I, 5–9→Part II, 10–14→Part III, 15–16→Part IV |
| Single-letter suffix support | `_canonical_item_count` regex `item_\d+[a-z]?` matches company-specific items like `Item 1D` (Caterpillar Executive Officers) in addition to standard 1A/1B/1C/7A/9A-9C |
| Body-header fallback | For link-less TOC filings (Goldman Sachs, Citigroup): when linked-TOC result yields < 8 canonical items, scans bold body headings matching `^Item N[letter]. Title` for anchors |
| Text keyword vocabulary | `TEN_K_SCHEMA.text_rules` maps: Business→Item 1, Risk Factors→Item 1A, Properties→Item 2, Legal Proceedings→Item 3, MD&A→Item 7, Financial Statements→Item 8, Exhibits→Item 15 |
| Bare-item cap | `max_bare_item=15` for 10-K; page numbers > 15 are not misidentified as item numbers |

## Access Patterns

- Get TenK: `tenk = filing.obj()` (or `TenK(filing)` directly)
- Read a section: `tenk['Item 7']` or `tenk.management_discussion`
- Disambiguate via part: `tenk.get_item_with_part('Part II', 'Item 7')`
- Subsidiaries: `tenk.subsidiaries` → `SubsidiaryList` → `.to_dataframe()`
- Financial statements: `tenk.financials.income_statement()`
- Structure tree: `tenk.get_structure()` (Rich display)
- AI context: `tenk.to_context('full', focus='debt')`
