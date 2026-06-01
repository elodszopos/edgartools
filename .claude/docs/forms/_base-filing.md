# Filing — Base Class Field Reference

**Python class**: `Filing`
**Source**: `edgar/_filings.py:1411`
**Access**: constructed by `Filings.__getitem__`, `get_by_accession_number`, `Filing.from_sgml`, `Filing.from_dict`
**All form-specific docs**: inherit these fields; per-form docs say "See `_base-filing.md`"

---

## Constructor

`Filing(cik, company, form, filing_date, accession_no, related_entities=None)` — `_filings.py:1416`

All five required parameters are stored as instance attributes. All content is lazy — no network calls at construction.

---

## Instance Attributes (set in `__init__`)

| Attribute | Type | Description |
|-----------|------|-------------|
| `cik` | `int` | Central Index Key (CIK) of the primary filer |
| `company` | `str` | Name of the primary filer |
| `form` | `str` | SEC form type string, e.g. `'10-K'`, `'8-K/A'` |
| `filing_date` | `str` | Date filed as `'YYYY-MM-DD'` string |
| `accession_no` | `str` | Dashed accession number, e.g. `'0001564590-18-004771'` |
| `_related_entities` | `List[Dict]` | Co-filers from index enrichment; empty list if single filer |
| `_filing_homepage` | `FilingHomepage\|None` | Instance cache; None until `homepage` first accessed |
| `_sgml` | `FilingSGML\|None` | Instance cache; None until `sgml()` first called |

---

## Properties (immediate — no network)

| Property | Type | Description | Source |
|----------|------|-------------|--------|
| `accession_number` | `str` | Alias for `accession_no` | `_filings.py:1439` |
| `is_multi_entity` | `bool` | True if `_related_entities` non-empty OR header has multiple filers | `_filings.py:1510` |
| `all_ciks` | `List[int]` | All CIKs including co-filers; sorted, deduplicated | `_filings.py:1443` |
| `all_entities` | `List[Dict[str, Any]]` | All `{cik, company}` dicts including co-filers | `_filings.py:1475` |
| `obj_type` | `Optional[str]` | Class name that `.obj()` returns, or None if unsupported | `_filings.py:2009` |
| `exhibits` | `list` | Shortcut to `attachments.exhibits` | `_filings.py:1593` |
| `docs` | `Docs` | Interactive API documentation object | `_filings.py:1435` |

---

## URL Properties (immediate — no network)

| Property | Type | Value pattern | Source |
|----------|------|---------------|--------|
| `base_dir` | `str` | `{SEC_ARCHIVE_URL}/data/{cik}/{accession_no_nodash}` | `_filings.py:2149` |
| `homepage_url` | `str` | `{SEC_ARCHIVE_URL}/data/{cik}/{accession_no}-index.html` | `_filings.py:2137` |
| `text_url` | `str` | `{base_dir}/{accession_no}.txt` | `_filings.py:2141` |
| `filing_url` | `str` | `{base_dir}/{document.document}` — primary doc URL | `_filings.py:2133` |
| `index_header_url` | `str` | `{base_dir}/index-headers.html` | `_filings.py:2145` |
| `url` | `str` | Alias for `homepage_url` | `_filings.py:2153` |

---

## Properties (lazy — trigger SGML load on first access)

These all call `self.sgml()` internally. SGML is loaded once and cached.

| Property | Type | Lazy | Description | Source |
|----------|------|------|-------------|--------|
| `attachments` | `Attachments` | network | All documents in the SGML bundle | `_filings.py:1587` |
| `document` | `Attachment` | network | Primary display document (HTML/XHTML); paper-filing fallback to scanned PDF | `_filings.py:1532` |
| `primary_documents` | `list[Attachment]` | network | Primary HTML + XML documents | `_filings.py:1550` |
| `period_of_report` | `Optional[str]` | network | Reporting period; from SGML header, fallback to homepage | `_filings.py:1560` |
| `homepage` | `FilingHomepage` | network | Lazy-loaded index page; instance-cached after first access | `_filings.py:2157` |
| `home` | `FilingHomepage` | network | Alias for `homepage` | `_filings.py:2167` |

---

## Cached Properties (computed once, then stored)

| Property | Type | Description | Source |
|----------|------|-------------|--------|
| `header` | `FilingHeader` | Parsed SEC-HEADER metadata from SGML | `_filings.py:1994` |
| `reports` | `Optional[Reports]` | XBRL viewer reports from FilingSummary.xml | `_filings.py:1922` |
| `statements` | `Optional[Statements]` | Financial statement reports; from `reports.statements` | `_filings.py:1932` |
| `viewer` | `FilingViewer\|None` | SEC Interactive Data Viewer; requires MetaLinks.json | `_filings.py:1940` |
| `agent` | `Optional[str]` | Filing agent name (e.g. `'Workiva'`, `'Donnelley'`) | `_filings.py:1576` |
| `filing_directory` | `FilingDirectory` | Directory listing from `base_dir` | `_filings.py:1823` |
| `index_headers` | `IndexHeaders` | Index headers HTML; network call | `_filings.py:1954` |

