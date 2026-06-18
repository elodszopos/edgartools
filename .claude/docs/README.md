# EdgarTools Documentation — AI-Optimized Reference

## What is EdgarTools?

Python library that turns SEC EDGAR filings into typed Python objects — financial statements, insider trades, fund holdings, proxy statements, and 24+ form types — behind a small public API (`Company`, `Filing`, `find`, `obj`, `get_filings`).

## Architecture at a Glance

- **Entry**: `edgar/__init__.py` exposes `find()` (id → Entity/Filing/Fund), `obj()` (Filing → typed data object via a 40+ form dispatch table), `get_filings()`, `Company`.
- **Access spine**: `Filing`/`Filings` (PyArrow-backed) load SGML lazily; everything is `cached_property` / `lru_cache` — no network until a field is touched. Storage resolves local → datamule → network.
- **Two financial-data paths**: (1) `Company.get_facts()` → `EntityFacts` builds standardized multi-period statements from the SEC company-facts API using learned concept mappings; (2) `filing.xbrl()` → `XBRL` parses per-filing XBRL from six linkbases and renders statements from the presentation tree.
- **Typed reports**: `filing.obj()` returns `TenK`/`TenQ`/`EightK`, ownership forms, offerings, funds, proxy, etc.; each is a thin lazy wrapper over a `Filing` with a `from_filing()` factory.
- **Documents**: `edgar/documents` is the modern HTML parser (Document → node tree → sections/tables/search); `edgar/files` is the legacy/fallback path still used by company-report item extraction.
- **AI-native**: built-in MCP server (`edgartools-mcp`), installable skills, and an evaluation harness.

## Doc Index

| Doc File | Scope |
|----------|-------|
| core-filing-access | Filing, Filings, find(), obj() dispatch, identity, rate-limit modes |
| http-networking-storage | requests, throttling, cache, SSL, local/cloud/datamule storage |
| reference-search | ticker/CIK/CUSIP lookup, company subsets, EFTS full-text search |
| entity-company | Company, Entity, EntityFacts container, submissions, filings |
| entity-facts-statements | facts→statements, FactQuery, concept mappings, TTM, training |
| reports-financials | TenK/TenQ/EightK/SixK/TwentyF/FortyF, Financials, auditor, subsidiaries, earnings |
| xbrl-core | XBRL, Statement(s), StatementLineItem, FactsView, FactQuery, Notes |
| xbrl-rendering-periods | rendering pipeline, period selection, statement resolution, validation, currency |
| xbrl-parsers-standardization | instance + 5 linkbase parsers, concept standardization, reverse index |
| xbrl-stitching-analysis | XBRLS multi-filing stitching, ratios, Altman/Beneish/Piotroski, synonym groups |
| documents-parsing | HTMLParser, Document, nodes, TableNode, ParserConfig, DocumentSearch |
| documents-extraction | section detectors (TOC/heading/pattern/hybrid), strategies, renderers, ranking |
| sgml-attachments | FilingSGML, FilingHeader, Attachments, FilingSummary, MetaLinks |
| legacy-html-markdown | SECHTMLParser, HtmlDocument, ChunkedDocument, HTML→markdown |
| display-datatools | repr_rich, design language (PALETTE/SYMBOLS), DataFrame + XML helpers |
| ownership-holdings | Form 3/4/5, Schedule 13D/13G, ThirteenF, Form 144 |
| offerings-registration | FormC, FormD, RegistrationS1/S3, Prospectus424B, DRS, Effect |
| funds | Fund/FundClass/FundSeries/FundCompany, N-PORT, N-MFP, N-CEN, N-CSR, 497K |
| specialized-filings | ProxyStatement, MunicipalAdvisorForm, Correspondence, NPX, ABS, ATS-N, BDC, XmlFiling |
| ai-core-mcp | MCP server launch, tool registration, tool surface, formats/helpers |
| ai-evaluation-skills | eval harness, judge, evaluators, skill install/export |

## Key Files

| Purpose | Path |
|---------|------|
| Public API, find()/obj() dispatch | `edgar/__init__.py` |
| Filing / Filings | `edgar/_filings.py` |
| Company / Entity | `edgar/entity/core.py` |
| Entity facts container | `edgar/entity/entity_facts.py` |
| Facts → statements | `edgar/entity/enhanced_statement.py` |
| XBRL object | `edgar/xbrl/xbrl.py` |
| Statements | `edgar/xbrl/statements.py` |
| HTTP layer | `edgar/httprequests.py`, `edgar/httpclient.py` |
| SGML / attachments | `edgar/sgml/`, `edgar/attachments.py` |
| Modern document parser | `edgar/documents/` |
| Typed reports | `edgar/company_reports/` |
| MCP server | `edgar/ai/mcp/server.py` |

## Build & Test

```
hatch run test-fast        # fast tests, no network — run often
hatch run test-network     # network tests (sequential, rate-limited)
hatch run test-regression  # regression tests (tests/issues/regression/)
hatch run cov              # with coverage
```

Only parallelize fast tests to avoid SEC rate limits. Version in `edgar/__about__.py`.
