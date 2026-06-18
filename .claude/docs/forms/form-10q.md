# Form 10-Q — Quarterly Report

**SEC form codes**: 10-Q, 10-Q/A
**Python class**: `TenQ` (extends `CompanyReport`)
**Access**: `filing.obj()` → `TenQ`
**Base fields**: See `_base-filing.md` (Filing fields), `_base-company-report.md` (CompanyReport fields)
**Source**: `edgar/company_reports/ten_q.py`

---

## Complete Field Reference

### From Filing (inherited)

See `_base-filing.md` — `cik`, `company`, `form`, `filing_date`, `accession_no`, `period_of_report`, `html()`, `xbrl()`, `attachments`, and all Filing methods.

### From CompanyReport (inherited)

See `_base-company-report.md` — `financials`, `income_statement`, `balance_sheet`, `cash_flow_statement`, `auditor`, `notes`, `reports`, `grep()`, `view()`, `to_context()`, `_focused_context()`.

### TenQ-Specific Fields

#### Class-level attributes

| Field | Type | Description |
|-------|------|-------------|
| `structure` | `FilingStructure` | Parts I-II with their items; class-level, shared by all instances. See `ten_q.py:23` |

#### Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `document` | `Document\|None` | cached/network | `HTMLParser(ParserConfig(form='10-Q'))` parse of filing HTML; returns `None` if no HTML. See `ten_q.py:203` |
| `sections` | `Sections\|{}` | no (plain `@property`, recomputes each call; backing `document` is cached) | Dict of part-qualified section keys → `Section` objects; empty dict if `document` is None. Keys always part-qualified (e.g., `part_i_item_1`, `part_ii_item_1`). See `ten_q.py:225` |
| `items` | `List[str]` | no (plain `@property`, recomputes each call) | Part-qualified item names (e.g., `['Part I, Item 1', 'Part II, Item 1']`); falls back to `chunked_document.list_items()` when sections is empty. See `ten_q.py:245` |
| `chunked_document` | `ChunkedDocument` | cached/network | Legacy HTML parser; fallback for `items` and `__getitem__`. See `ten_q.py:455` |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `__getitem__` | `item_or_part: str` | `str\|None` | Multi-format lookup; Part I is default for unqualified `'Item 1'` (backward compat). See `ten_q.py:292` |
| `get_item_with_part` | `part: str`, `item: str`, `markdown: bool = True` | `str\|None` | Explicit part+item lookup — critical for disambiguation (Part I Item 1 ≠ Part II Item 1). See `ten_q.py:389` |
| `get_structure` | — | `rich.tree.Tree` | Rich tree of Parts/Items with presence indicators. See `ten_q.py:458` |
| `id_parse_document` | `markdown: bool = True` | `dict` | HTML ID-based parse via `ParsedHtml10Q`; result cached in `_id_parse_cache`. See `ten_q.py:444` |
| `to_context` | `detail: str = 'standard'`, `focus: str\|list[str]\|None = None` | `str` | AI-optimized string; `'minimal'`/`'standard'`/`'full'`; `focus` triggers `_focused_context()`. See `ten_q.py:82` |
| `__str__` | — | `str` | `"TenQ('CompanyName')"`. See `ten_q.py:79` |
| `__rich__` | — | `rich.Panel` | Rich panel with periods, structure tree, and financials. See `ten_q.py:510` |

---

## __getitem__ Lookup Chain

Applied in order; returns on first match.

| Priority | Input format | Key tried | Example |
|----------|-------------|-----------|---------|
| 1 | Direct key | `item_or_part` as-is | `'part_i_item_1'` |
| 2 | `'Part I, Item X'` / `'Part II, Item X'` | `part_i_item_{n}` or `part_ii_item_{n}` | `'Part II, Item 1'` → `part_ii_item_1` |
| 3 | `'Item X'` (unqualified) | `part_i_item_{n}` first, then `part_ii_item_{n}`, then TOC keys | `'Item 1'` → Part I (backward compat) |
| 4 | Short number `'1'`/`'1a'` | `part_i_item_{n}` first, then `part_ii_item_{n}`, then TOC keys | `'1'` → Part I Item 1 |
| fallback | All formats | `chunked_document[item_or_part]` (planned for removal in v6.0, no DeprecationWarning emitted by TenQ override) | logs warning |

**CRITICAL**: `tenq['Item 1']` returns Part I Item 1 (Financial Statements) for backward compat. Use `tenq['Part II, Item 1']` or `tenq.get_item_with_part('Part II', 'Item 1')` for Legal Proceedings.

---

## get_item_with_part Input Normalization

