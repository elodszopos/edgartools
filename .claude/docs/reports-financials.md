## Company Reports & Financials

### Overview

This domain provides typed Python objects returned by `filing.obj()` for all major periodic report forms (10-K, 10-Q, 8-K, 6-K, 20-F, 40-F). A shared `CompanyReport` base class provides XBRL financial statements, notes, document parsing, auditor and subsidiary extraction, and AI context generation. The `Financials` and `MultiFinancials` classes wrap XBRL into a simplified metric API. `EarningsRelease` parses earnings data from 8-K EX-99 press release HTML tables. The `TTM` package calculates trailing-twelve-month metrics from `EntityFacts` quarterly data, with stock-split adjustment support.

---

### Public API surface

| Symbol | file:line | Purpose |
|--------|-----------|---------|
| `CompanyReport` | `edgar/company_reports/_base.py:23` | Base class for all periodic report objects |
| `TenK` | `edgar/company_reports/ten_k.py:62` | 10-K annual report |
| `TenQ` | `edgar/company_reports/ten_q.py:22` | 10-Q quarterly report |
| `CurrentReport` / `EightK` | `edgar/company_reports/current_report.py:201` | 8-K current report (EightK is an alias) |
| `SixK` | `edgar/company_reports/sixk.py:69` | 6-K foreign private issuer report |
| `TwentyF` | `edgar/company_reports/twenty_f.py:13` | 20-F foreign annual report |
| `FortyF` | `edgar/company_reports/forty_f.py:417` | 40-F Canadian MJDS annual report |
| `AuditorInfo` | `edgar/company_reports/auditor.py:14` | Dataclass with auditor name/location/PCAOB firm ID |
| `extract_auditor_info` | `edgar/company_reports/auditor.py:46` | Extract AuditorInfo from XBRL DEI facts |
| `Subsidiary` | `edgar/company_reports/subsidiaries.py:50` | Single subsidiary record (name, jurisdiction, ownership_pct) |
| `SubsidiaryList` | `edgar/company_reports/subsidiaries.py:63` | Collection of Subsidiary from EX-21 |
| `parse_subsidiaries` | `edgar/company_reports/subsidiaries.py:218` | Parse HTML EX-21 into List[Subsidiary] |
| `PressRelease` | `edgar/company_reports/press_release.py:35` | Single EX-99.1 attachment from 8-K |
| `PressReleases` | `edgar/company_reports/press_release.py:12` | Collection of press release attachments |
| `Financials` | `edgar/financials.py:13` | XBRL-backed financial statements + metric accessors |
| `MultiFinancials` | `edgar/financials.py:907` | Merged multi-period financial statements |
| `EarningsRelease` | `edgar/earnings.py:922` | HTML table parser for 8-K EX-99 press releases |
| `FinancialTable` | `edgar/earnings.py:449` | Single parsed financial table from an earnings release |
| `Scale` | `edgar/earnings.py:60` | Enum: UNITS / THOUSANDS / MILLIONS / BILLIONS |
| `StatementType` | `edgar/earnings.py:87` | Enum classifying table type (INCOME_STATEMENT, BALANCE_SHEET, etc.) |
| `RowType` | `edgar/earnings.py:101` | Enum: AMOUNT / PER_SHARE / SHARES / PERCENTAGE / OTHER |
| `get_earnings_tables` | `edgar/earnings.py:1365` | Convenience: all FinancialTable from an 8-K filing |
| `find_earnings_exhibit` / `find_earnings_exhibits` | `edgar/earnings.py:1417,1381` | Locate EX-99 HTML attachments |
| `TTMCalculator` | `edgar/ttm/calculator.py:103` | Core TTM aggregation from FinancialFact list |
| `TTMMetric` | `edgar/ttm/calculator.py:64` | Result dataclass: value, periods, gaps, warnings |
| `DurationBucket` | `edgar/ttm/calculator.py:54` | Duration classification constants (QUARTER/YTD_6M/YTD_9M/ANNUAL) |
| `TTMStatement` | `edgar/ttm/statement.py:17` | Full TTM financial statement (income or cashflow) with multiple line items |
| `TTMStatementBuilder` | `edgar/ttm/statement.py:197` | Builds TTMStatement from EntityFacts |
| `detect_splits` | `edgar/ttm/splits.py:28` | Find stock split events from FinancialFact list |
| `apply_split_adjustments` | `edgar/ttm/splits.py:77` | Retroactively adjust EPS and share counts for splits |
| `FilingStructure` | `edgar/company_reports/_structures.py:7` | Part-keyed item lookup structure |
| `ItemOnlyFilingStructure` | `edgar/company_reports/_structures.py:31` | Flat item-only lookup (used by 8-K, no Parts) |

---

### Key classes

#### CompanyReport (`edgar/company_reports/_base.py:23`)

Shared base for TenK, TenQ, TwentyF, FortyF (not SixK which is standalone). Holds `self._filing` and provides lazy-computed financial, document, notes, and auditor access.