---

## Content Methods (lru_cache per instance)

| Method | Returns | Lazy | Description | Source |
|--------|---------|------|-------------|--------|
| `sgml()` | `FilingSGML` | network | Full SGML bundle; priority chain: local → datamule → network → homepage fallback | `_filings.py:1872` |
| `html()` | `Optional[str]` | network | Primary document HTML; XML ownership forms rendered to HTML; `None` for PDF/binary | `_filings.py:1598` |
| `xml()` | `Optional[str]` | network | Primary document XML; fallback to homepage XML attachment | `_filings.py:1639` |
| `text()` | `str` | network | HTML→text via `HTMLParser`; fallback to TEXT-EXTRACT attachment | `_filings.py:1655` |
| `parse()` | `Optional[Document]` | network | Parse HTML into structured `Document` tree | `_filings.py:1735` |
| `sections()` | `List[str]` | network | HTML sections list; raises `ValueError` if no HTML | `_filings.py:2035` |
| `full_text_submission()` | `str` | network | Download full `.txt` SGML submission file | `_filings.py:1688` |

---

## Content Methods (not cached)

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `markdown(include_page_breaks, start_page_number)` | `bool=False, int=0` | `str` | HTML→Markdown; falls back to `text_to_markdown` | `_filings.py:1699` |
| `xbrl()` | — | `Optional[XBRL]` | Parse XBRL; returns `None` if no XBRL; raises network errors | `_filings.py:1765` |
| `view()` | — | `None` | Render primary document as markdown in console | `_filings.py:1721` |

---

## Dispatch Methods

| Method | Returns | Description | Source |
|--------|---------|-------------|--------|
| `obj()` | `Optional[object]` | Dispatch to typed form class (TenK, TenQ, EightK, etc.) via module-level `obj()` | `_filings.py:2004` |
| `data_object()` | `Optional[object]` | Alias for `obj()` | `_filings.py:1999` |

---

## Navigation & Search Methods

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `search(query, regex)` | `str, bool=False` | search result | BM25 or regex search across HTML sections | `_filings.py:2053` |
| `grep(pattern, regex, document)` | `str, bool=False, Optional[str]=None` | `GrepResult` | Case-insensitive search across all attachments; `document='primary'` or doc type | `_filings.py:2061` |
| `get_entity()` | — | `Company` | Company owning this filing (lru_cache) | `_filings.py:2172` |
| `related_filings()` | — | `CompanyFilings` | All filings sharing same file_number (lru_cache) | `_filings.py:2191` |
| `as_company_filing()` | — | `CompanyFiling\|None` | Richer company-filing object via entity lookup (lru_cache) | `_filings.py:2179` |
| `correspondence()` | — | `Optional[CorrespondenceThread]` | SEC review correspondence thread; works on any form type | `_filings.py:2223` |

---

## Persistence Methods

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `save(directory_or_file)` | `PathLike` | `None` | Pickle to file; preloads SGML first for self-contained file | `_filings.py:1796` |
| `to_dict()` | — | `Dict[str, Union[str, int]]` | Serialize to 5-key dict | `_filings.py:1965` |
| `summary()` | — | `pd.DataFrame` | Single-row DataFrame with accession/date/company/CIK | `_filings.py:2271` |

---

## AI Integration Methods

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `to_context(detail)` | `str='standard'` | `str` | LLM-optimized markdown-KV context | `_filings.py:2278` |
| `serve(port)` | `int=8000` | `AttachmentServer` | Serve attachments on local HTTP server | `_filings.py:1790` |
| `open()` | — | `None` | Open primary document in browser | `_filings.py:2028` |
| `open_homepage()` | — | `None` | Open filing homepage in browser | `_filings.py:2024` |

---

## Classmethods

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `Filing.from_sgml(source)` | `Union[str, Path]` | `Filing` | Construct from SGML file or string | `_filings.py:1832` |
| `Filing.from_sgml_text(text)` | `str` | `Filing` | Construct from full-text submission string | `_filings.py:1852` |
| `Filing.from_dict(data)` | `Dict` | `Filing` | Requires keys: `cik, company, form, filing_date, accession_number` | `_filings.py:1973` |
| `Filing.from_json(path)` | `str` | `Filing` | Load from JSON file | `_filings.py:1986` |
| `Filing.load(path)` | `PathLike` | `Filing` | Load from pickle file | `_filings.py:1815` |