`part` parameter accepts all of: `'Part I'`, `'PART I'`, `'part_i'`, `'i'`, `'1'` (maps to Part I); `'Part II'`, `'PART II'`, `'part_ii'`, `'ii'`, `'2'` (maps to Part II).

`item` parameter accepts: `'Item 1'`, `'item 1'`, `'1'`, `'1a'` — prefix `item` is stripped, number extracted.

---

## Item Structure (Parts I-II)

| Part | Items | Key topics |
|------|-------|------------|
| Part I (Financial Information) | 1, 2, 3, 4 | Financial Statements, MD&A, Market Risk, Controls and Procedures |
| Part II (Other Information) | 1, 1A, 2, 3, 4, 5, 6 | Legal Proceedings, Risk Factors, Unregistered Equity Sales, Defaults on Senior Securities, Mine Safety, Other Information, Exhibits |

**Collision**: Both Part I and Part II have Item 1 (Financial Statements vs. Legal Proceedings) and Item 3 (Market Risk vs. Defaults on Senior Securities). Always use part-qualified access.

---

## Nested Objects

### FilingStructure (`edgar/company_reports/_structures.py:7`)

Class-level (`TenQ.structure`); not per-instance.

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get_part(part)` | `part: str` | `dict\|None` | Items dict for part (case-insensitive uppercase match) |
| `get_item(item, part=None)` | `item: str`, `part: Optional[str]` | `dict\|None` | Item metadata dict with `Title` and `Description` keys |
| `is_valid_item(item, part=None)` | `item: str`, `part: Optional[str]` | `bool` | True if item exists in structure |

Item metadata dict keys: `Title` (str), `Description` (str).

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form` not in `['10-Q', '10-Q/A']` | `AssertionError` raised in `__init__` |
| No filing HTML | `document` returns `None`; `sections` returns `{}` |
| `financials` is `None` (no XBRL) | `income_statement`, `balance_sheet`, `cash_flow_statement` return `None`; `auditor` returns `None` |
| `__getitem__` with unqualified `'Item 1'` | Returns Part I (Financial Statements), NOT Part II (Legal Proceedings) |
| `chunked_document` fallback | Logs `WARNING` with accession number and available section keys |
| `get_item_with_part` with unknown `part` string | `part_prefix` is `None`; falls through to `chunked_document` fallback, then `id_parse_document` fallback if `chunked_document` yields nothing |
| `__getitem__` finds no match | Returns `None` |

---

## TOC Analyzer Behavior for 10-Q

| Behavior | Detail |
|----------|--------|
| Part I seeding | All TOC parsers initialize `current_part = schema.seed_part = "Part I"`. Items appearing before any explicit Part header row are correctly attributed to Part I, not left as bare `item_N` keys that resolve to Part II |
| Unmatched text policy | `TEN_Q_SCHEMA.skip_unmatched_text=True` — TOC text that doesn't match a recognized pattern returns `""` and is dropped, preventing bogus `part_i_<descriptive-text>` section keys |
| Text keyword vocabulary | Only `Risk Factors→Item 1A` (safe 10-K/10-Q overlap). All other 10-K keyword mappings (Business→Item 1, MD&A→Item 7, etc.) are absent — they map to wrong items on a 10-Q |
| Bare-item cap | `max_bare_item=6` for 10-Q; page numbers 7+ in a TOC cell are not misidentified as item numbers. This fixed the PPG phantom `part_i_item_8` bug (accession `0000079879-26-000170`) |
| Part repeat disambiguation | 10-Q items repeat across parts (Part I Item 1 = Financial Statements; Part II Item 1 = Legal Proceedings). Part must be detected, never inferred from item number (`TEN_Q_SCHEMA.item_part_ranges` is empty) |
| Body-header fallback | Does NOT trigger for 10-Q — `_expected_item_floor()` returns 0 for non-10-K forms |

## Access Patterns

- Get TenQ: `tenq = filing.obj()` (or `TenQ(filing)` directly)
- Financial Statements (Part I, Item 1): `tenq['Part I, Item 1']` or `tenq['Item 1']`
- Legal Proceedings (Part II, Item 1): `tenq['Part II, Item 1']` or `tenq.get_item_with_part('Part II', 'Item 1')`
- MD&A: `tenq['Part I, Item 2']` or `tenq['Item 2']`
- All items with part qualification: `tenq.items` → `['Part I, Item 1', 'Part I, Item 2', ...]`
- Financial statements: `tenq.financials.income_statement()`
- Structure tree: `tenq.get_structure()` (Rich display)
- AI context: `tenq.to_context('standard', focus='revenue')`
