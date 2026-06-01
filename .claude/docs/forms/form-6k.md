# Form 6-K — Foreign Private Issuer Current Report

**SEC form codes**: 6-K, 6-K/A
**Python class**: `SixK` (standalone — does NOT extend `CompanyReport` or `CurrentReport`)
**Access**: `filing.obj()` → `SixK`
**Base fields**: None — `SixK` re-implements all fields directly
**Source**: `edgar/company_reports/sixk.py`

---

## Complete Field Reference

### Inheritance Chain

`SixK` holds `self._filing` directly (same pattern as `CompanyReport`) but does NOT inherit from it. No `CompanyReport` base class methods are available unless explicitly reimplemented.

| Available from base | Status |
|--------------------|--------|
| `auditor` | NOT available — no base class |
| `notes` | NOT available |
| `reports` | NOT available |
| `chunked_document` | NOT available |
| `grep()` from base | NOT available — use `self._filing.grep()` directly |

### SixK Fields

#### Identity Properties (immediate — no network)

| Field | Type | Lazy | Source | Description |
|-------|------|------|--------|-------------|
| `filing_date` | `str` | no | `self._filing.filing_date` | Filing submission date |
| `form` | `str` | no | `self._filing.form` | `'6-K'` or `'6-K/A'` |
| `company` | `str` | no | `self._filing.company` | Registrant name |

#### Cover Page Properties (cached parse — network on first access)

Parsed by `_get_cover_metadata()` which calls `self._filing.html()` → `lxml.html.fromstring(html).text_content()` → `_parse_cover_page(text)`. Result cached in `self._cover_metadata`.

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `commission_file_number` | `Optional[str]` | cached | SEC Commission File Number, e.g. `'001-14948'`; regex on cover text |
| `report_month` | `Optional[str]` | cached | From `'For the month of [Month] [Year]'`; e.g. `'March 2026'` |
| `annual_report_form` | `Optional[str]` | cached | `'20-F'` or `'40-F'` — which form the issuer uses for annual reports; from checkbox markup |
| `content_description` | `Optional[str]` | cached | Text between `'Material Contained in this Report'`/`'Exhibit Description'` and `'SIGNATURES'` |
| `date_of_report` | `str` | no | `self._filing.header.period_of_report` → formatted as `'%B %d, %Y'`; returns `''` if missing |

#### Exhibit Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `exhibits` | `List[Attachment]` | cached | Non-graphic attachments; excludes `document_type == 'GRAPHIC'` and the cover page itself (`document_type == self._filing.form`) |
| `has_exhibits` | `bool` | no | `len(self.exhibits) > 0` |
| `press_releases` | `Optional[PressReleases]` | network | EX-99.x matching press-release query; returns `None` (not empty) if none found |
| `has_press_release` | `bool` | no | `self.press_releases is not None` |

`press_releases` query: `document.endswith('.htm') AND (re.match('.*RELEASE', description) OR document_type in ['EX-99.1', 'EX-99', 'EX-99.01'])`.

#### Financial Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `financials` | `Optional[Financials]` | cached | `Financials.extract(self._filing)`; rare — only when 6-K includes IFRS XBRL data |

No `income_statement`/`balance_sheet`/`cash_flow_statement` properties — access via `self.financials.income_statement()` etc. when `financials` is not None.

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `text()` | none | `str` | Full text of exhibits via `rich_to_text(self._content_renderables())` |
| `to_context(detail)` | `detail: str='standard'` | `str` | AI-optimized string |
| `_get_cover_metadata()` | none | `dict` | Internal; parses and caches cover page via lxml |
| `_get_exhibit_content(exhibit)` | `exhibit: Attachment` | `Optional[str]` | Rendered text of one exhibit |
| `_content_renderables()` | none | `Group` | Rich renderables for all exhibits |

---

## Cover Page Parsing

`_parse_cover_page(text: str) -> dict` — pure function on extracted text.