---

## `to_dict()` Schema

| Key | Type |
|-----|------|
| `accession_number` | `str` |
| `cik` | `int` |
| `company` | `str` |
| `form` | `str` |
| `filing_date` | `str` |

---

## `to_context(detail)` Detail Levels

| Level | Content | ~Tokens |
|-------|---------|---------|
| `'minimal'` | form, company, CIK, filed date, accession | ~100 |
| `'standard'` | + period, multi-entity, available actions | ~250 |
| `'full'` | + XBRL check, primary document filename | ~500 |

---

## Nested Object: `Attachment` (`edgar/attachments.py:254`)

Single document within a filing.

### `Attachment` Constructor Arguments

| Field | Type | Description |
|-------|------|-------------|
| `sequence_number` | `str` | Position in filing (digits or empty); `'1'` = primary document |
| `description` | `str` | Human description from SGML |
| `document` | `str` | Filename (e.g. `'aapl-20240928.htm'`) |
| `ixbrl` | `bool` | True if document is inline XBRL |
| `path` | `str` | URL path (relative to SEC_BASE_URL) |
| `document_type` | `str` | SEC document type (e.g. `'10-K'`, `'EX-31.1'`, `'XML'`) |
| `size` | `Optional[int]` | File size in bytes; `None` if not parseable |
| `sgml_document` | `Optional[SGMLDocument]` | In-memory content from SGML bundle |
| `purpose` | `Optional[str]` | Override description for display |
| `filing_sgml` | `Optional[FilingSGML]` | Parent SGML bundle reference |

### `Attachment` Properties

| Property | Type | Description | Source |
|----------|------|-------------|--------|
| `content` | `str\|bytes` | Raw document content; from `sgml_document` if loaded, else network download | `attachments.py:284` |
| `url` | `str` | Full SEC URL via `sec_document_url(self.path)` | `attachments.py:330` |
| `extension` | `str` | File extension including dot (`.html`, `.xml`, `.pdf`, `.paper`, `.txt`) | `attachments.py:334` |
| `display_extension` | `str` | Extension as displayed in EDGAR HTML | `attachments.py:341` |
| `display_description` | `str` | `purpose` → `description` → standard exhibit lookup | `attachments.py:314` |
| `empty` | `bool` | True if `document` is None or blank | `attachments.py:368` |

### `Attachment` Methods

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `is_text()` | — | `bool` | Extension in text_extensions set | `attachments.py:352` |
| `is_xml()` | — | `bool` | Extension in `.xsd`, `.xml`, `.xbrl` | `attachments.py:357` |
| `is_html()` | — | `bool` | Extension in `.htm`, `.html` | `attachments.py:359` |
| `is_binary()` | — | `bool` | Extension in binary_extensions set | `attachments.py:363` |
| `is_report()` | — | `bool` | Filename matches `R\d+\.htm` pattern | `attachments.py:418` |
| `text()` | — | `Optional[str]` | HTML→plain text; XBRL reports via FilingSummary | `attachments.py:421` |
| `download(path)` | `Optional[Union[str, Path]]=None` | `Optional[Union[str, bytes]]` | Download to path or return content | `attachments.py:371` |
| `markdown(include_page_breaks, start_page_number)` | `bool=False, int=0` | `Optional[str]` | HTML→Markdown; `None` if not HTML | `attachments.py:438` |
| `view()` | — | `None` | Render in console (Rich or XML) | `attachments.py:398` |

---

## Nested Object: `Attachments` (`edgar/attachments.py:488`)

Ordered container of `Attachment` objects accessed via `filing.attachments`.

### `Attachments` Constructor Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `document_files` | `List[Attachment]` | Primary + exhibit documents |
| `data_files` | `Optional[List[Attachment]]` | XBRL taxonomy and schema data files |
| `primary_documents` | `List[Attachment]` | Documents at minimum sequence number |
| `sgml` | `Optional[FilingSGML]` | Parent SGML bundle |

### `Attachments` Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `documents` | `List[Attachment]` | All document-type attachments |
| `data_files` | `List[Attachment]\|None` | All data-type attachments (XBRL files) |
| `primary_documents` | `List[Attachment]` | Primary document(s) at lowest sequence number |

### `Attachments` Properties