- `financials` (cached_property) → `Optional[Financials]` — calls `Financials.extract(self._filing)` — `_base.py:107`
- `income_statement` (property) → delegates to `self.financials.income_statement()` — `_base.py:43`
- `balance_sheet` (property) → delegates to `self.financials.balance_sheet()` — `_base.py:47`
- `cash_flow_statement` (property) → delegates to `self.financials.cashflow_statement()` — `_base.py:51`
- `auditor` (cached_property) → calls `extract_auditor_info(self.financials.xb)` — `_base.py:54`
- `notes` (cached_property) → `Notes` from XBRL + FilingSummary hierarchy — `_base.py:62`
- `reports` (cached_property) → XBRL report pages from FilingSummary.xml — `_base.py:102`
- `document` (cached_property) → `Document` via `HTMLParser(ParserConfig(form=...))` — `_base.py:115`
- `chunked_document` (cached_property, deprecated v5→v6) → `ChunkedDocument` — `_base.py:136`
- `items` (property) → `List[str]` — section identifiers in "Item X" format — `_base.py:157`
- `__getitem__(item_or_part)` → `str|None` — section text lookup — `_base.py:190`
- `grep(pattern, regex, document)` → `GrepResult` — delegates to `filing.grep()` — `_base.py:81`
- `to_context(detail, focus)` — AI-optimized string; 'minimal'/'standard'/'full'; focus triggers cross-cutting note context — implemented per subclass
- `_focused_context(focus, detail)` — pulls statement line items + note content for a topic — `_base.py:223`

#### TenK (`edgar/company_reports/ten_k.py:62`)

Extends CompanyReport. Class-level `structure = FilingStructure({...})` defines Parts I-IV with Items 1–16.

- `document` (cached_property) — HTMLParser with form='10-K'; falls back to ChunkedDocument on error — `ten_k.py:181`
- `sections` (property) → `Sections` dict from `document.sections` — `ten_k.py:213`
- `items` (property) → maps friendly section names to "Item X" labels; falls back to chunked_document — `ten_k.py:234`
- `__getitem__(item_or_part)` → 5-priority lookup chain: (1) canonical part-key `part_{roman}_item_{n}`, (2) combined-items keys, (3) direct key, (4) friendly name, (5) chunked_document fallback — `ten_k.py:505`
- `business` / `risk_factors` / `management_discussion` / `directors_officers_and_governance` — shortcut properties to Items 1, 1A, 7, 10 — `ten_k.py:292-307`
- `subsidiaries` (cached_property) → finds first EX-21 attachment, calls `parse_subsidiaries(content)` → `SubsidiaryList|None` — `ten_k.py:309`
- `get_item_with_part(part, item, markdown)` → `str|None` — explicit part+item lookup — `ten_k.py:674`
- `get_structure()` → Rich tree of Parts/Items — `ten_k.py:709`
- `id_parse_document(markdown)` → legacy HTML ID-based parse, cached — `ten_k.py:352`

