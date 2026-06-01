## SGML Submission Parsing & Attachments

### Overview

This domain handles the full lifecycle of a raw SEC EDGAR filing submission bundle (the multi-megabyte `.txt` SGML file). It parses the flat SGML stream into a header + document tree (`FilingSGML`), materializes typed metadata objects (`FilingHeader` and its sub-objects), and exposes every embedded file as an `Attachment` inside an `Attachments` collection. For XBRL filings, it also parses the SEC-generated `FilingSummary.xml` into navigable `Reports` (R-files with menu categories), the rich `MetaLinks.json` into tag definitions and calculation trees, and provides two viewer-oriented layers: `ConceptExtractor` (concept-annotated rows from R*.htm files) and `FinancialTableExtractor` (DataFrame extraction from HTML tables).

---

### Public API surface

| Symbol | file:line | Purpose |
|---|---|---|
| `FilingSGML` | `edgar/sgml/sgml_common.py:226` | Top-level entry point — owns header + document map |
| `FilingHeader` | `edgar/sgml/sgml_header.py:371` | Parsed SEC-HEADER text with typed sub-objects |
| `FilingMetadata` | `edgar/sgml/sgml_header.py:77` | Dict-backed metadata (accession#, form, dates) |
| `CompanyInformation` | `edgar/sgml/sgml_header.py:123` | Frozen dataclass: name, CIK, SIC, IRS #, state |
| `FilingInformation` | `edgar/sgml/sgml_header.py:145` | Frozen dataclass: form, file#, SEC act, film# |
| `Filer` | `edgar/sgml/sgml_header.py:167` | Company + filing info + addresses + former names |
| `Owner` | `edgar/sgml/sgml_header.py:202` | Lazy name-reversal for SEC-DOCUMENT individual owners |
| `ReportingOwner` | `edgar/sgml/sgml_header.py:252` | Owner + company/filing info + addresses |
| `SubjectCompany` | `edgar/sgml/sgml_header.py:295` | Subject company in tender offer / going-private filings |
| `Issuer` | `edgar/sgml/sgml_header.py:337` | Issuer entity for Form 3/4/5 filings |
| `FormerCompany` | `edgar/sgml/sgml_header.py:161` | Frozen dataclass: name + date_of_change |
| `SGMLParser` | `edgar/sgml/sgml_parser.py:219` | Detects format and dispatches to sub-parser |
| `SGMLDocument` | `edgar/sgml/sgml_parser.py:78` | Single embedded document with lazy content |
| `SGMLFormatType` | `edgar/sgml/sgml_parser.py:50` | Enum: `SEC_DOCUMENT` / `SUBMISSION` |
| `FilingSummary` | `edgar/sgml/filing_summary.py:323` | Parses `FilingSummary.xml` from XBRL bundle |
| `Reports` | `edgar/sgml/filing_summary.py:22` | PyArrow-backed collection of Report objects |
| `Report` | `edgar/sgml/filing_summary.py:212` | Single R*.htm entry with content access + DataFrame |
| `File` | `edgar/sgml/filing_summary.py:315` | XBRL input/supplemental file descriptor |
| `Statements` | `edgar/sgml/filing_summary.py:598` | Pattern-matched financial statement navigation |
| `StatementType` | `edgar/sgml/filing_summary.py:493` | Enum: INCOME / BALANCE / CASH_FLOW / COMPREHENSIVE_INCOME / EQUITY |
| `MetaLinks` | `edgar/sgml/metalinks.py:120` | Parses `MetaLinks.json` — tags, calculation trees, FASB refs |
| `TagDefinition` | `edgar/sgml/metalinks.py:38` | XBRL concept with labels, crdr, calculations, auth refs |
| `CalculationEntry` | `edgar/sgml/metalinks.py:28` | Calculation relationship: parent, weight, order, root flag |
| `MetaLinksReport` | `edgar/sgml/metalinks.py:92` | Report metadata entry from MetaLinks (mirrors FilingSummary) |
| `AuthRef` | `edgar/sgml/metalinks.py:107` | FASB codification reference |
| `ConceptRow` | `edgar/sgml/concept_extractor.py:69` | Concept-annotated row from an R*.htm file |
| `ConceptReport` | `edgar/sgml/concept_extractor.py:124` | Full parsed R*.htm with period headers + rows |
| `extract_concepts_from_report` | `edgar/sgml/concept_extractor.py:481` | Parse R*.htm HTML into `ConceptReport` |
| `parse_numeric` | `edgar/sgml/concept_extractor.py:49` | Parse display strings like `(279)` → `-279.0` |
| `FinancialTableExtractor` | `edgar/sgml/table_to_dataframe.py:27` | Extract financial DataFrame from HTML table node |
| `extract_statement_dataframe` | `edgar/sgml/table_to_dataframe.py:297` | Convenience: parse report HTML → `pd.DataFrame` |
| `Attachment` | `edgar/attachments.py:254` | Single filing document with content + download |
| `Attachments` | `edgar/attachments.py:488` | Collection with indexing, query, download, serve |
| `FilingHomepage` | `edgar/attachments.py:917` | EDGAR index page with attachment scraping |
| `FilerInfo` | `edgar/attachments.py:238` | Pydantic model for filer block from homepage HTML |
| `AttachmentServer` | `edgar/attachments.py:866` | Local HTTP server to view attachments in browser |
| `get_document_type` | `edgar/attachments.py:188` | Normalize declared doc type vs. file extension |
| `sec_document_url` | `edgar/attachments.py:43` | Strip `ix?doc=/` and prepend `SEC_BASE_URL` |
| `iter_documents` | `edgar/sgml/sgml_common.py:123` | Stream `SGMLDocument` objects from URL/path |
| `list_documents` | `edgar/sgml/sgml_common.py:145` | Collect all `SGMLDocument` objects into a list |
| `parse_submission_text` | `edgar/sgml/sgml_common.py:170` | Parse raw SGML text → `(FilingHeader, dict[seq → [SGMLDocument]])` |

---

### Key classes

#### `SGMLParser` — edgar/sgml/sgml_parser.py:219
Detects SGML format and dispatches to sub-parsers.

- `detect_format(content) -> SGMLFormatType` — identifies `SUBMISSION` vs `SEC_DOCUMENT` format by string prefix, raises `SECIdentityError`/`SECFilingNotFoundError`/`SECHTMLResponseError` for error responses — sgml_parser.py:221
- `parse(content) -> dict` — validates 500MB size cap, then delegates; returns `{format, header, documents}` — sgml_parser.py:278

#### `SubmissionFormatParser` — edgar/sgml/sgml_parser.py:354
Parser for modern `<SUBMISSION>` SGML format.

- `parse(content) -> dict` — splits at first `<DOCUMENT>`, parses header line-by-line building a hierarchical dict, extracts documents using `_extract_all_documents()` — sgml_parser.py:430
- `_handle_header_line(line)` — classifies lines as section-start, section-end, or data-tag, maintaining a `current_path` stack — sgml_parser.py:382

#### `SecDocumentFormatParser` — edgar/sgml/sgml_parser.py:457
Parser for older `<SEC-DOCUMENT>` format.

- `parse(content) -> dict` — extracts `<SEC-HEADER>` or `<IMS-HEADER>` block, then calls `_extract_all_documents()` — sgml_parser.py:471

#### `SGMLDocument` — edgar/sgml/sgml_parser.py:78
Zero-copy lazy document. Stores a reference to the full SGML string + byte offsets rather than copying content.

- `from_content_ref(metadata, content_ref, start, end) -> SGMLDocument` — zero-copy factory (primary path) — sgml_parser.py:89
- `from_parsed_data(data) -> SGMLDocument` — legacy compatibility factory — sgml_parser.py:103
- `raw_content` (property) — materializes via `content_ref[start:end]` on access — sgml_parser.py:117
- `content` (property) — calls `get_content_between_tags(raw_content)`, handles UU-encoded binary (decodes via `uu.decode`) — sgml_parser.py:131
- `text() -> str` — extracts `<TEXT>…</TEXT>` via compiled regex — sgml_parser.py:145
- `xml() -> Optional[str]` — extracts `<XML>…</XML>` — sgml_parser.py:150
- `html() -> Optional[str]` — extracts `<HTML>…</HTML>` — sgml_parser.py:155
- `xbrl() -> Optional[str]` — extracts `<XBRL>…</XBRL>` — sgml_parser.py:160
- `get_content_type() -> str` — returns `'xml'`/`'html'`/`'xbrl'`/`'text'` — sgml_parser.py:165

#### `FilingSGML` — edgar/sgml/sgml_common.py:226
Main container and entry point. Owns `FilingHeader` + two document indexes.

- `__init__(header, documents)` — builds `_documents_by_sequence` (defaultdict) and `_documents_by_name` (dict by filename) — sgml_common.py:233
- `from_source(source) -> FilingSGML` — reads URL/path → `parse_submission_text()`, with empty-response retry via direct httpx fetch — sgml_common.py:406
- `from_text(full_text_submission) -> FilingSGML` — same pipeline from an in-memory string — sgml_common.py:445
- `from_filing(filing) -> FilingSGML` — wraps `from_source(filing.text_url)`, backfills missing accession/CIK/form from filing object — sgml_common.py:506
- `from_homepage(homepage) -> FilingSGML` — creates minimal instance with empty header, overrides `attachments` cached_property with homepage's attachments — sgml_common.py:482
- `attachments` (cached_property) → `Attachments` — iterates `_documents_by_sequence`, creates `Attachment` per doc, queries `filing_summary` for R*.htm purpose labels, classifies primary (seq==1) / data (XML/XSD/XBRL) / document files — sgml_common.py:317
- `filing_summary` (cached_property) → `Optional[FilingSummary]` — looks up `FilingSummary.xml` by name, parses it, wires back-references — sgml_common.py:360
- `html() -> Optional[str]` — returns content of primary HTML attachment — sgml_common.py:293
- `xml() -> Optional[str]` — returns content of primary XML attachment — sgml_common.py:301
- `get_content(filename) -> Optional[str]` — O(1) lookup by filename in `_documents_by_name` — sgml_common.py:309
- `get_document_by_sequence(sequence) -> Optional[SGMLDocument]` — O(1) — sgml_common.py:466
- `get_document_by_name(filename) -> Optional[SGMLDocument]` — O(1) — sgml_common.py:475
- `download(path, archive=False)` — saves all documents to dir or zip — sgml_common.py:369
- `path` (property) — constructs `/Archives/edgar/data/{cik}/{accession_no_nodash}` — sgml_common.py:284

#### `FilingHeader` — edgar/sgml/sgml_header.py:371
Typed header extracted from `<SEC-HEADER>` text.

- `__init__(text, filing_metadata, filers, reporting_owners, issuer, subject_companies)` — wraps metadata dict in `FilingMetadata` — sgml_header.py:379
- `parse_from_sgml_text(header_text, preprocess=False) -> FilingHeader` — tab-indented format parser for SEC-DOCUMENT format; `preprocess=True` handles 1990s full-tag format via `preprocess_old_headers()` — sgml_header.py:724
- `parse_submission_format_header(parsed_data) -> FilingHeader` — converts SUBMISSION format parsed dict to same structure — sgml_header.py:455
- `accession_number` (property) — from `filing_metadata["ACCESSION NUMBER"]` — sgml_header.py:397
- `cik` (property) — from metadata, falls back to first filer's CIK — sgml_header.py:401
- `form` (property) — `"CONFORMED SUBMISSION TYPE"` — sgml_header.py:413
- `period_of_report` (property) — `"CONFORMED PERIOD OF REPORT"` — sgml_header.py:417
- `filing_date` (property) — `"FILED AS OF DATE"` — sgml_header.py:421
- `acceptance_datetime` (property) → `datetime` — parsed from `"ACCEPTANCE-DATETIME"` — sgml_header.py:435
- `file_numbers` (property) — aggregated from filers + reporting_owners + subject_companies — sgml_header.py:441

#### `Owner` — edgar/sgml/sgml_header.py:202
Lazy name resolver for insider filings.

- `name` (property) — if `needs_reversal=True` (SEC-DOCUMENT format), looks up `Entity(cik).is_company`; if company keeps name as-is, else calls `reverse_name()` to flip `"Last First"` → `"First Last"`. Falls back to reversal on any exception — sgml_header.py:219

#### `FilingSummary` — edgar/sgml/filing_summary.py:323
Parses `FilingSummary.xml` from the XBRL bundle.

- `parse(xml_text) -> FilingSummary` — uses BeautifulSoup `xml` parser, extracts root-level stats and iterates `<Report>` tags, builds `pa.Table` from records, builds `short_name_map` and `category_map` dicts, parses `InputFiles` and `SupplementalFiles` — filing_summary.py:359
- `get_report_by_short_name(short_name) -> Optional[Report]` — filing_summary.py:459
- `get_reports_by_category(category) -> Reports` — filing_summary.py:462
- `get_reports_by_filename(file_name) -> Optional[Report]` — filing_summary.py:465
- `statements` (property) → `Statements` — filters to `MenuCategory=="Statements"` and wraps in `Statements` — filing_summary.py:468
- `tables` (property) → `Reports` — filters to `MenuCategory=="Tables"` — filing_summary.py:473

#### `Reports` — edgar/sgml/filing_summary.py:22
PyArrow-backed pageable collection of Report objects.

- `__getitem__(item)` — filters by `Position` column — filing_summary.py:98
- `get_by_category(category) -> Reports` — PyArrow filter on `MenuCategory` column — filing_summary.py:128
- `get_by_filename(file_name) -> Optional[Report]` — exact match on `HtmlFileName` — filing_summary.py:144
- `get_by_short_name(short_name) -> Optional[Report]` — exact match on `ShortName` — filing_summary.py:154
- `filter(column, value) -> Reports | Report` — arbitrary column/value filter with `pc.is_in` — filing_summary.py:160
- `statements` (property) → `Optional[Statements]` — category filter + Statements wrapper — filing_summary.py:136
- `next()` / `previous()` — paginated navigation via `DataPager` — filing_summary.py:73

#### `Report` — edgar/sgml/filing_summary.py:212
Single R*.htm report entry.

- `content` (property) — fetches via `sgml.get_content(self.html_file_name)` — filing_summary.py:241
- `text() -> str` — renders via `_build_renderable(500)`, returns rich text — filing_summary.py:249
- `view()` — renders to console via `_build_renderable()` — filing_summary.py:272
- `to_dataframe() -> pd.DataFrame` — calls `extract_statement_dataframe(content)` — filing_summary.py:277
- `_build_renderable(width) -> Optional[Renderable]` — renders the report as Rich output. Most R-files: single table via `_get_report_table()`. "(Tables)" and "Notes" reports that wrap a full `<table>` inside a TextBlock cell are detected by `_has_embedded_tables()` and rendered as a `Group` — one section heading per row, narrative lead-in text, then each embedded table rendered independently. Falls back to single-table if no renderables produced — filing_summary.py:278
- `_has_embedded_tables(soup) -> bool` — class method; returns `True` if any `<td>` TextBlock cell in the `.report` table contains a nested `<table>` element (#755) — filing_summary.py:273

#### `Statements` — edgar/sgml/filing_summary.py:598
Pattern-matched financial statement navigator over a `Reports` filtered to `"Statements"` category.

- Properties `balance_sheet`, `income_statement`, `cash_flow_statement`, `comprehensive_income_statement`, `equity_statement` → `Optional[Report]` — each calls `_get_statement(StatementType.X, threshold=0.5)` — filing_summary.py:631-651
- `detected_statements` (property) → `Dict[StatementType, str]` — all matched statements above 0.5 threshold — filing_summary.py:656

#### `StatementMapper` — edgar/sgml/filing_summary.py:501
Pattern-matching engine.

- `match_statement(statement) -> Dict[StatementType, float]` — regex patterns with weights 1-3, normalized to 0-1; combined patterns checked first (e.g., "operations and comprehensive income") — filing_summary.py:547

#### `MetaLinks` — edgar/sgml/metalinks.py:120
Container and query engine for `MetaLinks.json`.

- `parse(json_text) -> MetaLinks` — parses `instance[key].tag`, `instance[key].report`, `std_ref`; builds reverse calc-children index and label lowercase index at construction — metalinks.py:181
- `get_tag(tag_id) -> Optional[TagDefinition]` — O(1) by qualified ID e.g. `"us-gaap_Assets"` — metalinks.py:294
- `get_tag_by_label(label) -> Optional[TagDefinition]` — case-insensitive label lookup via pre-built index — metalinks.py:298
- `get_calculation_children(tag_id, role) -> List[TagDefinition]` — reverse index lookup, sorted by order — metalinks.py:341
- `get_calculation_roots(role) -> List[TagDefinition]` — tags where `entry.root==True` for role — metalinks.py:348
- `get_calculation_tree(tag_id, role, max_depth=10) -> dict` — recursive nested dict with `tag`, `weight`, `order`, `children` — metalinks.py:357
- `search(query, category=None) -> List[TagDefinition]` — ranked: exact > starts_with > word > substring; optionally scoped to category's presentation roles — metalinks.py:386
- `get_tags_for_role(role) -> List[TagDefinition]` — all tags with role in their `presentation` list — metalinks.py:337

#### `TagDefinition` — edgar/sgml/metalinks.py:38
XBRL concept definition.

- `namespace` (property) — prefix from `tag_id.split('_', 1)[0]` — metalinks.py:53
- `is_standard` (property) — True if namespace in `('us-gaap', 'dei', 'srt', 'ecd', 'country', 'stpr', 'ifrs-full')` — metalinks.py:62
- `is_monetary`, `is_member`, `is_axis` (properties) — type classification — metalinks.py:67-75
- `calculation_in(role) -> Optional[CalculationEntry]` — metalinks.py:77
- `is_root_in(role) -> bool` — metalinks.py:81

#### `ConceptReport` / `extract_concepts_from_report` — edgar/sgml/concept_extractor.py
Parses R*.htm files to produce concept-annotated rows.

- `extract_concepts_from_report(html_content, form=None) -> ConceptReport` — finds `<table class="report">`, extracts title + scaling from `<th class="tl">`, uses `_extract_period_headers()` with a virtual grid (honors colspan/rowspan), picks primary period via `_pick_primary_period()`, iterates body rows by CSS class (`re`/`ro`/`reu`/`rou`/`rh`), maps each value cell to semantic column by position not index — concept_extractor.py:481
- `ConceptRow.numeric_value` (property) — returns value for `primary_period` only; returns `None` if primary period absent (guards against returning prior-year values) — concept_extractor.py:99
- `ConceptRow.numeric_values` (property) — all period values as floats — concept_extractor.py:115

#### `FinancialTableExtractor` / `extract_statement_dataframe` — edgar/sgml/table_to_dataframe.py
DataFrame extraction from HTML report tables.

- `extract_statement_dataframe(report_content) -> pd.DataFrame` — parses HTML with `HTMLParser`, finds first table with `>20%` numeric cells and `>=3 rows`, delegates to `FinancialTableExtractor` — table_to_dataframe.py:297
- `extract_table_to_dataframe(table_node) -> pd.DataFrame` — extracts metadata (currency, units, scaling), classifies vertical vs standard table layout, builds DataFrame with period headers as columns, applies scaling — table_to_dataframe.py:59

#### `Attachment` — edgar/attachments.py:254
Single embedded document.

- `content` (property) — if `sgml_document` present, returns `sgml_document.content` (zero-network); else `download_file(self.url)` — attachments.py:283
- `content` (setter) — stores `_content_override` for test patching — attachments.py:305
- `download(path=None)` — if path is None returns content; if dir saves to `path/document`; handles bytes vs str — attachments.py:371
- `view()` — for R*.htm calls `filing_summary.reports.get_by_filename()` then `report.view()`; for HTML parses via `Document.parse()` — attachments.py:398
- `text() -> Optional[str]` — similar dispatch: R*.htm → `report.text()`, HTML → `Document.parse()` text, else raw content — attachments.py:421
- `markdown(...) -> Optional[str]` — HTML only; cleans via `get_clean_html()`, converts via `to_markdown()` — attachments.py:438
- `display_description` (property) — prefers `purpose` (from FilingSummary short_name), then raw description, then `_lookup_exhibit_description(doc_type)` — attachments.py:314
- `url` (property) — `sec_document_url(self.path)` — attachments.py:330
- `is_report() -> bool` — matches `R\d+\.htm` pattern — attachments.py:418

#### `Attachments` — edgar/attachments.py:488
Collection with dual structure: `documents` (human-readable) + `data_files` (XBRL/XML) + `primary_documents`.

- `__getitem__(item)` — int/digit → `get_by_sequence`; str → iterate by `.document` filename — attachments.py:506
- `get_by_sequence(sequence)` — linear scan by `sequence_number` — attachments.py:518
- `query(query_str, include_data_files=True) -> Attachments` — `eval()`-based filter with `allowed_attrs = {document, description, document_type}`, handles `re.match()` pattern specially — attachments.py:595
- `exhibits` (property) — primary + `query("re.match('EX-', document_type)")` — attachments.py:578
- `primary_html_document` (property) — first primary doc with `.html`/`.htm` extension; falls back to `primary_documents[0]` — attachments.py:546
- `primary_xml_document` (property) — first primary doc with `.xml` extension — attachments.py:562
- `download(path, archive=False)` — if `sgml` present delegates to `sgml.download()`; else async downloads all via `asyncio.gather` — attachments.py:640
- `serve(port=8000)` — downloads to tempdir, starts `SimpleHTTPRequestHandler` in a daemon thread, opens browser — attachments.py:683
- `markdown(...) -> Dict[str, str]` — iterates HTML attachments, returns filename → markdown dict — attachments.py:727
- `load(soup) -> Attachments` — scrapes `<table class="tableFile">` from homepage HTML — attachments.py:799

#### `FilingHomepage` — edgar/attachments.py:917
EDGAR filing index page wrapper.

- `load(url) -> FilingHomepage` — fetches URL, parses HTML with BeautifulSoup, calls `Attachments.load(soup)` — attachments.py:1067
- `get_filers() -> List[FilerInfo]` — scrapes `div#filerDiv` blocks; cached — attachments.py:966
- `get_filing_dates() -> Tuple[filing_date, accepted_date, period]` — label-based `infoHead`/`info` div scraping with positional fallback; cached — attachments.py:1021
- `xbrl_document` (property) — searches `datafiles` reversed for `description in xbrl_document_types` — attachments.py:957

---

### Class hierarchy

```
SGMLParser
  ├── SubmissionFormatParser   (modern <SUBMISSION> format)
  └── SecDocumentFormatParser  (legacy <SEC-DOCUMENT> format)

SGMLDocument  (dataclass, zero-copy lazy content)

FilingSGML
  ├── header: FilingHeader
  │     ├── filing_metadata: FilingMetadata
  │     ├── filers: List[Filer]
  │     │     ├── company_information: CompanyInformation  (frozen dataclass)
  │     │     ├── filing_information: FilingInformation    (frozen dataclass)
  │     │     ├── business_address: Address
  │     │     ├── mailing_address: Address
  │     │     └── former_company_names: List[FormerCompany]
  │     ├── reporting_owners: List[ReportingOwner]
  │     │     └── owner: Owner  (lazy name reversal)
  │     ├── issuer: Optional[Issuer]
  │     └── subject_companies: List[SubjectCompany]
  ├── _documents_by_sequence: DefaultDict[str, List[SGMLDocument]]
  ├── _documents_by_name: Dict[str, SGMLDocument]
  ├── attachments (cached_property): Attachments
  │     ├── documents: List[Attachment]
  │     ├── data_files: List[Attachment]
  │     └── primary_documents: List[Attachment]
  └── filing_summary (cached_property): Optional[FilingSummary]
        ├── reports: Reports  (PyArrow Table)
        │     └── __iter__ → Report
        │           └── to_dataframe() via extract_statement_dataframe()
        ├── statements: Statements
        │     └── StatementMapper (pattern-scoring engine)
        ├── input_files: List[File]
        └── supplemental_files: List[File]

MetaLinks
  ├── _tags: Dict[str, TagDefinition]
  │     └── calculations: Dict[str, CalculationEntry]
  ├── _reports: Dict[str, MetaLinksReport]
  ├── _auth_refs: Dict[str, AuthRef]
  └── _calc_children: Dict[role → Dict[parent → [(child_id, CalculationEntry)]]]

ConceptReport
  ├── period_headers: List[str]
  └── rows: List[ConceptRow]

FilingHomepage
  └── attachments: Attachments   (loaded from index HTML, no sgml_document set)
```

---

### Configuration & options

| Option | Type | Default | Effect |
|---|---|---|---|
| `SGMLParser` `_MAX_CONTENT_SIZE` | int | 500 * 1024 * 1024 | Max content bytes; raises ValueError if exceeded |
| `SGMLDocument._content_ref` | str | `""` | Reference to full SGML string (zero-copy) |
| `Attachment.sgml_document` | Optional[SGMLDocument] | None | If set, content served from memory; else network download |
| `Attachment.purpose` | Optional[str] | None | Label from FilingSummary short_name; overrides display_description |
| `Attachments.query()` `include_data_files` | bool | True | Whether to filter data_files alongside documents |
| `Attachments.serve()` `port` | int | 8000 | TCP port for local attachment server |
| `AttachmentServer` `port` | int | 8000 | TCP port |
| `FilingHeader.parse_from_sgml_text()` `preprocess` | bool | False | True enables `preprocess_old_headers()` for 1990s tab format |
| `Owner.__init__()` `needs_reversal` | bool | False | True triggers lazy Entity lookup to decide name reversal |
| `extract_concepts_from_report()` `form` | Optional[str] | None | For annual forms (10-K etc.) picks longest-duration period as primary |
| `MetaLinks.get_calculation_tree()` `max_depth` | int | 10 | Recursion limit for calculation tree |
| `MetaLinks.search()` `category` | Optional[str] | None | Scope search to tags in a specific menu category |
| `Statements._get_statement()` `threshold` | float | 0.5 | Min confidence score to return a matched statement |
| `FilingSGML.from_source()` cache bypass | implicit | — | If cached content `<50 bytes`, retries via direct `httpx.Client` |
| `FinancialTableExtractor` numeric threshold | 0.2 | — | Table needs `>20%` numeric cells to be considered financial |

---

### Data flow / lifecycle

**SGML parsing pipeline:**
1. `Filing.sgml()` calls `FilingSGML.from_filing(filing)` → `from_source(text_url)` → `read_content_as_string(url)` (streaming with gzip support, HTTP cache)
2. Empty-response guard: if `<50 bytes` and URL source, retries with direct `httpx.Client` bypass
3. `parse_submission_text(content)` calls `SGMLParser().parse(content)`:
   - Detects `SUBMISSION` vs `SEC_DOCUMENT` format
   - `SUBMISSION`: `SubmissionFormatParser` splits at first `<DOCUMENT>`, parses header line-by-line into nested dict (using `_SECTION_TAGS` and `_REPEATABLE_TAGS` sets), extracts docs with `_extract_all_documents()`
   - `SEC_DOCUMENT`: `SecDocumentFormatParser` finds `<SEC-HEADER>…</SEC-HEADER>` block, extracts docs similarly
4. `_extract_all_documents()` uses `str.find('<DOCUMENT>')` offset scanning — zero-copy, stores `content_ref + _content_start + _content_end` per document
5. `FilingHeader` is created from parsed data; `_documents_by_sequence` defaultdict keyed by sequence string, `_documents_by_name` by filename
6. `FilingSGML` instance is cached as `filing._sgml`

**Attachments lazy build:**
1. `Filing.attachments` → `self.sgml().attachments` (cached_property on `FilingSGML`)
2. Iterates `_documents_by_sequence`, creates one `Attachment` per `SGMLDocument` with `sgml_document=doc` (zero-network content)
3. For any doc with a matching `FilingSummary.xml` R-file entry, sets `attachment.purpose = report.short_name`
4. Sequence `"1"` → primary_documents; XML/XSD/XBRL filenames → data_files; rest → documents
5. `Attachments(document_files, data_files, primary_documents, sgml=self)` returned

**FilingSummary lazy build:**
1. `FilingSGML.filing_summary` (cached_property) looks up `"FilingSummary.xml"` in `_documents_by_name`
2. Calls `document.content` (materializes from `<XML>` tag in the SGML stream)
3. `FilingSummary.parse(xml_text)` — BeautifulSoup XML parse, builds `pa.Table` from report records, populates `short_name_map` and `category_map`
4. Back-references wired: `reports._filing_summary = filing_summary`, `filing_summary._filing_sgml = sgml`

**Content access path (zero-network for SGML-loaded filings):**
- `Attachment.content` → `sgml_document.content` → `get_content_between_tags(raw_content)` → materializes slice of original string from stored offsets

**Report content access path:**
- `Report.content` → `reports._filing_summary._filing_sgml.get_content(html_file_name)` → `_documents_by_name[filename].content`

**Fallback chain for `Filing.sgml()`:**
1. Return cached `_sgml` if present
2. Check local storage path → `from_source(local_path)`
3. Check datamule storage → `get_datamule_filing(accession_no)`
4. Network fetch → `from_filing(self)` → `from_source(text_url)`
5. On transient error (empty response, HTML error page) → `from_homepage(homepage)` (minimal: empty header, attachments from index HTML with live URLs)
6. `SECIdentityError`, `SECFilingNotFoundError`, `IdentityNotSetException`, network exceptions — re-raised immediately without fallback

---

### Design patterns

- **Zero-copy lazy content** — `SGMLDocument` stores `(content_ref, start, end)` instead of extracting substrings; the full SGML string is kept alive until `raw_content` is accessed. Eliminates memory duplication for 300MB+ filing bundles.
- **Cached property** — `FilingSGML.attachments`, `FilingSGML.filing_summary`, `FilingSGML.entity`, `Filing.reports`, `Filing.statements`, `Filing.header` all use `@cached_property` to compute once on first access.
- **Strategy / sub-parser dispatch** — `SGMLParser` detects format and delegates to `SubmissionFormatParser` or `SecDocumentFormatParser`; both produce the same output dict shape.
- **Backfill pattern** — `FilingSGML.from_filing()` patches missing metadata (accession#, CIK, form) from the parent `Filing` object after parsing, handling cases where the SGML header is incomplete.
- **Stack-based hierarchical parser** — `SubmissionFormatParser._handle_header_line()` tracks `current_path` as a list of `(tag, index)` tuples to navigate an arbitrarily nested dict while reading the header line-by-line.
- **Two-level description resolution** — `Attachment.display_description` checks `purpose` (from FilingSummary) → raw `description` → `_lookup_exhibit_description(doc_type)` → Reg S-K exhibit code table, giving human-readable labels without extra network calls.
- **eval-based query DSL** — `Attachments.query()` uses `eval()` with a restricted namespace containing only `re` and `attachment`, enabling ad-hoc filtering like `"document_type in ['EX-99.1', 'EX-99']"`.
- **Reverse index build at construction** — `MetaLinks.__init__()` immediately builds `_calc_children` (parent → children per role) and `_label_index` (lowercase label → tag_id) for O(1) lookup and ranked search.
- **PyArrow columnar storage** — `Reports` stores report records in a `pa.Table`, enabling `pc.is_in` filtered views without Python-level loops.
- **Grid-based column mapping** — `concept_extractor._build_header_grid()` builds a virtual grid honoring colspan/rowspan so R*.htm period headers are mapped by column position rather than index, correctly handling footnote markers and multi-row headers.

---

### Cross-domain interactions

**This domain imports from:**
- `edgar.attachments` — `Attachment`, `Attachments`, `get_document_type` (sgml_common.py)
- `edgar.sgml.filing_summary` — `FilingSummary` (sgml_common.py)
- `edgar.sgml.sgml_header` — `FilingHeader` (sgml_common.py)
- `edgar.sgml.sgml_parser` — `SGMLDocument`, `SGMLFormatType`, `SGMLParser`, `parse_document` (sgml_common.py)
- `edgar.sgml.tools` — `is_xml`, `get_content_between_tags` (sgml_common.py, sgml_parser.py)
- `edgar._party` — `Address`, `get_addresses_as_columns` (sgml_header.py)
- `edgar.entity` — `Entity` (sgml_header.py, sgml_common.py — lazy import for CIK → entity lookup)
- `edgar.core` — `binary_extensions`, `text_extensions`, `has_html_content`, `DataPager`, `PagingState` (attachments.py, filing_summary.py)
- `edgar.httprequests` — `download_file`, `get_with_retry`, `stream_with_retry` (attachments.py, sgml_common.py)
- `edgar.documents` — `HTMLParser`, `ParserConfig` (filing_summary.py, table_to_dataframe.py)
- `edgar.files.html_documents` — `get_clean_html` (attachments.py)
- `edgar.files.markdown` — `to_markdown` (attachments.py)
- `edgar.vendored.uu` — UU decoder for binary-encoded attachments (sgml_parser.py)
- `edgar.reference` — `describe_form`, `states` (sgml_header.py)
- `edgar.xmltools` — `child_text` (filing_summary.py)

**Consumed by:**
- `edgar._filings.Filing` — `sgml()`, `header` (cached_property), `attachments` (property), `reports` (cached_property), `statements`, `viewer`
- `edgar.xbrl` — `XBRL.from_filing()` which accesses `FilingSGML.attachments` for XBRL instance document
- `edgar.company_reports` — various report types call `Filing.sgml()` / `Filing.attachments`
- `edgar.viewer` — `FilingViewer.from_filing()` reads `MetaLinks.json` via `FilingSGML.get_content()`

---

### Gotchas & notable behaviors

- **Format detection order matters** — `SGMLParser.detect_format()` checks for valid SGML structure (`<SUBMISSION>`, `<SEC-DOCUMENT>`, `<IMS-DOCUMENT>`, `<DOCUMENT>`) BEFORE checking for HTML content. This prevents false positives when SGML bundles contain HTML inside `<TEXT>` sections — sgml_parser.py:224.
- **`<DOCUMENT>` without `</DOCUMENT>` is logged and silently truncated** — `_extract_all_documents()` logs a warning and stops processing if the closing tag is missing — sgml_parser.py:511.
- **Legacy 1990s SEC-DOCUMENT headers** — `parse_from_sgml_text()` has a two-pass approach: first attempt normal parsing, on `KeyError`/`ValueError`/`IndexError` retries with `preprocess=True` which calls `preprocess_old_headers()` to strip full tags and convert to tab-indented format — sgml_common.py:203.
- **Data-file classification** — the `is_datafile` flag in `FilingSGML.attachments` is set once and sticky: if any document (by filename extension) is XML, all subsequent documents also go to `data_files`. This is an intentional shortcut — sgml_common.py:351.
- **Owner name reversal is lazy and fallible** — `Owner.name` calls `Entity(cik)` which makes a network request; exceptions cause a fallback to always reverse the name (treating the owner as an individual) — sgml_header.py:225.
- **`FilingSGML.from_homepage()` produces a hollow instance** — the `attachments` cached_property is directly overwritten in `__dict__` to bypass the normal cached_property mechanism. The header is empty (`text=""`, `filing_metadata={}`) and `get_content()` always returns None — sgml_common.py:482.
- **`Attachments.query()` uses `eval()`** — the query string is executed with only `re` and `attachment` in scope. Callers must only reference `{document, description, document_type}` attributes — attachments.py:595.
- **Content type normalization** — `get_document_type()` corrects for SEC mis-declarations: if the declared type is one of `XML/HTML/PDF/HTM/JS/CSS/ZIP/XLS/XSLX/JSON`, the actual file extension is used instead — attachments.py:188.
- **Primary period selection for annual filings** — `_pick_primary_period()` in concept_extractor detects annual forms (10-K, 20-F, 40-F) and picks the longest-duration "X Months Ended" column header as the primary period, avoiding the case where quarterly columns appear before annual columns in a 10-K (GH #818) — concept_extractor.py:449.
- **Duplicate period headers** — if two semantic columns in an R*.htm table have the same label (e.g. two `"Mar. 29, 2025"` columns), the second is disambiguated by appending the column position `"Mar. 29, 2025 (3)"` — concept_extractor.py:606.
- **`ConceptRow.numeric_value` guards primary period absence** — if `primary_period` is None or absent from the row's `values` dict, returns `None` rather than the first available period value, preventing silent wrong-year bindings (GH #810) — concept_extractor.py:99.
- **Footnote marker cells** — R*.htm header rows include `[1]`, `[a]` etc. as standalone `<th>` elements. `_FOOTNOTE_MARKER_RE` filters them out before building semantic columns so they don't become spurious period columns (GH #812) — concept_extractor.py:39.
- **`ConceptReport.currency_scaling` is unreliable** — the docstring warns this field is populated by a narrow text match on the R*.htm header and should be replaced by scale derived from XBRL `decimals` attribute when accessed via `ViewerReport.currency_scaling` — concept_extractor.py:128.
- **TextBlock-wrapped tables require the `_build_renderable` path** — SEC XBRL "(Tables)" and some "Notes" R-files embed a complete `<table>` inside a `<td>` TextBlock cell. The old single-table renderer flattened these into a single outer row, losing structure. `Report._build_renderable()` detects the pattern via `_has_embedded_tables()` and renders each embedded table as an independent Rich table, preserving the nested structure. `Report.text()` and `Report.view()` both use this path — filing_summary.py:278 (#755).
- **SUBMISSION vs SEC-DOCUMENT key name differences** — SUBMISSION format uses hyphenated keys (`CONFORMED-NAME`, `CIK`, `STANDARD-INDUSTRIAL-CLASSIFICATION`), while SEC-DOCUMENT uses space-separated keys (`COMPANY CONFORMED NAME`, `CENTRAL INDEX KEY`, `STANDARD INDUSTRIAL CLASSIFICATION`). `parse_submission_format_header()` and `parse_from_sgml_text()` handle the two formats separately — sgml_header.py:455 vs sgml_header.py:724.
- **`_REPEATABLE_TAGS` controls list vs dict in SUBMISSION header** — tags like `FILER`, `REPORTING-OWNER`, `SERIES` are stored as lists; non-repeatable section tags like `COMPANY-DATA` are stored as single dicts — sgml_parser.py:341.
- **`FilingSummary._filing_sgml` is None until wired** — `FilingSummary.parse()` returns an instance with `_filing_sgml = None`; `FilingSGML.filing_summary` (cached_property) wires it back after parsing — sgml_common.py:365.
- **Max SGML size is 500MB** — real 10-Ks with embedded images can exceed 300MB; the 500MB cap is intentional headroom with a hard OOM guard — sgml_parser.py:16.