| Property | Type | Description | Source |
|----------|------|-------------|--------|
| `primary_html_document` | `Optional[Attachment]` | First `.html`/`.htm` in primary_documents; falls back to first primary doc | `attachments.py:547` |
| `primary_xml_document` | `Optional[Attachment]` | First `.xml` in primary_documents | `attachments.py:563` |
| `text_document` | `Optional[Attachment]` | Last document with description `'Complete submission text file'` | `attachments.py:571` |
| `exhibits` | `Attachments` | Primary HTML doc + all `EX-*` documents | `attachments.py:578` |
| `graphics` | `Attachments` | All `GRAPHIC` type attachments | `attachments.py:591` |

### `Attachments` Methods

| Method | Parameters | Returns | Description | Source |
|--------|-----------|---------|-------------|--------|
| `__getitem__(item)` | `Union[int, str]` | `Attachment` | By sequence number (int or digit str) or filename | `attachments.py:506` |
| `get_by_sequence(sequence)` | `Union[str, int]` | `Attachment` | Exact sequence number match; raises `KeyError` on miss | `attachments.py:518` |
| `get_by_index(index)` | `int` | `Attachment` | 0-based list index | `attachments.py:528` |
| `get_report(filename)` | `str` | `Report` | Look up XBRL report by filename via FilingSummary | `attachments.py:535` |
| `query(query_str, include_data_files)` | `str, bool=True` | `Attachments` | Filter by `document`, `description`, or `document_type` attribute expressions | `attachments.py:595` |
| `download(path, archive)` | `Union[str, Path], bool=False` | `None` | Download all attachments to directory or zip | `attachments.py:640` |
| `serve(port)` | `int=8000` | `Tuple[Thread, TCPServer, str]` | Serve all attachments on local HTTP | `attachments.py:683` |
| `markdown(include_page_breaks, start_page_number)` | `bool=False, int=0` | `Dict[str, str]` | All HTML attachments as `{filename: markdown}` | `attachments.py:727` |
| `__len__()` | — | `int` | Total attachment count (documents + data_files) | `attachments.py:749` |
| `__iter__()` / `__next__()` | — | `Attachment` | Iterate all attachments | `attachments.py:752` |

---

## Nested Object: `FilingHeader` (`edgar/sgml/sgml_header.py:371`)

Accessed via `filing.header` (cached_property).

### `FilingHeader` Properties

| Property | Type | Source |
|----------|------|--------|
| `accession_number` | `str` | `sgml_header.py:397` |
| `cik` | `str` | `sgml_header.py` |
| `form` | `str` | `sgml_header.py` |
| `period_of_report` | `Optional[str]` | `sgml_header.py` |
| `filing_date` | `str` | `sgml_header.py` |
| `date_as_of_change` | `Optional[str]` | `sgml_header.py` |
| `document_count` | `Optional[int]` | `sgml_header.py` |
| `acceptance_datetime` | `Optional[str]` | `sgml_header.py` |
| `file_numbers` | `List[str]` | `sgml_header.py` |
| `filers` | `List[Filer]` | Each has `company_information` (name, CIK, SIC, addresses) |
| `reporting_owners` | `List[ReportingOwner]` | For Forms 3/4/5 |
| `issuer` | `Optional[Issuer]` | For Forms 3/4/5 |
| `subject_companies` | `List[SubjectCompany]` | For tender offers, mergers |

---

## `GrepResult` (returned by `filing.grep()`)

| Field | Type | Description |
|-------|------|-------------|
| `pattern` | `str` | The search pattern |
| `matches` | `List[GrepMatch]` | All matches found |

Each `GrepMatch` has: `location` (document name or `'primary'`), `context` (surrounding text snippet).

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `EDGAR_IDENTITY` not set | `sgml()` raises `IdentityNotSetException` (prompts interactively with 60s timeout in TTY) |
| Filing not on EDGAR | `sgml()` raises `SECFilingNotFoundError` |
| Network timeout | `sgml()` raises if permanent; HTML fallback for transient content errors |
| No HTML document | `html()` returns `None`; `text()` falls back to TEXT-EXTRACT attachment |
| No XBRL data | `xbrl()` returns `None` |
| No HTML for sections | `sections()` raises `ValueError` with diagnostic message |
| Paper/scanned filing | `document` property returns scanned PDF attachment if found |
| `Attachments[key]` miss | Raises `KeyError` |

---

## Access Patterns

- Get filing: `Company("AAPL").get_filings(form="10-K").latest(1)` or `find("0001564590-18-004771")`
- Get typed object: `filing.obj()` → `TenK`, `TenQ`, `EightK`, etc.
- Check form type: `filing.form in ['10-K', '10-K/A']`
- Search text: `filing.grep("going concern")` or `filing.grep("Level 3", document="primary")`
- Persist: `filing.save("/tmp/")` → `Filing.load("/tmp/0001564590-18-004771.pkl")`
- AI context: `filing.to_context('full')`
