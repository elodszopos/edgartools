# Doc Index

Quick-reference for selecting docs by task scope. Read 2-4 per task (SIMPLE=2, MEDIUM=3, COMPLEX=4).
Always include the most specific doc plus the relevant overview. Entry point for the public API is `edgar/__init__.py` (`find`, `obj`, `get_filings`).

## Entry & Data Access

core-filing-access            Filing, Filings, find(), obj() dispatch
http-networking-storage       requests, rate limiting, cache, local/cloud/datamule storage
reference-search              ticker/CIK/CUSIP lookup, company subsets, EFTS full-text search

## Companies & Financials

entity-company                Company, Entity, EntityFacts, submissions
entity-facts-statements       facts to statements, FactQuery, concept mappings, TTM
reports-financials            TenK/TenQ/EightK, Financials, auditor, subsidiaries, earnings

## XBRL Engine

xbrl-core                     XBRL, Statement, StatementLineItem, FactsView, Notes
xbrl-rendering-periods        statement rendering, period selection, validation, currency
xbrl-parsers-standardization  six linkbase parsers, concept standardization, reverse index
xbrl-stitching-analysis       multi-filing stitching, ratios, fraud metrics, synonym groups

## Documents & Content

documents-parsing             modern HTML parser, Document, node tree, table extraction, search
documents-extraction          section detectors, strategies, renderers, BM25 ranking
sgml-attachments              SGML submission parsing, Attachments, FilingSummary, MetaLinks
legacy-html-markdown          legacy files parser, ChunkedDocument, HTML to markdown
display-datatools             rich display, design language, DataFrame and XML utilities

## Filing Types

ownership-holdings            Form 3/4/5, Schedule 13D/13G, 13F holdings, Form 144
offerings-registration        Form C/D, S-1/S-3, 424B prospectus, DRS, Effect
funds                         Fund hierarchy, N-PORT, N-MFP, N-CEN, N-CSR, 497K
specialized-filings           proxy statements, municipal advisor, correspondence, ABS, ATS-N, BDC

## AI Integration

ai-core-mcp                   MCP server, tool surface, formats, helpers
ai-evaluation-skills          eval harness, judge, skills install/export
