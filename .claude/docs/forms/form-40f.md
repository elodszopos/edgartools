# Form 40-F — Canadian MJDS Annual Report

**SEC form codes**: 40-F, 40-F/A
**Python class**: `FortyF` (extends `CompanyReport`)
**Access**: `filing.obj()` → `FortyF`
**Base fields**: See `reports-financials.md` (CompanyReport section) and `core-filing-access.md` (Filing section)
**Source**: `edgar/company_reports/forty_f.py`

---

## Complete Field Reference

### From Filing (inherited via `self._filing`)

See `core-filing-access.md` → Filing. Proxied via base class properties.

### From CompanyReport (inherited)

See `reports-financials.md` → CompanyReport. Key inherited fields:

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing_date` | `str` | no | `self._filing.filing_date` |
| `form` | `str` | no | `'40-F'` or `'40-F/A'` |
| `company` | `str` | no | `self._filing.company` |
| `period_of_report` | `Optional[str]` | no | `self._filing.header.period_of_report` |
| `financials` | `Optional[Financials]` | cached | iXBRL from 40-F wrapper document (not the AIF exhibit) |
| `income_statement` | `Optional[Statement]` | cached | Delegates to `self.financials.income_statement()` |
| `balance_sheet` | `Optional[Statement]` | cached | Delegates to `self.financials.balance_sheet()` |
| `cash_flow_statement` | `Optional[Statement]` | cached | Delegates to `self.financials.cashflow_statement()` |
| `auditor` | `Optional[AuditorInfo]` | cached | From XBRL DEI facts |
| `notes` | `Notes` | cached | Notes hierarchy from XBRL + FilingSummary |
| `reports` | `Optional[Reports]` | cached | XBRL report pages from FilingSummary.xml |
| `chunked_document` | `ChunkedDocument` | cached | Deprecated v5; removed v6 |

### FortyF-Specific Fields

#### AIF Discovery Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `_aif_result` | `Tuple[Optional[Attachment], str]` | cached | `(attachment, discovery_reason_string)` from `_find_aif_attachment()` |
| `aif_attachment` | `Optional[Attachment]` | cached | Best AIF exhibit; `None` if not found |
| `aif_html` | `Optional[str]` | cached | Raw HTML of AIF exhibit; triggers network download |
| `aif_text` | `Optional[str]` | cached | Plain text of AIF via BeautifulSoup or tag-stripping regex; triggers network |
| `aif_document` | `Optional[Document]` | cached | Parsed `Document` from AIF HTML via `HTMLParser(ParserConfig(form='40-F'))` |

#### MD&A Discovery Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `_mda_result` | `Tuple[Optional[Attachment], str]` | cached | `(attachment, discovery_reason_string)` |
| `mda_attachment` | `Optional[Attachment]` | cached | MD&A exhibit; `None` if not found |
| `mda_html` | `Optional[str]` | cached | Raw HTML of MD&A exhibit; triggers network |
| `mda_text` | `Optional[str]` | cached | Plain text of MD&A via BeautifulSoup or tag-stripping regex |

#### Document / Section Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `document` | `Optional[Document]` | cached | **Overrides base class** — returns `aif_document` if found, else parses `self._filing.html()` |
| `items` | `List[str]` | cached | Detected NI 51-102 section names in Title Case — NOT US Item numbers |
| `_section_positions` | `List[Tuple[int, str]]` | cached | `(char_position, Title_Case_name)` pairs from `_find_section_positions(aif_text)` |
| `business` | `Optional[str]` | cached | Extracted "Description of the Business" text from AIF via regex pipeline |

#### Named Section Properties (NI 51-102)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `risk_factors` | `Optional[str]` | no | `self['Risk Factors']` |
| `corporate_structure` | `Optional[str]` | no | `self['Corporate Structure']` |
| `dividends` | `Optional[str]` | no | `self['Dividends']` |
| `capital_structure` | `Optional[str]` | no | `self['Description Of Capital Structure']` |
| `directors_and_officers` | `Optional[str]` | no | `self['Directors And Officers']` |
| `legal_proceedings` | `Optional[str]` | no | `self['Legal Proceedings']` |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `__getitem__(key)` | `key: str` | `Optional[str]` | Section text lookup — see lookup order below |
| `view(item_or_part)` | `item_or_part: str` | `None` | Prints section text |
| `grep(pattern, *, regex, document)` | `pattern: str, regex: bool=False, document: Optional[str]=None` | `GrepResult` | Delegates to `self._filing.grep()` |
| `get_structure()` | none | `Tree` | Rich tree of expected vs detected NI 51-102 sections |
| `to_context(detail)` | `detail: str='standard'` | `str` | AI-optimized string; `'minimal'`/`'standard'`/`'full'` |

---

## AIF Discovery — Priority Chain

`_find_aif_attachment(filing)` uses `filing.homepage.attachments` (carries file sizes).

| Priority | Trigger | Source |
|----------|---------|--------|
| 1 | `document_type` in `('EX-1', 'EX-1.1', 'EX-1.2')` | Standard MJDS AIF exhibit |
| 2 | `description` contains `'ANNUAL INFORMATION'` or `'AIF'` | Description match |
| 3 | `document_type.startswith('EX-99')` AND `'aif'` in filename | Filename keyword — `'aif'` preferred over `'annual'` |
| 4 | Content-sniff: EX-99.x > 100 KB, first 80 KB contains NI 51-102 signals | `_has_aif_content()` — all EX-99.x checked |
| 5 | Main 40-F document (inline AIF, e.g. CNQ) | Embedded AIF |
| fallback | First major EX-99.x > 100 KB | Last resort |

NI 51-102 content signals (any one triggers match): `CORPORATE STRUCTURE`, `DESCRIPTION OF THE BUSINESS`, `GENERAL DEVELOPMENT OF THE BUSINESS`, `RISK FACTORS`.

Skipped types: `GRAPHIC`, `EX-101.*`, `XML`, `EX-23.*`, `EX-31.*`, `EX-32.*`, `EX-97*`, `''`. Only `.htm`/`.html`/`.xhtml` files considered.

---

## MD&A Discovery — Priority Chain

`_find_mda_attachment(filing, aif_attachment)` excludes already-identified AIF.

| Priority | Trigger |
|----------|---------|
| 1 | `description` contains `'MD&A'`, `'MANAGEMENT DISCUSSION'`, or `"MANAGEMENT'S DISCUSSION"` |
| 2 | `document_type.startswith('EX-99')` AND `'mda'` or `'managementdiscussion'` in filename |
| 3 | Content-sniff: remaining EX-99.x > 100 KB, first 80 KB contains 2+ MD&A signals |

MD&A content signals (2+ required to reduce false positives): `MANAGEMENT'S DISCUSSION AND ANALYSIS`, `MANAGEMENT DISCUSSION AND ANALYSIS`, `RESULTS OF OPERATIONS`, `LIQUIDITY AND CAPITAL RESOURCES`.

