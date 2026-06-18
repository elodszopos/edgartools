# Form 20-F — Foreign Private Issuer Annual Report

**SEC form codes**: 20-F, 20-F/A
**Python class**: `TwentyF` (extends `CompanyReport`)
**Access**: `filing.obj()` → `TwentyF`
**Base fields**: See `reports-financials.md` (CompanyReport section) and `core-filing-access.md` (Filing section)
**Source**: `edgar/company_reports/twenty_f.py`

---

## Complete Field Reference

### From Filing (inherited via `self._filing`)

See `core-filing-access.md` → Filing. Proxied via base class properties below.

### From CompanyReport (inherited)

See `reports-financials.md` → CompanyReport. Key inherited fields:

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing_date` | `str` | no | `self._filing.filing_date` |
| `form` | `str` | no | `self._filing.form` — `'20-F'` or `'20-F/A'` |
| `company` | `str` | no | `self._filing.company` |
| `period_of_report` | `Optional[str]` | no | `self._filing.header.period_of_report` |
| `financials` | `Optional[Financials]` | cached | `Financials.extract(self._filing)` — XBRL/iXBRL; IFRS or US GAAP |
| `income_statement` | `Optional[Statement]` | cached | Delegates to `self.financials.income_statement()` |
| `balance_sheet` | `Optional[Statement]` | cached | Delegates to `self.financials.balance_sheet()` |
| `cash_flow_statement` | `Optional[Statement]` | cached | Delegates to `self.financials.cashflow_statement()` |
| `auditor` | `Optional[AuditorInfo]` | cached | `extract_auditor_info(self.financials.xb)` — DEI XBRL facts |
| `notes` | `Notes` | cached | Notes hierarchy from XBRL + FilingSummary |
| `reports` | `Optional[Reports]` | cached | XBRL report pages from FilingSummary.xml |
| `doc` | `Document` | cached | Alias for `document` |
| `chunked_document` | `ChunkedDocument` | cached | Deprecated v5; removed v6 |

### TwentyF-Specific Fields

#### Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `document` | `Optional[Document]` | cached | HTMLParser with `ParserConfig(form='20-F')` on `self._filing.html()` |
| `sections` | `dict` | no | `document.sections` — keys normalized, e.g. `'item_5'`; empty dict if no document |
| `items` | `List[str]` | no | Detected item names; prefers `chunked_document.list_items()` for TOC format; falls back to section regex extraction |
| `key_information` | `Optional[str]` | no | `self['Item 3']` — Key Information |
| `risk_factors` | `Optional[str]` | no | `self['Item 3']` — same as `key_information` |
| `business` | `Optional[str]` | no | `self['Item 4']` — Information on the Company |
| `company_information` | `Optional[str]` | no | `self['Item 4']` — alias for `business` |
| `operating_review` | `Optional[str]` | no | `self['Item 5']` — Operating and Financial Review |
| `management_discussion` | `Optional[str]` | no | `self['Item 5']` — alias for `operating_review` |
| `directors_and_employees` | `Optional[str]` | no | `self['Item 6']` — Directors, Senior Management and Employees |
| `major_shareholders` | `Optional[str]` | no | `self['Item 7']` — Major Shareholders and Related Party Transactions |
| `financial_information` | `Optional[str]` | no | `self['Item 8']` — Financial Information |
| `controls_and_procedures` | `Optional[str]` | no | `self['Item 15']` — Controls and Procedures |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `__getitem__(item_name)` | `item_name: str` | `Optional[str]` | Section text lookup — see lookup order below |
| `view(item_or_part)` | `item_or_part: str` | `None` | Prints section text to stdout |
| `grep(pattern, *, regex, document)` | `pattern: str, regex: bool=False, document: Optional[str]=None` | `GrepResult` | Delegates to `self._filing.grep()` |
| `to_context(detail)` | `detail: str='standard'` | `str` | AI-optimized string; `'minimal'`/`'standard'`/`'full'` |
| `_focused_context(focus, detail)` | `focus: str|list, detail: str='standard'` | `str` | Cross-cutting context for specific topics |

---

## Filing Structure

Class-level `structure = FilingStructure({...})` — 5 Parts, Items 1–19.

| Part | Items | Key Sections |
|------|-------|-------------|
| Part I | 1, 2, 3, 4, 4A | Identity of Directors; Offer Statistics; Key Information; Information on the Company; Unresolved Staff Comments |
| Part II | 5, 6, 7, 8, 9 | Operating and Financial Review; Directors/Employees; Major Shareholders; Financial Information; The Offer and Listing |
| Part III | 10, 11, 12 | Additional Information; Market Risk; Securities Other Than Equity |
| Part IV | 13, 14, 15, 16 | Defaults; Material Modifications; Controls and Procedures; Various Disclosures |
| Part V | 17, 18, 19 | Financial Statements (US GAAP/IFRS); Financial Statements (home-country); Exhibits |

Item 17 vs Item 18: Item 17 = US GAAP or IFRS; Item 18 = home-country standards (only if different from Item 17).

---

## `__getitem__` Lookup Order

Accepts: section key, item number with/without "Item" prefix, Part lookups.

| Priority | Input Format | Example | Mechanism |
|----------|-------------|---------|-----------|
| 1 | Exact section key | `'item_5'` | `self.sections[item_name]` |
| 2 | Part-prefixed keys | auto | Tries `part_i_item_5` through `part_v_item_5` |
| 3 | Direct item key | auto | `item_{num}` |
| 4 | Friendly key | auto | `Item {NUM}` (uppercase) |
| 5 | chunked_document | fallback | `self.chunked_document[item_name]` — backward compat |

Returns `None` if not found. Raises nothing.

Input normalization: `'Item 16A'` → extracts `'16a'`; `'5'` → `'5'`.

---

## `to_context` Output

| `detail` value | Approximate tokens | Contents |
|----------------|-------------------|---------|
| `'minimal'` | ~100 | Company identity, period, filing date, revenue, net income |
| `'standard'` | ~300 | Above + form/CIK, financials (5 metrics), detected sections, available actions |
| `'full'` | ~500+ | Above + auditor name/location/PCAOB firm ID |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form` not in `['20-F', '20-F/A']` | `AssertionError` in `__init__` |
| `self._filing.html()` returns None | `document` → `None`; `sections` → `{}`; all item lookups return `None` |
| No XBRL data | `financials` → `None`; `income_statement`/`balance_sheet`/`cash_flow_statement` → `None`; `auditor` → `None` |
| `financials.xb` is None | `auditor` → `None` (DEI facts unavailable) |
| `chunked_document` accessed | `DeprecationWarning` emitted; removed in v6 |
| Item not in sections or chunked_document | `__getitem__` returns `None` |
| `notes` when no financials | Returns empty `Notes([], entity_name=str(self.company))` |

---

## Access Patterns

- Get object: `filing.obj()` where `filing.form in ['20-F', '20-F/A']`
- Section drill-down: `twenty_f['Item 5']` or `twenty_f.operating_review`
- Financials: `twenty_f.financials.income_statement()` → `Statement`
- Notes: `twenty_f.notes[5]` or `twenty_f.notes['Debt']`
- Auditor: `twenty_f.auditor.name`, `.location`, `.firm_id`, `.icfr_attestation`
- AI context: `twenty_f.to_context('full')`
- Topic focus: `twenty_f._focused_context('revenue')`

**Key gotcha**: `items` and `__getitem__` prefer `chunked_document` (TOC parser) over the new HTML parser for 20-F, which is the inverse of TenK/TenQ. Financial statements appear in Item 17 (US GAAP/IFRS) or Item 18 (home-country standards).