| Field extracted | Pattern |
|----------------|---------|
| `commission_file_number` | `Commission File Number[:\s]+([\d\-]+)` |
| `report_month` | `For the month of ([A-Za-z]+(?:\s+\d{4})?)` |
| `annual_report_form` | `Form\s*20-?F\s+\[?\s*X\s*\]?` → `'20-F'`; `Form\s*40-?F...` → `'40-F'` |
| `content_description` | Text between `Material Contained...` or `Exhibit Description` and `SIGNATURES`; whitespace-collapsed |

All fields default to `None` on parse failure.

---

## `exhibits` Filter Logic

Iterates `self._filing.attachments`. An attachment is excluded if:
- `att.document_type` is falsy
- `att.document_type == 'GRAPHIC'`
- `att.document_type == self._filing.form` (the 6-K cover page itself)

Result: EX-99.x, EX-10.x, other typed exhibits — everything except the cover and graphics.

---

## `to_context` Output

| `detail` value | Contents |
|----------------|---------|
| `'minimal'` | Company identity, filed date, date_of_report, report_month, annual_report_form, content_description |
| `'standard'` | Above + form/CIK, commission_file_number, flags (`has_press_release`/`has_exhibits`), first 10 exhibits (type + description), available actions |
| `'full'` | Above + all exhibit details (type/description/filename), cover page raw text |

---

## Nested Object: `Attachment` (from `exhibits`)

Each item in `self.exhibits` is an `Attachment`. See `sgml-attachments.md` for full schema. Key fields for 6-K use:

| Field | Type | Description |
|-------|------|-------------|
| `sequence_number` | `str` | Exhibit sequence in SGML bundle |
| `document_type` | `str` | e.g. `'EX-99.1'`, `'EX-10.1'` |
| `description` | `str` | Human-readable description |
| `document` | `str` | Filename |
| `url` | `str` | Full EDGAR URL |
| `content` | `bytes\|str` | Downloaded content (lazy) |
| `is_binary()` | method | True for PDF/image |
| `empty` | `bool` | True if content not yet loaded |

## Nested Object: `PressReleases`

`press_releases` → `PressReleases(attachments)`. See `reports-financials.md` → PressReleases. Each item is `PressRelease(attachment)` with `.html()`, `.text()`, `.to_markdown()`, `.view()`, `.open()`.

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form` not in `['6-K', '6-K/A']` | `AssertionError` in `__init__` |
| `self._filing.html()` returns None or lxml error | `_get_cover_metadata()` → `{}`; all cover properties → `None`; `date_of_report` → `''` |
| No press-release attachments match query | `press_releases` → `None` (not empty list) |
| No XBRL data | `financials` → `None` |
| Exhibit is binary | `text()` skips that exhibit (`.is_binary()` check) |
| Exhibit content unavailable | `_get_exhibit_content()` → `None`; exhibit skipped in `text()` |
| `self._filing.header.period_of_report` is None | `date_of_report` → `''` |

---

## Access Patterns

- Get object: `filing.obj()` where `filing.form in ['6-K', '6-K/A']`
- Cover metadata: `six_k.content_description`, `six_k.report_month`, `six_k.annual_report_form`
- Exhibit iteration: `for att in six_k.exhibits: ...`
- Press releases: `six_k.press_releases[0].text()` (if `has_press_release`)
- Full text: `six_k.text()` — all exhibits concatenated
- XBRL (rare): `six_k.financials.income_statement()` if `six_k.financials`
- AI context: `six_k.to_context('full')`
- Underlying filing: `six_k._filing` — full `Filing` object with all methods

**Key gotcha**: No `auditor`, `notes`, `reports`, `grep()`, or inherited `CompanyReport` methods. No numbered item structure — 6-K content is purely exhibit-based. `financials` is rare; most 6-K filings do not include XBRL. `annual_report_form` tells you which annual form the issuer files (`'20-F'` or `'40-F'`), not the current 6-K form code. `press_releases` returns `None` on miss (not an empty `PressReleases`), so always check `has_press_release` first.