---

## `__getitem__` Lookup Order

Operates on `aif_text` + `_section_positions` (not on HTML sections dict).

| Priority | Mechanism | Example |
|----------|-----------|---------|
| 1 | Exact case-insensitive match | `'risk factors'` == `'Risk Factors'` |
| 2 | Keyword containment | `'business'` matches `'Description Of The Business'` |

Returns `None` if no section matches or if `aif_text` is unavailable. Raises `TypeError` if `key` is not a `str`.

**Critical**: `forty_f['Item 5']` returns `None` — US Item numbers do not work. Use `forty_f['Operating and Financial Review']` or named properties.

---

## Section Detection Pipeline

`_find_section_positions(full_text)` runs NI 51-102 pattern matching:

- Skips the first `min(max(5000, 3% of text), 10000)` chars to avoid TOC false positives
- Detects TOC entries (inline page numbers or 2+ standalone bare page numbers within 300 chars) and cross-references (`"see X"`, mid-sentence lowercase) — both skipped
- Deduplicates sections starting within 200 chars of each other (keeps first)
- Returns `List[Tuple[int, str]]` sorted by position

NI 51-102 section patterns detected (partial list): `CORPORATE STRUCTURE`, `GENERAL DEVELOPMENT OF THE BUSINESS`, `DESCRIPTION OF THE BUSINESS`, `DESCRIPTION OF CAPITAL STRUCTURE`, `MARKET FOR SECURITIES`, `DIVIDENDS`, `DIRECTORS AND OFFICERS`, `RISK FACTORS`, `LEGAL PROCEEDINGS`, `MATERIAL PROPERTIES`, `BUSINESS OVERVIEW`.

---

## `get_structure()` Output

Rich `Tree` showing NI 51-102 expected sections with match status:
- Green bold = detected in AIF
- Dim = expected but not detected
- Extra detected sections not in expected list shown with `*` suffix

Expected sections: Corporate Structure, General Development Of The Business, Description Of The Business, Risk Factors, Dividends, Description Of Capital Structure, Market For Securities, Directors And Officers, Legal Proceedings.

---

## `to_context` Output

| `detail` value | Contents |
|----------------|---------|
| `'minimal'` | Company/form/period/filed, AIF/MD&A found status |
| `'standard'` | Above + detected section names (count), available properties list, section lookup examples |
| `'full'` | Above + 150-char preview of each detected section |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form` not in `('40-F', '40-F/A')` | `AssertionError` in `__init__` |
| AIF not found | `aif_attachment` → `None`; `aif_html`/`aif_text`/`aif_document` → `None`; all section lookups return `None` |
| `__getitem__` with non-string key | `TypeError` raised |
| No XBRL in 40-F wrapper | `financials` → `None`; statement properties → `None`; `auditor` → `None` |
| bs4 unavailable for text extraction | Falls back to `re.sub(r'<[^>]+>', ' ', html)` tag stripping |
| `mda_attachment` → `None` | `mda_html`/`mda_text` → `None` |

---

## Access Patterns

- Get object: `filing.obj()` where `filing.form in ['40-F', '40-F/A']`
- Business description: `forty_f.business`
- Section lookup: `forty_f['Risk Factors']` or `forty_f.risk_factors`
- Fuzzy lookup: `forty_f['business']` → matches `'Description Of The Business'`
- All sections: `forty_f.items` — returns Title Case NI 51-102 names
- Raw AIF for LLM: `forty_f.aif_text`
- Raw MD&A for LLM: `forty_f.mda_text`
- XBRL financials: `forty_f.financials` (from 40-F wrapper, not AIF)
- Discovery reason: `forty_f._aif_result[1]` — human-readable string
- Structure display: `forty_f.get_structure()`

**Key gotcha**: `financials` comes from the 40-F iXBRL wrapper document, not the AIF exhibit. AIF exhibit is a separate HTML document. The `document` property returns the AIF document, not the 40-F wrapper — this overrides the base class behavior.