Key detail: `_ITEM_TO_PART_10K` dict maps item numbers to their SEC-canonical Part (prevents silent cross-part fallback, GH #821). Cross Reference Index format (e.g., GE, Henry Schein) detected via `CrossReferenceIndex` and used as fallback before chunked_document.

#### TenQ (`edgar/company_reports/ten_q.py:22`)

Extends CompanyReport. Parts I and II, each with their own Item 1 (Financial Statements vs. Legal Proceedings) — critical disambiguation point.

- `document` (cached_property) — HTMLParser with form='10-Q' — `ten_q.py:203`
- `sections` (property) → part-qualified keys like `part_i_item_1`, `part_ii_item_1` — `ten_q.py:225`
- `items` (property) → returns "Part I, Item X" / "Part II, Item X" format — `ten_q.py:245`
- `__getitem__(item_or_part)` → handles `'Part I, Item 1'`, `'part_i_item_1'`, `'Item 1'` (defaults to Part I), `'1'` — `ten_q.py:292`
- `get_item_with_part(part, item, markdown)` → explicit part disambiguation — `ten_q.py:389`

Key detail: `tenq['Item 1']` returns Part I Item 1 (Financial Statements) for backward compat. Use `tenq['Part II, Item 1']` for Legal Proceedings.

#### CurrentReport / EightK (`edgar/company_reports/current_report.py:201`)

Extends CompanyReport. `EightK = CurrentReport` at module level (alias). Uses `ItemOnlyFilingStructure` (no Parts). Defines all 33 8-K items (1.01–9.01).

- `document` (cached_property) — HTMLParser form='8-K', 95% detection rate — `current_report.py:318`
- `items` (property) → 3-tier fallback: (1) new parser sections, (2) chunked_document, (3) text-based `_extract_items_from_text()` for legacy SGML 1999-2001 — `current_report.py:626`
- `__getitem__(item_name)` → 3-tier fallback matching items — `current_report.py:670`
- `content_type` (cached_property) → `str` classifying filing: 'earnings', 'cybersecurity', 'restructuring', 'asset_change', 'auditor_change', 'shareholder_vote', 'material_agreement', 'director_change', 'governance', 'debt_offering', 'regulation_fd', 'other' — `current_report.py:357`
- `is_amendment` (property) → `bool`, True for 8-K/A — `current_report.py:399`
- `earnings` (cached_property) → `EarningsRelease.from_filing(self._filing)` or `None` — `current_report.py:466`
- `has_earnings` (property) → True if Item 2.02 present AND `earnings` is not None — `current_report.py:446`
- `has_press_release` (property) → True if Item 2.02 present AND press release found — `current_report.py:435`
- `press_releases` (property) → `PressReleases|None` — queries attachments for EX-99.1, EX-99, EX-99.01 HTML docs — `current_report.py:594`
- `income_statement` / `balance_sheet` / `cash_flow_statement` — delegate to `self.earnings` — `current_report.py:494-539`
- `get_income_statement(default)` / `get_balance_sheet(default)` / `get_cash_flow_statement(default)` — safe accessors returning DataFrame or default — `current_report.py:541-591`
- `get_exhibit(exhibit_type)` → `Attachment|None` — exact document_type match — `current_report.py:403`
- `get_exhibits(prefix)` → non-XBRL/non-primary exhibits — `current_report.py:415`
- `date_of_report` (property) → formatted period_of_report string — `current_report.py:735`
- `text()` → full text including all exhibit content — `current_report.py:780`

Key detail: `income_statement/balance_sheet/cash_flow_statement` on 8-K come from `EarningsRelease` (parsed HTML tables), NOT from XBRL — 8-K filings only contain DEI XBRL metadata.

#### SixK (`edgar/company_reports/sixk.py:69`)

Standalone (does NOT extend CompanyReport). No numbered item structure. Foreign private issuer reports.

- `_get_cover_metadata()` → parses and caches cover page metadata using lxml — `sixk.py:100`
- `commission_file_number`, `report_month`, `annual_report_form`, `content_description` (properties) — from cover page — `sixk.py:139-157`
- `exhibits` (cached_property) → non-graphic attachments — `sixk.py:159`
- `press_releases` (property) → same query as 8-K EX-99 filter — `sixk.py:178`
- `financials` (cached_property) → `Financials.extract(self._filing)` — rare, uses IFRS taxonomy — `sixk.py:196`
- `annual_report_form` → `'20-F'` or `'40-F'` — indicates which form issuer uses for annual reports — `sixk.py:149`

#### TwentyF (`edgar/company_reports/twenty_f.py:13`)

Extends CompanyReport. 5-part structure (Parts I-V), Items 1-19.

- `document` (cached_property) — HTMLParser form='20-F' — `twenty_f.py:114`
- `items` (property) → prefers `chunked_document.list_items()` over new parser (TOC format better handled by chunked parser) — `twenty_f.py:154`
- `__getitem__` → tries part-prefixed keys across Parts i–v, then direct item_key, then friendly key — `twenty_f.py:176`
- Convenience properties: `key_information`/`risk_factors` (Item 3), `business`/`company_information` (Item 4), `operating_review`/`management_discussion` (Item 5), `directors_and_employees` (Item 6), `major_shareholders` (Item 7), `financial_information` (Item 8), `controls_and_procedures` (Item 15) — `twenty_f.py:354-404`

Key detail: Financial statements appear in Item 17 (US GAAP/IFRS) or Item 18 (home-country standards). `auditor` property works via XBRL DEI facts — same as 10-K.

#### FortyF (`edgar/company_reports/forty_f.py:417`)

Extends CompanyReport. Canadian MJDS form wrapping an Annual Information Form (AIF). The 40-F wrapper typically contains iXBRL; the AIF is a separate exhibit.

- `aif_attachment` (cached_property) → best AIF exhibit via `_find_aif_attachment()` — 5-priority chain: EX-1 → description → AIF filename → content-sniff NI 51-102 headings → inline — `forty_f.py:445`
- `aif_html` / `aif_text` (cached_property) → raw HTML / BeautifulSoup plain text of AIF — `forty_f.py:449,527`
- `aif_document` (cached_property) → parsed Document from AIF HTML — `forty_f.py:463`
- `document` (cached_property) → overrides base; returns `aif_document` if found, else filing.html() — `forty_f.py:473`
- `mda_attachment` / `mda_html` / `mda_text` (cached_property) → MD&A exhibit — 3-priority: description → filename → content-sniff — `forty_f.py:497,503,511`
- `business` (cached_property) → extracts "Description of the Business" from AIF plain text via regex — `forty_f.py:545`
- `items` (cached_property) → detected NI 51-102 section names (not US Item numbers) — `forty_f.py:596`
- `__getitem__(key)` → case-insensitive match or keyword containment against detected sections — `forty_f.py:600`
- Named section properties: `risk_factors`, `corporate_structure`, `dividends`, `capital_structure`, `directors_and_officers`, `legal_proceedings` — `forty_f.py:555-583`
- `financials` (inherited) — wraps iXBRL from the 40-F main wrapper document — from base class

Key detail: AIF content-sniff scans first 80 KB using NI 51-102 signals (`CORPORATE STRUCTURE`, `DESCRIPTION OF THE BUSINESS`, `GENERAL DEVELOPMENT OF THE BUSINESS`, `RISK FACTORS`). Size threshold 100 KB separates real documents from certs/consents.

#### AuditorInfo / extract_auditor_info (`edgar/company_reports/auditor.py`)

- `AuditorInfo` — dataclass: `name: str`, `location: str`, `firm_id: int`, `icfr_attestation: bool` — `auditor.py:14`
- `extract_auditor_info(xbrl)` → reads DEI facts: `dei_AuditorName`, `dei_AuditorLocation`, `dei_AuditorFirmId`, `dei_IcfrAuditorAttestationFlag` — `auditor.py:46`
- Returns `None` if `dei_AuditorName` fact is absent. `firm_id` defaults to `0` on parse error.
- Used via `CompanyReport.auditor` cached_property on TenK, TenQ, TwentyF.

#### Subsidiary / SubsidiaryList / parse_subsidiaries (`edgar/company_reports/subsidiaries.py`)

- `Subsidiary` — dataclass: `name: str`, `jurisdiction: str`, `ownership_pct: Optional[float]` — `subsidiaries.py:50`
- `SubsidiaryList` — iterable wrapper; `to_dataframe()` → pandas DataFrame; `__rich__` renders table — `subsidiaries.py:63`
- `parse_subsidiaries(html_content)` → `List[Subsidiary]` — HTML table parser using BeautifulSoup; handles 2-col (name+jurisdiction) and 3-col (with ownership) layouts — `subsidiaries.py:218`
- Only top-level tables used (no nested layout tables). Header detection via `_STRONG_HEADER_PATTERNS` and corroboration rules. Section labels like "U.S. Subsidiaries:" are skipped. Empty spacer columns stripped. Footnote markers removed from names.
- Accessed via `TenK.subsidiaries` (EX-21 attachment search). Returns `None` if no EX-21 exhibit; empty `SubsidiaryList` if EX-21 present but no parseable data.

#### PressRelease / PressReleases (`edgar/company_reports/press_release.py`)

- `PressReleases(attachments)` — wraps Attachments collection; `__getitem__` returns `PressRelease(attachment)` — `press_release.py:12`
- `PressRelease(attachment)` — wraps a single Attachment — `press_release.py:35`
  - `html()` → raw HTML with caching — `press_release.py:56`
  - `text()` → plain text via `HtmlDocument.from_html()` — `press_release.py:68`
  - `to_markdown()` → `MarkdownContent` — `press_release.py:80`
  - `view()` → renders markdown — `press_release.py:76`
  - `open()` → opens in browser — `press_release.py:74`
- Query for press releases: `.htm` document AND (`description` matches `.*RELEASE` OR `document_type` in `['EX-99.1', 'EX-99', 'EX-99.01']`) — `current_report.py:598`
- For `has_press_release`, Item 7.01-only (Reg FD) filings are excluded — they typically contain investor presentations, not press releases.

#### Financials (`edgar/financials.py:13`)

Thin facade over `XBRL`. Constructed via `Financials.extract(filing)` which calls `XBRL.from_filing(filing)`. Returns `None` if filing has no XBRL data.

Statement accessors (all accept `include_dimensions` and `view: ViewType`):
- `balance_sheet()` / `income_statement()` / `cashflow_statement()` / `cash_flow_statement()` (alias) / `statement_of_equity()` / `comprehensive_income()` → `Optional[Statement]` — `financials.py:27-124`
- `cover()` → `Optional[Statement]` — DEI cover page — `financials.py:126`

Metric accessors (all accept `period_offset: int = 0`):
- `get_revenue()`, `get_net_income()`, `get_operating_income()` → concept-based search first (via standardization mappings), label-based fallback — `financials.py:326-450`
- `get_total_assets()`, `get_total_liabilities()`, `get_stockholders_equity()`, `get_current_assets()`, `get_current_liabilities()` → label-based search — `financials.py:452-608`
- `get_operating_cash_flow()`, `get_capital_expenditures()`, `get_free_cash_flow()` → label-based; FCF = OCF - abs(CapEx) — `financials.py:510-574`
- `get_shares_outstanding_basic()`, `get_shares_outstanding_diluted()` → XBRL concept-name search (`WeightedAverageNumberOf...`) — `financials.py:677-741`
- `get_financial_metrics()` → dict with 14 metrics + `current_ratio`, `debt_to_assets` — `financials.py:743`
- `get_currency_symbol()` → detects most common ISO 4217 unit from XBRL units dict; defaults to `'$'` — `financials.py:827`
- `to_context()` → AI-optimized string listing available actions — `financials.py:853`

Internal search helpers:
- `_get_standardized_concept_by_xbrl(statement_type, standard_concept_names, period_offset)` — exact local-name match against standardization mappings — `financials.py:141`
- `_get_standardized_concept_value(statement_type, concept_patterns, period_offset)` — label regex match — `financials.py:255`
- `_get_concept_value(statement_type, concept_patterns, period_offset)` — concept column regex match — `financials.py:610`

Key detail for `get_net_income`: tries `'Net Income'` AND `'Profit or Loss'` concepts to cover both US GAAP (`NetIncomeLoss`) and IFRS 20-F filers (`ifrs-full_ProfitLoss`). Substring matching is explicitly avoided to prevent picking NCI lines (Issue #814).

#### MultiFinancials (`edgar/financials.py:907`)

Wraps `XBRLS` (multiple XBRL instances). Created via `MultiFinancials.extract(filings)` → `XBRLS.from_filings(filings)`.

- `balance_sheet(view)` / `income_statement(view)` / `cashflow_statement(view)` / `cash_flow_statement(**kwargs)` (alias) → `Optional[StitchedStatement]` — `financials.py:919-934`
- No metric convenience methods — use statement objects directly.

#### EarningsRelease (`edgar/earnings.py:922`)

Parses HTML tables from 8-K EX-99 exhibits. Does NOT use XBRL — 8-K XBRL contains only DEI metadata.

- `EarningsRelease.from_filing(filing)` → tries EX-99.1 first; if no income statement found, tries subsequent EX-99.* exhibits — `earnings.py:952`
- `document` (property) → parsed via `parse_html(html_content)` — `earnings.py:987`
- `detected_scale` (property) → finds parenthetical `(in millions)` patterns in document text — `earnings.py:1005`
- `tables` (property, cached internally) → all extracted + classified `FinancialTable` objects — `earnings.py:1029`
- `financial_tables` (property) → excludes DEFINITIONS tables — `earnings.py:1036`
- `income_statement` (property) → largest INCOME_STATEMENT table — `earnings.py:1057`
- `balance_sheet`, `cash_flow_statement`, `segment_data`, `eps_reconciliation`, `guidance` (properties) → first matching table of that type — `earnings.py:1064-1102`
- `get_key_metrics(quarterly)` → dict: revenue, net_income, eps_basic, eps_diluted, period, scale — `earnings.py:1104`
- `to_facts_dataframe()` → combined DataFrame matching `EntityFacts.to_dataframe()` schema — `earnings.py:1210`
- `summary()` → text summary of available statements — `earnings.py:1302`

#### FinancialTable (`edgar/earnings.py:449`)

Dataclass fields: `dataframe`, `scale`, `title`, `statement_type`, `periods`, `raw_index`, `row_types`.

- `scaled_dataframe` (property) → applies scale to AMOUNT rows only; PER_SHARE/SHARES/PERCENTAGE rows unscaled — `earnings.py:499`
- `get_row_type(label, position)` → positional list lookup (handles duplicate labels like two 'Basic' rows) — `earnings.py:478`
- `per_share_rows`, (property) → DataFrame slice of PER_SHARE rows — `earnings.py:492`
- `to_html(include_title, classes)` → XSS-safe HTML with optional caption — `earnings.py:536`
- `to_json(include_metadata)` → JSON with data + optional metadata — `earnings.py:573`
- `to_markdown(include_context)` → markdown for AI input — `earnings.py:607`
- `to_context(detail)` → 'minimal'/'standard'/'full' AI string — `earnings.py:634`
- `to_csv()` → CSV string — `earnings.py:689`
- `to_facts_dataframe()` → schema-compatible facts DataFrame with concept, label, value, numeric_value, unit, period_type, period_start, period_end, fiscal_year, fiscal_period — `earnings.py:703`
- `with_standardized_labels(label_mapping)` / `with_clean_columns(column_names)` → create cleaned copies — `earnings.py:774, 804`

#### TTMCalculator (`edgar/ttm/calculator.py:103`)

Calculates TTM from `List[FinancialFact]` for a single concept.

- `calculate_ttm(as_of)` → `TTMMetric` — selects 4 consecutive quarters from quarterized facts — `calculator.py:127`
- `calculate_ttm_trend(periods)` → `pd.DataFrame` — rolling TTM values; columns: `as_of_quarter`, `ttm_value`, `fiscal_year`, `fiscal_period`, `as_of_date`, `yoy_growth`, `periods_included` — `calculator.py:210`
- `quarterize()` → `List[FinancialFact]` — public access to derived quarters — `calculator.py:194`
- `_quarterize_facts()` → derives Q2=YTD_6M-Q1, Q3=YTD_9M-YTD_6M, Q4=FY-YTD_9M (or FY-Q1-Q2-Q3 fallback) — `calculator.py:525`
- `_is_additive_concept(fact)` → returns False for instant facts, shares, ratios, per-share — `calculator.py:434`
- `_deduplicate_by_period_end(facts)` → prefers periodic report forms (10-K/10-Q/20-F etc.) over non-periodic (DEF 14A, S-1) — `calculator.py:1104`
- `derive_eps_for_quarter(net_income_facts, shares_facts, eps_concept)` → derives Q4 EPS using CV-based routing: CV≤0.03 uses FY WAS; CV>0.03 derives Q4 WAS = 4×FY_WAS - 3×YTD9_WAS — `calculator.py:755`

Duration bucket constants (non-overlapping): QUARTER=70-120 days, YTD_6M=140-229, YTD_9M=230-329, ANNUAL=330-420 — `calculator.py:30-44`

#### TTMStatement / TTMStatementBuilder (`edgar/ttm/statement.py`)

- `TTMStatement` — dataclass: `statement_type`, `as_of_date`, `items` (list of dicts with label/values/concept/depth/is_total), `company_name`, `cik`, `periods` — `statement.py:17`
  - `to_dataframe()` → DataFrame with label + period columns — `statement.py:39`
  - `to_llm_string()` → markdown via `to_dataframe().to_markdown()` — `statement.py:66`
- `TTMStatementBuilder(entity_facts)` — takes `EntityFacts` — `statement.py:197`
  - `build_income_statement(as_of, max_periods)` → `TTMStatement` — `statement.py:488`
  - `build_cashflow_statement(as_of, max_periods)` → `TTMStatement` — `statement.py:512`
  - Internal `_build_statement()` derives base periods from preferred concepts (Revenue, Revenues, NetIncomeLoss), then iterates `multi_period.iter_hierarchy()` computing TTM trend per concept — `statement.py:213`
  - EPS special-cased: uses NI/shares formula rather than direct TTM sum — `statement.py:262`

#### detect_splits / apply_split_adjustments (`edgar/ttm/splits.py`)

- `detect_splits(facts)` → `List[Dict]` with `date`, `ratio` — searches for `StockSplitConversionRatio` facts; rejects facts with filing lag > 280 days or duration > 31 days; prefers 8-K instant facts for accurate effective date — `splits.py:28`
- `apply_split_adjustments(facts, splits)` → adjusted `List[FinancialFact]` — divides per-share metrics by cumulative ratio, multiplies share counts; skips monetary flows — `splits.py:77`

---

### Class hierarchy

```
CompanyReport (_base.py)
├── TenK (ten_k.py)
├── TenQ (ten_q.py)
├── TwentyF (twenty_f.py)
└── FortyF (forty_f.py)

SixK (sixk.py)          # standalone, does NOT extend CompanyReport
CurrentReport (current_report.py)  # extends CompanyReport
EightK = CurrentReport   # alias

FilingStructure (_structures.py)
└── ItemOnlyFilingStructure (_structures.py)

Financials (financials.py)        # wraps XBRL
MultiFinancials (financials.py)   # wraps XBRLS

EarningsRelease (earnings.py)
└── uses FinancialTable (earnings.py)

TTMCalculator (calculator.py)
TTMStatementBuilder (statement.py)
└── produces TTMStatement (statement.py)
    └── uses TTMCalculator internally

AuditorInfo (auditor.py)          # dataclass
Subsidiary (subsidiaries.py)      # dataclass
SubsidiaryList (subsidiaries.py)
PressRelease (press_release.py)
PressReleases (press_release.py)
```

---

### Configuration & options

| Option | Type | Default | Effect |
|--------|------|---------|--------|
| `CompanyReport.__init__(filing)` | Filing | required | The underlying Filing object |
| `Financials.extract(filing)` | Filing | required | Wraps XBRL or returns None |
| `MultiFinancials.extract(filings)` | iterable | required | Builds XBRLS from multiple filings |
| `get_revenue(period_offset)` | int | 0 | 0=most recent, 1=previous period |
| `income_statement(include_dimensions, view)` | bool, ViewType | None, None | None=False for dimensions; STANDARD for display |
| `ViewType.STANDARD` | enum | display default | Face presentation matching SEC Viewer |
| `ViewType.DETAILED` | enum | to_dataframe default | All dimensional data |
| `ViewType.SUMMARY` | enum | — | Non-dimensional totals only |
| `EarningsRelease.from_filing(filing)` | Filing | required | Finds best EX-99 exhibit |
| `get_earnings_tables(filing)` | Filing | required | Returns `List[FinancialTable]` |
| `TTMCalculator.__init__(facts)` | List[FinancialFact] | required | Facts for one concept |
| `calculate_ttm(as_of)` | date | None | None=most recent data |
| `calculate_ttm_trend(periods)` | int | 8 | Number of TTM windows; max 100 |
| `TTMStatementBuilder.build_income_statement(as_of, max_periods)` | date, int | None, 8 | Controls TTM window and depth |
| `TenK.__getitem__(item_or_part)` | str | required | 'Item 1', '1', 'business', 'Part I' |
| `TenQ.__getitem__(item_or_part)` | str | required | 'Part I, Item 1' or 'Item 1' |
| `FortyF.__getitem__(key)` | str | required | Case-insensitive NI 51-102 section name |
| `to_context(detail, focus)` | str, str/list | 'standard', None | 'minimal'/'standard'/'full'; focus=topic cross-cut |
| `parse_subsidiaries(html_content)` | str | required | Raw HTML from EX-21 attachment |
| `detect_splits(facts)` | List[FinancialFact] | required | All facts for a concept/company |
| `apply_split_adjustments(facts, splits)` | lists | required | Facts to adjust + split list from detect_splits |
| `DurationBucket.QUARTER` bounds | int constants | 70-120 days | Classification for quarterly facts |
| `DurationBucket.YTD_6M` bounds | int constants | 140-229 days | 6-month YTD classification |
| `DurationBucket.YTD_9M` bounds | int constants | 230-329 days | 9-month YTD classification |
| `DurationBucket.ANNUAL` bounds | int constants | 330-420 days | Annual classification |
| `MAX_SPLIT_LAG_DAYS` | int | 280 | Rejects split facts filed too late |
| `MAX_SPLIT_DURATION_DAYS` | int | 31 | Rejects long-duration split aggregation facts |

---

### Data flow / lifecycle

**Report object creation:**
- User calls `filing.obj()` on a Filing → dispatches to `TenK(filing)`, `TenQ(filing)`, `CurrentReport(filing)`, etc.
- Constructor runs `assert filing.form in [...]`; sets `self._filing`; all heavy work is lazy.

**Financials path (TenK/TenQ/TwentyF/FortyF/SixK):**
- `report.financials` → `Financials.extract(filing)` → `XBRL.from_filing(filing)` → parses iXBRL/XBRL from EDGAR
- `report.income_statement` → `financials.income_statement()` → `xb.statements.income_statement()` → `Statement`
- `Statement.render(standard=True)` → `to_dataframe()` used by metric getters

**Financials path (8-K):**
- `eight_k.financials` returns None (XBRL has only DEI metadata)
- `eight_k.earnings` → `EarningsRelease.from_filing(filing)` → finds EX-99.x HTML attachment → `parse_html(html_content)` → walks document tables
- Table classification uses title patterns (high-confidence) + keyword scoring (weighted: strong keywords score 2, regular score 1, threshold ≥2)
- Scale detection: parenthetical patterns `(in millions)` in document text; per-table from caption, headers, first 3 rows, footer, index labels, preceding sibling nodes

**Document / section parsing:**
- `report.document` → `HTMLParser(ParserConfig(form='10-K'))`.parse(html)` → `Document` with `.sections` dict
- TenK/TenQ: section keys are part-qualified (e.g., `part_i_item_1`) for disambiguation
- TwentyF `.items` prefers `chunked_document.list_items()` (TOC format)
- FortyF `.document` returns AIF document, not the 40-F wrapper
- Legacy `chunked_document` available in TenK/TenQ as fallback (deprecated v5, removed v6)

**Auditor extraction:**
- `report.auditor` → `extract_auditor_info(xbrl)` → `xbrl._find_facts_for_element('dei_AuditorName')` etc.
- Source: DEI XBRL facts; requires XBRL data to be present (returns None if no financials or no xb)

**Subsidiary extraction:**
- `tenk.subsidiaries` → iterates `filing.attachments`; finds first `doc_type.startswith('EX-21')`; calls `parse_subsidiaries(content)`
- Parser uses BeautifulSoup on HTML; skips nested tables; strips spacer columns; classifies rows as header/section-label/data

**TTM calculation:**
- Entry via `Company.get_ttm_revenue()` → `TTMCalculator(revenue_facts).calculate_ttm()`
- `_quarterize_facts()`: separates by duration bucket → derives Q2/Q3/Q4 → deduplicates by period_end (prefers periodic forms over proxies/S-1s)
- `calculate_ttm_trend()`: detects FYE month from facts to avoid fiscal_year label collisions (GH #793); uses `calculate_fiscal_year_for_label()` not tagged `fiscal_year`
- EPS trend: separate path using NI/shares formula to avoid summing per-share values

**Split adjustment:**
- `detect_splits(facts)` → `apply_split_adjustments(facts, splits)` → clone facts with new numeric_value
- Monetary flows (revenue, net income) are NOT adjusted — only per-share and share-count facts

---

### Design patterns

- **Lazy evaluation via `cached_property`**: All expensive operations (XBRL parsing, HTML parsing, AIF download, section detection) are deferred and computed once. Used throughout `CompanyReport`, `TenK`, `TwentyF`, `FortyF`, `EarningsRelease`.
- **Multi-tier fallback chain**: 8-K item parsing uses new parser → chunked_document → text extraction. TenK uses new parser → Cross Reference Index → chunked_document. Prevents regression across all filing eras (1999–present).
- **Canonical part mapping for disambiguation**: `_ITEM_TO_PART_10K` dict constrains 10-K item lookup to its SEC-defined Part, preventing a section detector mis-labeling one Part's content as another's (GH #821).
- **Strategy pattern for parsing**: `HTMLParser(ParserConfig(form='10-K'))` selects form-specific section detection; `ParserConfig.form` drives pattern selection without subclassing.
- **Facade pattern**: `Financials` hides XBRL complexity, exposing only `Statement` objects and named metric getters. `MultiFinancials` exposes the same interface over `XBRLS`.
- **Concept-first, label-second lookup**: `get_revenue()` and similar first try `_get_standardized_concept_by_xbrl()` (exact XBRL concept name via standardization map) before falling back to `_get_standardized_concept_value()` (label regex). Prevents picking wrong rows that happen to match a label pattern (Issue #814).
- **AIF content sniffing**: FortyF uses NI 51-102 heading detection with size threshold to identify the AIF among many EX-99 exhibits, handling the wide variation in Canadian filer exhibit structures.
- **Derivation-with-validation**: TTM quarterization marks derived facts with `calculation_context` string; `_is_positive_concept()` guards against data-quality issues producing negative revenue/assets; CV-based routing for EPS derivation.
- **Form-tier deduplication**: TTM deduplication prefers facts from periodic reports (10-K/10-Q/20-F/40-F) over non-periodic (DEF 14A, S-1) to prevent proxy statement historical data corrupting quarterly trends (GH #796).

---

### Cross-domain interactions

**Imports from other edgar.* modules:**
- `edgar.xbrl.XBRL`, `edgar.xbrl.XBRLS`, `edgar.xbrl.Statement` — core XBRL parsing, used by Financials
- `edgar.xbrl.presentation.ViewType` — enum for dimensional display control
- `edgar.xbrl.statements.StitchedStatement` — multi-period statement type for MultiFinancials
- `edgar.xbrl.notes.Notes` — notes hierarchy, accessed via `CompanyReport.notes`
- `edgar.xbrl.standardization.get_default_store` — standardization mappings for metric getters
- `edgar.documents.HTMLParser`, `edgar.documents.ParserConfig`, `edgar.documents.parse_html` — HTML section and table parsing
- `edgar.files.htmltools.ChunkedDocument` — legacy parser fallback in TenK/TenQ
- `edgar.entity.models.FinancialFact` — the atomic data unit for TTM calculations
- `edgar.entity.enhanced_statement.detect_fiscal_year_end`, `calculate_fiscal_year_for_label` — FYE detection for correct TTM labels
- `edgar.entity.unit_handling.UnitNormalizer`, `UnitType` — unit classification for additivity check
- `edgar._filings.Attachments`, `Attachment` — attachment access across all report classes
- `edgar.httprequests.download_text` — used by FortyF for AIF/MD&A download

**Consumed by other edgar.* modules:**
- `edgar.company_reports` exports are consumed by `edgar._filings.Filing.obj()` dispatch logic (returns typed report objects)
- `edgar.financials.Financials` is re-exported from `edgar.company_reports.__init__` for backward compatibility
- `Company.get_ttm_revenue()` and related methods call `TTMCalculator` from `edgar.ttm`

---

### Gotchas & notable behaviors

- **8-K financial statements**: `income_statement`, `balance_sheet`, `cash_flow_statement` on `CurrentReport` come from `EarningsRelease` (HTML table parsing), NOT XBRL. `eight_k.financials` will be `None` for most 8-Ks. Always check `eight_k.has_earnings` first.
- **SixK does not extend CompanyReport**: It lacks `financials` via base class — it has its own `financials` cached_property. It also has no `auditor` or `notes` properties.
- **TenQ Item 1 collision**: Both Part I and Part II of 10-Q have an "Item 1". `tenq['Item 1']` returns Part I (Financial Statements) by backward-compat convention. Use `tenq['Part II, Item 1']` or `tenq.get_item_with_part('Part II', 'Item 1')` for Legal Proceedings.
- **TwentyF items fallback**: Items list and section access prefers `chunked_document` over the new HTMLParser because the new parser handles TOC-based 20-F format less reliably. This is the inverse of TenK/TenQ.
- **FortyF sections are NI 51-102 headings, not US Item numbers**: `forty_f.items` returns strings like `'Risk Factors'`, `'Description Of The Business'`; `forty_f['Item 5']` will not work — use `forty_f['Operating and Financial Review']` or the named properties.
- **AuditorInfo requires XBRL**: `report.auditor` returns `None` if `self.financials` is None or `financials.xb` is None. Pre-2009 filings or non-XBRL filings will always return None.
- **Subsidiary footnote stripping**: `_FOOTNOTE_PATTERN` removes trailing `(1)`, `[2]`, `*` etc. Limited to 1-2 digit numbers to avoid stripping years like `[2024]`.
- **EarningsRelease scale detection**: Uses parenthetical patterns `(in millions)` not bare word matches, to avoid false positives in narrative text. Per-table scale detection takes precedence over document-level scale.
- **TTM period label collision (GH #793)**: SEC tags comparative facts in next-year filings with the filing's fiscal_year. `calculate_ttm_trend` uses `detect_fiscal_year_end` + `calculate_fiscal_year_for_label` to derive correct labels from `period_end`, not from the tagged `fiscal_year`.
- **TTM proxy/S-1 contamination (GH #796)**: DEF 14A proxy statements can contain historical financial facts with wrong fiscal metadata. `_deduplicate_by_period_end` prioritizes periodic report forms. Facts with `fiscal_period=''` are skipped in derivation.
- **TTM Q4 derivation fallback**: Primary path is FY - YTD_9M. Fallback is FY - (Q1 + Q2 + Q3) when YTD_9M is absent (common for companies that report discrete quarters).
- **EPS special case in TTM**: EPS is NOT additive — four quarterly EPS values do NOT sum to annual EPS. TTMStatementBuilder routes EPS through `_trend_for_eps()` which computes TTM EPS = TTM_NetIncome / avg(quarterly_shares).
- **Split detection prefers 8-K instant facts**: `_split_fact_priority()` returns 0 for 8-K instant facts (period_end = actual event date) over 10-K/10-Q facts (period_end = reporting period end). Max lag = 280 days, max duration = 31 days.
- **chunked_document deprecation**: `CompanyReport.chunked_document` emits `DeprecationWarning` in v5; will be removed in v6. TenK/TenQ still use it internally as a fallback without the warning (accessed as instance attribute, not via base class property).
- **PressRelease query**: EX-99.2 is excluded from the press release query (only EX-99, EX-99.1, EX-99.01). Item 7.01-only 8-Ks (Reg FD) exclude `has_press_release` even if EX-99.1 is present.
- **FortyF AIF size threshold**: 100 KB minimum for content-sniff candidates. Small exhibits (certifications, consents) are filtered before NI 51-102 sniffing. Some filers (e.g., ENB) use EX-99.5 — all EX-99.x are checked, not just EX-99.1.
- **Financials `get_net_income` and IFRS**: tries `'Profit or Loss'` standard concept after `'Net Income'` to capture `ifrs-full_ProfitLoss` and `ifrs-full_ProfitLossAttributableToOwnersOfParent` used by foreign 20-F filers.
- **MultiFinancials has no metric getters**: Only statement-level access; no `get_revenue()` etc. Use the returned `StitchedStatement` objects directly.
