## Documents — Extraction, Strategies, Renderers & Ranking

### Overview

This domain converts a parsed `Document` node-tree (produced by the HTML parser) into useful output. It covers five subsystems: (1) **extractors** — four section-detection strategies (TOC, heading, pattern, hybrid) that locate filing sections like Item 1, MD&A, Risk Factors; (2) **strategies** — the document building pipeline (DocumentBuilder, HeaderDetectionStrategy, StyleParser, TableProcessor, XBRLExtractor) that runs during parsing; (3) **renderers** — three output formats (plain text, markdown, fast table); (4) **processors** — HTMLPreprocessor and DocumentPostprocessor that bookend the parse; and (5) supporting subsystems: a BM25/hybrid/semantic **ranking** engine, an LRU/disk **search index cache**, an **anchor/TOC cache** for navigation deduplication, and a set of **utilities** (TableMatrix with colspan/rowspan expansion, CurrencyColumnMerger, TOCAnalyzer, toc_filter, html_utils, StreamingParser).

### Public API Surface

| Symbol | file:line | Purpose |
|---|---|---|
| `TextExtractor` | `edgar/documents/extractors/text_extractor.py:13` | Extract plain text from Document with configurable options |
| `SectionExtractor` | `edgar/documents/extractors/pattern_section_extractor.py:16` | Pattern-regex section extraction for 10-K/10-Q/8-K/20-F/424B |
| `HybridSectionDetector` | `edgar/documents/extractors/hybrid_section_detector.py:22` | Orchestrates TOC→heading→pattern fallback chain |
| `TOCSectionDetector` | `edgar/documents/extractors/toc_section_detector.py:23` | TOC-based section detection wrapping SECSectionExtractor |
| `SECSectionExtractor` | `edgar/documents/extractors/toc_section_extractor.py:36` | Core TOC→anchor→text extraction engine |
| `HeadingSectionDetector` | `edgar/documents/extractors/heading_section_detector.py:19` | Heading-node section detection using HeaderInfo metadata |
| `DocumentBuilder` | `edgar/documents/strategies/document_builder.py:28` | Builds node tree from lxml HtmlElement during parsing |
| `HeaderDetectionStrategy` | `edgar/documents/strategies/header_detection.py:334` | Multi-strategy header detection (style/pattern/structural/contextual) |
| `StyleParser` | `edgar/documents/strategies/style_parser.py:12` | Parses CSS inline style strings into `Style` objects |
| `TableProcessor` | `edgar/documents/strategies/table_processing.py:34` | Advanced table struct analysis, type detection |
| `XBRLExtractor` | `edgar/documents/strategies/xbrl_extraction.py:12` | Extracts iXBRL facts from inline XBRL elements |
| `TextRenderer` | `edgar/documents/renderers/text.py:12` | Plain-text renderer (thin wrapper over TextExtractor) |
| `MarkdownRenderer` | `edgar/documents/renderers/markdown.py:12` | Markdown renderer with optional TOC, metadata, table formats |
| `FastTableRenderer` | `edgar/documents/renderers/fast_table.py:90` | High-performance (~32x faster than Rich) table renderer |
| `TableStyle` | `edgar/documents/renderers/fast_table.py:33` | Config dataclass for FastTableRenderer styles |
| `HTMLPreprocessor` | `edgar/documents/processors/preprocessor.py:12` | Cleans/normalizes raw HTML before parsing |
| `DocumentPostprocessor` | `edgar/documents/processors/postprocessor.py:13` | Post-parse cleanup: empty-node removal, heading normalization |
| `BM25Engine` | `edgar/documents/ranking/ranking.py:78` | BM25 Okapi ranking for document nodes |
| `HybridEngine` | `edgar/documents/ranking/ranking.py:219` | BM25 + semantic structure scoring combined |
| `SemanticEngine` | `edgar/documents/ranking/ranking.py:332` | Pure structure-based ranking (no text matching) |
| `RankedResult` | `edgar/documents/ranking/ranking.py:26` | Result dataclass with `node`, `score`, `rank`, `text`, `snippet` |
| `SearchIndexCache` | `edgar/documents/ranking/cache.py:34` | Memory+disk LRU cache for BM25 search indices |
| `TOCAnalyzer` | `edgar/documents/utils/toc_analyzer.py:30` | Maps section names to anchor IDs from the filing's TOC |
| `TableMatrix` | `edgar/documents/utils/table_matrix.py:22` | 2D matrix builder for colspan/rowspan expansion |
| `CurrencyColumnMerger` | `edgar/documents/utils/currency_merger.py:11` | Detects and merges split "$" + number columns |
| `AnchorCache` | `edgar/documents/utils/anchor_cache.py:15` | Caches anchor/navigation link analysis by MD5 hash |
| `LRUCache` | `edgar/documents/utils/cache.py:46` | Thread-safe LRU cache with stats |
| `CacheManager` | `edgar/documents/utils/cache.py:302` | Singleton managing style_cache, header_cache, pattern_cache, node_cache, regex_cache |
| `StreamingParser` | `edgar/documents/utils/streaming.py:19` | Event-driven streaming parser for large HTML documents |
| `find_anchor_targets()` | `edgar/documents/utils/anchor_targets.py:4` | XPath lookup for element by id or `<a name=...>` |
| `is_anchor_match()` | `edgar/documents/utils/anchor_targets.py:12` | Test if element matches anchor id |
| `filter_toc_links()` | `edgar/documents/utils/toc_filter.py:10` | Removes repetitive "Table of Contents" navigation links |
| `compute_semantic_scores()` | `edgar/documents/ranking/semantic.py:49` | Compute 0–1 structure-awareness scores for nodes |
| `extract_section_html()` | `edgar/documents/utils/section_slicer.py` | Anchor-to-anchor HTML slice returning well-formed `<div>` string |
| `build_section_subtree()` | `edgar/documents/utils/section_slicer.py` | Returns detached lxml `<div>` element for the section |
| `get_form_schema()` | `edgar/documents/form_schema.py` | Resolve form string to `FormSchema`; used by `TOCAnalyzer` |
| `FormSchema` | `edgar/documents/form_schema.py` | Declarative per-form TOC schema (bare-item cap, text rules, part ranges) |
| `TextItemRule` | `edgar/documents/form_schema.py` | Single keyword→item mapping rule for `FormSchema.text_rules` |
| `evaluate_size()` | `edgar/documents/section_size_bands.py` | Returns warning string if section length is outside expected band |

---

### Key Classes

#### Extractors

**`HybridSectionDetector`** (`hybrid_section_detector.py:22`) — Orchestrates all three detection strategies with validation pipeline.
- `detect_sections() -> Dict[str, Section]` — tries TOC→heading→pattern, applies validate/dedup/filter — `:69`
- `_try_heading_detection() -> Optional[Dict]` — confidence >= 0.7 required — `:135`
- `_try_pattern_detection() -> Optional[Dict]` — delegates to `SectionExtractor` — `:178`
- `_validate_pipeline(sections, enable_cross_validation) -> Dict` — boundary validation + dedup + confidence filter — `:100`
- `_cross_validate(sections) -> Dict` — cross-checks TOC results against pattern results; boosts confidence when methods agree — `:261`
- `_deduplicate(sections) -> Dict` — groups similar sections, keeps highest confidence, merges detection method names — `:360`
- `_filter_by_confidence(sections) -> Dict` — uses `DetectionThresholds.min_confidence`, form-specific thresholds — `:479`

**`TOCSectionDetector`** (`toc_section_detector.py:23`) — Wraps `SECSectionExtractor`, requires `document.metadata.original_html`.
- `detect() -> Optional[Dict[str, Section]]` — detects filing agent, calls SECSectionExtractor, sets `confidence=0.95` and `detection_method='toc'` — `:48`
- Section text uses **lazy closure** `_text_extractor` callback; stores `_html_source` and `_section_extractor` on `Section` for lazy table extraction — `:100`

**`SECSectionExtractor`** (`toc_section_extractor.py:36`) — Core engine for TOC→anchor→content pipeline.
- `__init__(document, agent)` — calls `_analyze_sections()` which parses HTML once and caches the lxml tree in `self._tree` — `:44`
- `_analyze_sections()` — calls `TOCAnalyzer.analyze_toc_structure()`, verifies anchor targets exist, sorts sections by logical order — `:62`
- `get_section_text(section_name, include_subsections, clean) -> Optional[str]` — extracts text between anchor boundaries using `etree.iterwalk` in document order — `:145`
- `_extract_section_content(html, boundary, include_subsections, clean)` — depth-first iterwalk from start anchor to end anchor, adds paragraph breaks at block elements — `:226`
- `_find_actual_item_content(html, item_num, boundary, clean)` — fallback: searches for uppercase "ITEM N" header in raw HTML when TOC anchor points to wrong location — `:350`
- `_get_subsections(parent_section) -> List[str]` — identifies letter-suffix subsections (Item 1A is a subsection of Item 1, but Item 10 is not) — `:493`

**`SectionExtractor`** (`pattern_section_extractor.py:16`) — Pattern-based extractor using regex for all major form types.
- Has `SECTION_PATTERNS` class variable: `Dict[form_type, Dict[section_name, List[(pattern, title)]]]` covering 10-K, 10-Q (Part I/II), 20-F (Items 1–19), 8-K (Items 1.01–9.01), and 424B forms — `:28`
- `extract(document) -> Dict[str, Section]` — form-aware; 424B variants all map to '424B' pattern key — `:529`
- `_find_section_headers(document)` — 5-strategy fallback: (1) HeadingNode, (2) SectionNode with embedded headings, (3) bold ParagraphNode with `_looks_like_section_header()`, (4) TableNode cells, (5) any ParagraphNode starting with "Item \d" — `:951`
- `_match_sections(headers, patterns, document, part_context)` — collects all candidates per section, prefers non-TOC entries, prefers uppercase headers, picks largest content size; uses `find_toc_boundaries()` to skip TOC matches — `:1108`
- `_detect_10q_parts(headers) -> Dict[int, str]` — assigns Part I/II context per header index for 10-Q disambiguation — `:1076`
- `_create_sections(matched, document) -> Dict[str, Section]` — produces Section objects with confidence=0.7 (pattern) or 0.6 (html_fallback) — `:1260`

**`HeadingSectionDetector`** (`heading_section_detector.py:19`) — Standalone heading-based detection.
- `detect() -> Optional[Dict[str, Section]]` — filters by `header_info.confidence >= min_confidence` (default 0.5) and `header_info.is_item == True` — `:50`
- `_extract_section_from_heading(heading, header_info)` — builds section from heading to next sibling at same/higher level — `:99`

#### Strategies (Parser Pipeline)

**`DocumentBuilder`** (`document_builder.py:28`) — Core HTML→node-tree converter called during parsing.
- `build(tree) -> DocumentNode` — finds body element, recursively calls `_process_element` — `:78`
- `_create_node_for_element(element, style)` — dispatches to HeadingNode (h1–h6), ParagraphNode (p), ListItemNode (li), TableNode (via `table_processing` strategy), ImageNode (img), TextNode (br, inline elements) — `:234`
- Header detection runs via `strategies['header_detection'].detect(element, context)` at confidence > `config.header_detection_threshold` — `:262`
- XBRL tracking: `_enter_xbrl_context()` / `_exit_xbrl_context()` push/pop metadata from namespaced elements to `xbrl_context_stack` — `:662`
- Page number containers are filtered: flexbox-based (Oracle), center/right-aligned, footer-style divs — `:366`
- `ix:exclude` elements are in `SKIP_ELEMENTS`; `ix:nonfraction`/`ix:continuation` treated as inline unless they contain block children — `:346`

**`HeaderDetectionStrategy`** (`header_detection.py:334`) — Combines four sub-detectors with weighted voting.
- `detect(element, context) -> Optional[HeaderInfo]` — calls all four detectors, combines with `_combine_results()` — `:365`
- `_combine_results(results, text) -> HeaderInfo` — weighted avg: pattern=0.4, style=0.3, structural=0.2, contextual=0.1; level by weighted vote; checks any detector for `is_item`/`item_number` — `:405`
- `is_section_header(text, element) -> bool` — heuristic check (no context needed): matches Item/Part patterns and major section names — `:452`
- Sub-detectors:
  - `StyleBasedDetector` — uses font-size ratio vs base, bold, centered, uppercase, margins — `:30`
  - `PatternBasedDetector` — 9 regex patterns: Item X.Y (0.95), Part (0.9), known section names (0.85), numbered (0.7), all-caps (0.6) — `:100`
  - `StructuralDetector` — checks h1-h6 tags (1.0), header/thead/caption parents, bold/strong tags, next sibling is block — `:170`
  - `ContextualDetector` — checks `_looks_like_header()` (short text, title/uppercase, no terminal punctuation), prev/next element relationships, document position and depth — `:246`

**`StyleParser`** (`style_parser.py:12`) — CSS inline style parser with `LRUCache[dict]` (max 5000 from CacheManager).
- `parse(style_string) -> Style` — checks cache first; splits on `;`, maps each property to Style fields — `:35`
- Converts all lengths to pixels: pt×1.333, em×16, in×96, cm×37.8, mm×3.78 — `:199`
- Font-weight keywords normalized to numerics: bold→700, bolder→800 — `:243`
- `merge_styles(base, override) -> Style` — delegates to `Style.merge()` — `:334`

**`TableProcessor`** (`table_processing.py:34`) — Full table struct analysis with header detection.
- `process(element) -> TableNode` — sets `table._config`, extracts caption, summary, processes structure — `:82`
- `_is_header_row(tr) -> bool` — 8 heuristics: th elements, multi-year patterns, financial period regex (compiled once via `@lru_cache(maxsize=1)`), units notation, all-bold cells, text/numeric ratio — `:389`
- `_detect_table_type(table) -> TableType` — checks FINANCIAL_KEYWORDS (36 terms), METRICS_KEYWORDS, page-number patterns for TOC, "exhibit" for EXHIBIT_INDEX — `:567`
- Special date-range handling: same-year repetition ("Jan 1, 2024–Mar 31, 2024") is NOT treated as multi-year header — `:421`
- `_extract_relationships(table)` — detects total rows, indentation levels (hierarchy metadata) — `:625`

**`XBRLExtractor`** (`xbrl_extraction.py:12`) — iXBRL fact extraction during parse.
- `extract_context(element) -> Optional[Dict]` — dispatches by local tag name: nonfraction, nonnumeric, continuation, footnote, fraction — `:47`
- `_initialize_context(element)` — lazy init: walks document root to extract all `xbrli:context` and `xbrli:unit` definitions — `:133`
- Handles continuations by `continuedAt` attribute chain — `:266`
- Transformation registry: `ixt:numdotdecimal`, `ixt:numcommadecimal`, `ixt:zerodash`, `ixt:datedoteu`, `ixt:datedotus` — `:32`

#### Renderers

**`TextRenderer`** (`renderers/text.py:12`) — Thin wrapper: creates `TextExtractor` with `include_metadata=False, include_links=False`.

**`TextExtractor`** (`extractors/text_extractor.py:13`) — Full-featured text extraction.
- Constructor options: `clean`, `include_tables`, `include_metadata`, `include_links`, `max_length`, `preserve_structure`, `table_max_col_width` (default 200) — `:24`
- `extract(document) -> str` — walks root recursively, joins with `'\n\n'` (non-structure) or `'\n'` (structure mode) — `:57`
- Tables: if `table_max_col_width` is set, uses `FastTableRenderer(TableStyle.simple())` with custom width; otherwise calls `table.text()` — `:208`
- `_is_bullet_point_container()` — detects flex-display ContainerNode with short first child (bullet char) and longer second child — `:267`
- `_clean_document_text()` — global: collapses 4+ newlines to 3; does NOT clean table content to preserve alignment — `:306`
- `_normalize_punctuation()` — em/en-dash→` - `; fixes spacing around sentence-ending punctuation, abbreviations, and percentages — `:321`

**`MarkdownRenderer`** (`renderers/markdown.py:12`) — Full structural Markdown output.
- Constructor: `include_metadata`, `include_toc`, `max_heading_level` (default 6), `table_format` ('pipe'/'grid'/'simple'), `wrap_width` — `:24`
- `render(document) -> str` — optionally prepends YAML front matter and TOC placeholder; replaces `<!-- TOC -->` after rendering — `:52`
- Tables: three formats. `pipe` uses `_expand_table_structure()` + `_combine_multi_row_headers()` to handle colspan and prioritize date-like headers — `:202`
- `_render_text(node)` — applies **bold** (`font_weight >= 700`), *italic*, `<u>` formatting; escapes Markdown chars outside tables — `:184`
- `_generate_toc()` — indented `-[text](#anchor)` entries; anchor = lowercase, spaces→hyphens, non-alphanumeric stripped — `:400`
- `_looks_like_date()` — checks for full month names or year prefixes with at least one digit — `:596`

**`FastTableRenderer`** (`renderers/fast_table.py:90`) — ~32x faster than Rich rendering.
- Uses `TableMatrix` to expand colspan/rowspan before rendering — `:110`
- `TableStyle` presets: `pipe_table()` (markdown), `minimal()`, `simple()` (Rich SIMPLE aesthetic, unicode `─` separator, max_col_width=500 for LLM contexts) — `:42`
- `render_table_data(headers, rows) -> str` — pipeline: identify meaningful columns (score-based, max 8) → merge related columns ($ + number) → calculate widths → detect alignments (numeric columns right-aligned at ≥70% ratio) → build — `:154`
- `_identify_meaningful_columns()` — scores columns by content: 3pts for ≥3 chars, 2 for 2-char alphanumeric, 1 for single char/$; keeps columns with avg ≥0.5 — `:267`
- `_should_merge_columns()` — merges if ≥50% of rows have `$` + number pattern, or if ≥70% of left-column cells are empty — `:394`
- `_detect_alignments()` — right-aligns columns where ≥70% of data values are numeric (removes $,%.()  before float check) — `:453`
- `_format_multiline_row()` — handles cells with `\n` by expanding to multiple physical lines — `:577`

#### Processors

**`HTMLPreprocessor`** (`processors/preprocessor.py:12`) — Pre-parse HTML cleanup.
- Pre-compiles 20+ regex patterns in `__init__` for performance — `:32`
- `process(html) -> str` — pipeline: remove BOM → remove XML declaration → fix encoding (Windows-1252 chars, `\xa0`) → remove `script/style/ix:hidden/ix:header` — strip comments → normalize entities → fix malformed tags → normalize whitespace → remove empty tags → fix common issues — `:88`
- Whitespace normalization adds `\n` around block elements, collapses multiple spaces/newlines — `:201`

**`DocumentPostprocessor`** (`processors/postprocessor.py:13`) — Post-parse quality pass.
- `process(document) -> Document` — pipeline: remove empty nodes → merge adjacent TextNodes (if `config.merge_adjacent_nodes`) → normalize heading levels (promotes if no H1 exists) → enhance sections (if `config.eager_section_extraction`) → add statistics → validate structure — `:29`
- `_validate_structure()` — detects orphaned nodes (adds to root), checks for circular references via DFS — `:254`
- Statistics added to `document.metadata.statistics`: node_count, text_length, table_count, heading_count, (optionally) section_count — `:239`

#### Ranking

**`BM25Engine`** (`ranking/ranking.py:78`) — Lazy-built BM25Okapi index.
- Rebuilds index if `nodes` list changes identity — `:125`
- Returns only nodes with `score > 0` — `:146`
- `get_index_data() / load_index_data()` — serializes tokenized corpus for caching — `:180`

**`HybridEngine`** (`ranking/ranking.py:219`) — BM25 (0.8) + semantic (0.2) by default.
- Normalizes BM25 scores to 0–1 before combining — `:298`
- `boost_sections` parameter for boosting specific section names — `:246`
- Validates weights sum to 1.0 (±0.01) — `:263`

**`SemanticEngine`** (`ranking/ranking.py:332`) — Pure structural ranking, no text matching.

**`compute_semantic_scores()`** (`ranking/semantic.py:49`) — 8-factor scoring:
1. NodeType boost: HEADING=2.0, SECTION=1.5, TABLE=1.0, XBRL_FACT=0.8, LIST=0.5, PARAGRAPH=0.3, TEXT=0.1
2. SemanticType boost: ITEM_HEADER=2.0, SECTION_HEADER=1.5, FINANCIAL_STATEMENT=1.2, TABLE_OF_CONTENTS=1.0
3. Cross-reference patterns (`see item N`, `refer to item`, etc.) — up to 1.5
4. Gateway terms (summary, overview, etc.) — 1.0
5. Section importance (risk factors=1.5, md&a=1.4, business=1.3, financial=1.2)
6. XBRL boost — 0.8 for XBRL_FACT
7. Text quality (length 50–1000 = +0.3; ≥2 sentences = +0.2)
8. Item header boost when query contains "item N" — +1.5
- Normalized to 0–1 by dividing by 7.0 — `:107`

**`SearchIndexCache`** (`ranking/cache.py:34`) — Two-tier LRU+disk cache.
- Memory LRU: max 10 entries; disk: `~/.edgar_cache/search/*.pkl`; TTL: 24h — `:50`
- `compute_document_hash(document_id, content_sample) -> str` — SHA-256 truncated to 16 hex chars — `:75`
- `get_stats() -> Dict` — hit_rate, memory_entries, disk_entries — `:242`

#### Utilities

**`TOCAnalyzer`** (`utils/toc_analyzer.py:30`) — Maps section names to HTML anchor IDs. Now form-aware via `FormSchema` from `edgar/documents/form_schema.py`.
- `__init__(form)` — accepts form type; loads `self.schema = get_form_schema(form)` which drives bare-item cap, text-keyword vocabulary, and `seed_part` for TOC walk initialization
- `analyze_toc_structure(html, agent, tree)` — dispatches to agent-specific parsers (Workiva, Donnelley/DFIN, Novaworks, Toppan Merrill) then falls back to generic. After all parsers: **body-header fallback** triggers when canonical item count is below floor (8 for 10-K), scanning bold body headings instead of TOC links — `:68`
- **Body-header detection** (`_analyze_body_item_headers`) — for link-less TOC 10-Ks (Goldman Sachs, Citigroup): scans bold/heading elements matching `^Item N[letter]. Title`, tracks Part context from "PART N" dividers, resolves each item to its nearest preceding anchor id — `:234`
- **Workiva**: 3-column table, multiple `<a>` per row sharing UUID href; groups by href, strips page numbers, combines texts — `:381`
- **DFIN**: "INDEX" heading, semantic anchor IDs (`#item_1_business`); item number extracted from anchor ID first, then text — `:460`
- **Novaworks**: "ITEM 1A. Risk Factors" combined text; handles shared Part/Item anchors; seeds Part I via `schema.seed_part` — `:575`
- **Toppan Merrill**: split cells like Workiva but with `#ITEM1BUSINESS_392371` style anchors; strips zero-width spaces; seeds Part I via `schema.seed_part` — `:638`
- `_make_section_key(item_name, current_part)` — for 10-K with no detected part header, infers part from `FormSchema.item_part_ranges` (Items 1–4→Part I, 5–9→Part II, etc.) so consistent `part_ii_item_7` keys are produced even when TOC lacks explicit Part headers. 10-Q: part must be detected, never inferred — `:486`
- `_normalize_section_name(text, anchor_id, preceding_item)` — priority: preceding cell label > anchor ID pattern > text > `FormSchema.match_text`. For 10-Q: unmatched text returns `""` (`skip_unmatched_text=True`) preventing bogus `part_i_<text>` keys — `:1079`
- `_item_from_anchor(anchor_id)` — letter suffix regex allows a–z but requires the letter NOT be followed by another letter; prevents `item1business` matching as `Item 1B` — `:396`
- `_item_from_anchor` part regex — requires left delimiter (`^`, `_`, `#`, `-`) before `part` token; prevents `counterparties` matching as `Part I` — `:419`
- `_extract_preceding_item_label` bare-item filter — caps accepted item number at `schema.max_bare_item`; prevents page-number `<td>8</td>` becoming phantom `Item 8` on 10-Q forms that have no Item 8 — `:927`
- `_canonical_item_count(mapping)` — counts keys matching `^(part_[ivxlcdm]+_)?item_\d+[a-z]?$`; single-letter suffix covers standard (1A, 1B, 7A) and company-specific (CAT Item 1D) suffixes — `:117`
- `_build_section_mapping()` — when duplicates exist, validates which anchor's content matches expected item heading; descriptive free-text keys that fail normalization are now dropped rather than emitted — `:1070`
- `_get_section_type_and_order()` — sort order from `FormSchema.match_text` (exclusions=False, mirroring historical inconsistency); Item 1=1000, Item 1A=1001; Part I=100, Part II=200 — `:1152`

**`find_toc_boundaries(html) -> Tuple[int, int]`** (`utils/toc_analyzer.py:1166`) — Finds the character extent of the TOC region (used by `SectionExtractor._match_sections` to skip TOC entries).

**`TableMatrix`** (`utils/table_matrix.py:22`) — 2D matrix for colspan/rowspan expansion.
- `build_from_rows(header_rows, data_rows) -> TableMatrix` — two-pass: calculate dimensions then place cells — `:35`
- `get_expanded_row(row_idx) -> List[Optional[Cell]]` — returns origin cells at first position, None for spanned positions — `:266`
- `filter_spacing_columns() -> TableMatrix` — complex column consolidation: merges `$`/number, `(`/`)`, number/`%` adjacent columns; preserves header-content columns — `:352`
- `get_data_columns() -> List[int]` — old-parser-compatible: keeps single empty columns as spacers, removes leading/trailing/consecutive empty columns — `:292`

**`CurrencyColumnMerger`** (`utils/currency_merger.py:11`) — Detects `$` columns paired with numeric columns (≥60% match threshold) and merges them — `:34`

**`AnchorCache`** (`utils/anchor_cache.py:15`) — MD5-keyed navigation pattern cache (memory + disk at `~/.edgar_cache/anchor/*.pkl`).
- `filter_with_cached_patterns(text, html) -> str` — preserves first 2 occurrences of each navigation pattern (document structure headers), filters additional repetitions — `:150`
- `_analyze_navigation_minimal()` — regex-based (no BeautifulSoup): counts anchor link texts appearing ≥5 times — `:120`

**`CacheManager`** (`utils/cache.py:302`) — Singleton with five typed caches: `style_cache` (LRU 5000), `header_cache` (LRU 2000), `pattern_cache` (LRU 10000), `node_cache` (WeakCache), `regex_cache` (LRU 500).

**`StreamingParser`** (`utils/streaming.py:19`) — `etree.iterparse`-based streaming for large documents (> CHUNK_SIZE=1MB).
- Stores `original_html` in `metadata.original_html` before parsing for TOC-based section detection — `:127`
- Does not clear elements while `_table_depth > 0` (TableProcessor needs full subtree) — `:114`
- Applies `DocumentPostprocessor` after streaming — `:138`

**`filter_toc_links(text) -> str`** (`utils/toc_filter.py:10`) — removes "Table of Contents", "Index to Financial Statements", "Index to Exhibits" lines from extracted text.

---

### Class Hierarchy

```
RankingEngine (ABC)
├── BM25Engine
├── HybridEngine          (contains BM25Engine)
└── SemanticEngine

HeaderDetector (ABC)
├── StyleBasedDetector
├── PatternBasedDetector
├── StructuralDetector
└── ContextualDetector

LRUCache[T]               (Generic, thread-safe OrderedDict)
WeakCache                 (strong-ref dict, same API)
TimeBasedCache[T]         (TTL-expiring dict)
SearchIndexCache          (memory LRU + disk pickle, different purpose)
AnchorCache               (memory dict + disk pickle)
CacheManager              (aggregates LRU/Weak caches)

TableMatrix               (2D matrix with MatrixCell)
├── ColumnAnalyzer        (uses TableMatrix)
└── CurrencyColumnMerger  (uses TableMatrix)

FastTableRenderer         (uses TableMatrix internally)
MarkdownRenderer          (uses TableNode directly)
TextRenderer              (delegates to TextExtractor)
TextExtractor             (uses FastTableRenderer when table_max_col_width set)
```

---

### Configuration & Options

| Option | Type | Default | Effect |
|---|---|---|---|
| `TextExtractor.clean` | bool | True | Normalize whitespace, punctuation |
| `TextExtractor.include_tables` | bool | True | Include table text in output |
| `TextExtractor.include_metadata` | bool | False | Prefix text with XBRL/section/type annotations |
| `TextExtractor.include_links` | bool | False | Include link URLs |
| `TextExtractor.max_length` | Optional[int] | None | Truncate at sentence/word boundary |
| `TextExtractor.preserve_structure` | bool | False | Use `#` heading markers and `[TABLE START]` markers |
| `TextExtractor.table_max_col_width` | Optional[int] | None | Forces FastTableRenderer; None uses `table.text()` |
| `MarkdownRenderer.include_toc` | bool | False | Generate `<!-- TOC -->` and replace with entries |
| `MarkdownRenderer.table_format` | str | 'pipe' | 'pipe'/'grid'/'simple' |
| `MarkdownRenderer.max_heading_level` | int | 6 | Clamps heading levels |
| `MarkdownRenderer.wrap_width` | Optional[int] | None | Wrap paragraphs at N chars |
| `TableStyle.max_col_width` | int | 50 (pipe), 40 (minimal), 500 (simple) | Max column width in chars |
| `TableStyle.padding` | int | 1 (pipe), 2 (minimal/simple) | Cell padding spaces |
| `BM25Engine.k1` | float | 1.5 | Term frequency saturation |
| `BM25Engine.b` | float | 0.75 | Length normalization |
| `HybridEngine.bm25_weight` | float | 0.8 | BM25 component weight (must sum with semantic_weight to 1.0) |
| `HybridEngine.semantic_weight` | float | 0.2 | Semantic component weight |
| `SearchIndexCache.memory_cache_size` | int | 10 | Max in-memory entries |
| `SearchIndexCache.ttl_hours` | int | 24 | Cache entry TTL |
| `SearchIndexCache.disk_cache_enabled` | bool | True | Persist to `~/.edgar_cache/search/` |
| `HybridSectionDetector.thresholds` | DetectionThresholds | default | min_confidence, cross_validation_boost, disagreement_penalty, boundary_overlap_penalty |
| `DetectionThresholds.min_confidence` | float | 0.6 | Minimum section confidence to include |
| `DetectionThresholds.enable_cross_validation` | bool | configurable | Run expensive cross-validation on TOC results |
| `DetectionThresholds.cross_validation_boost` | float | configurable | Confidence multiplier when methods agree |
| `DetectionThresholds.disagreement_penalty` | float | configurable | Confidence multiplier when methods disagree |
| `HeadingSectionDetector.min_confidence` | float | 0.5 | Minimum HeaderInfo.confidence (hybrid uses 0.7) |

---

### Data Flow / Lifecycle

**Parsing pipeline (how a Document is built):**
1. Raw HTML → `HTMLPreprocessor.process()` — strips scripts/styles/comments, fixes encoding, normalizes entities and whitespace
2. Cleaned HTML → lxml `HTMLParser` or `StreamingParser` → lxml tree
3. `StreamingParser` OR `DocumentBuilder.build(tree)` recursively processes elements:
   - `StyleParser.parse(style_attr)` called for each element (cached by `CacheManager.style_cache`)
   - `HeaderDetectionStrategy.detect(element, context)` called for non-excluded tags
   - `TableProcessor.process(element)` called for `<table>` elements
   - `XBRLExtractor.extract_context(element)` called for `ix:*` namespaced elements
4. `DocumentPostprocessor.process(document)` — remove empty nodes, merge adjacent TextNodes, normalize heading levels, optionally extract sections eagerly
5. `document.metadata.original_html` is preserved (set by StreamingParser; needed for TOC section detection)

**Section detection (lazy, on first `document.sections` access):**
1. `HybridSectionDetector.detect_sections()` is invoked
2. **Strategy 1 (TOC, confidence 0.95):** `TOCSectionDetector.detect()` → `SECSectionExtractor._analyze_sections()` → `TOCAnalyzer.analyze_toc_structure()` (agent-specific or generic) → maps section names to anchor IDs → `find_anchor_targets()` verifies anchors exist → calculates boundaries (anchor[i] to anchor[i+1]) → creates `Section` objects with lazy `_text_extractor` closure
3. **Strategy 2 (heading, 0.7–0.9):** iterates `document.headings`; requires `header_info.is_item and header_info.confidence >= 0.7`; collects nodes from heading to next sibling at same/higher level
4. **Strategy 3 (pattern, 0.7):** `SectionExtractor.extract()` → finds headers via 5-strategy fallback → detects TOC region to skip TOC entries → matches regex patterns per form type → prefers uppercase (actual) headers over mixed-case (TOC) entries
5. Validation pipeline: optional cross-validation (expensive) → boundary overlap detection → deduplication (keeps highest confidence, merges detection methods) → confidence filter
6. Text extraction from TOC sections is lazy: `section.text(clean=True)` calls the closure which calls `SECSectionExtractor.get_section_text()` → `_extract_section_content()` via `etree.iterwalk` between anchor boundaries

**Search/ranking pipeline:**
1. `BM25Engine.rank(query, nodes)` — checks if nodes list changed, rebuilds index if so → `preprocess_text()` (lowercase, normalize whitespace) → `tokenize()` (regex `\b[\w$%]+\b`, min 2 chars) → `BM25Okapi.get_scores()` → filters score > 0 → returns sorted `RankedResult` list
2. `HybridEngine.rank()` — runs BM25 first, then `compute_semantic_scores()` for all nodes → normalizes BM25 to 0–1 → weighted combination → resort
3. `SearchIndexCache.get/put` provides persistence: SHA-256 hash key, memory LRU then disk pickle, 24h TTL, LRU eviction at 10 entries

**Table rendering pipeline:**
1. `TableMatrix.build_from_rows(header_rows, data_rows)` — two-pass: calculate column count with colspan, place cells handling rowspan
2. `FastTableRenderer.render_table_node(table_node)` → `TableMatrix` → `render_table_data(headers, rows)` → identify meaningful columns → merge currency pairs → calculate widths → detect alignments → `_build_table()` → string output

---

### Design Patterns

- **Strategy pattern** — `HybridSectionDetector` tries three strategies in priority order with fallback; `HeaderDetectionStrategy` combines four sub-detectors with weighted voting; `TOCAnalyzer` dispatches to four agent-specific TOC parsers before generic fallback.
- **Lazy evaluation / lazy closures** — `TOCSectionDetector` creates closure `_text_extractor` per section; section text is not extracted until `section.text()` is called. Document `sections` property is lazy (computed on first access, cached).
- **Chain of responsibility** — `SectionExtractor._find_section_headers()` runs 5 strategies in sequence, each only activating if prior strategies didn't find Item headers.
- **Template method** — `RankingEngine` ABC defines `rank()` and `get_algorithm_name()`; concrete engines implement.
- **Singleton with lazy init** — `CacheManager` (via `get_cache_manager()`), `AnchorCache` (module-level `_anchor_cache`), `SearchIndexCache` (via `get_search_cache()`).
- **LRU cache** — `StyleParser` uses `CacheManager.style_cache`; `BM25Engine` rebuilds index only on node-list identity change; `TableProcessor._get_period_header_pattern()` uses `@lru_cache(maxsize=1)`.
- **Two-tier cache** — `SearchIndexCache` and `AnchorCache` both use memory dict + disk pickle.
- **Pre-compiled regex** — `HTMLPreprocessor` pre-compiles all 20+ patterns in `_compile_patterns()` at init time.
- **Visitor / walk pattern** — `DocumentPostprocessor` walks the node tree recursively; `TextExtractor._extract_from_node` dispatches based on node type.

---

### Cross-Domain Interactions

**This domain imports from:**
- `edgar.documents.document` — `Document`, `Section`, `DocumentMetadata`, `Sections`
- `edgar.documents.nodes` — `HeadingNode`, `ParagraphNode`, `TextNode`, `ContainerNode`, `SectionNode`, `DocumentNode`, `ListNode`, `ListItemNode`, `LinkNode`, `ImageNode`
- `edgar.documents.table_nodes` — `TableNode`, `Cell`, `Row`
- `edgar.documents.types` — `Style`, `HeaderInfo`, `ParseContext`, `NodeType`, `SemanticType`, `TableType`, `XBRLFact`
- `edgar.documents.config` — `ParserConfig`, `DetectionThresholds`
- `edgar.documents.agents` — `detect_filing_agent` (used by `HybridSectionDetector._detect_agent()`)
- `edgar.documents.exceptions` — `DocumentTooLargeError`, `HTMLParsingError`
- `edgar.paths` — `get_search_cache_directory()`, `get_anchor_cache_directory()`
- `rank_bm25` — `BM25Okapi` (third-party)
- `lxml` — `etree`, `lxml.html`, `lxml.etree.iterparse`

**Consumed by:**
- `edgar.documents.document` — `Document.sections` property triggers `HybridSectionDetector`; `Document.text()` uses `TextExtractor`
- `edgar.documents.parser` (HTMLParser) — uses `DocumentBuilder`, `HTMLPreprocessor`, `DocumentPostprocessor`, `HeaderDetectionStrategy`, `StyleParser`, `TableProcessor`, `XBRLExtractor`
- `edgar.documents.simple_parser` — uses `StreamingParser`
- Upper-layer filing classes (TenK, TenQ, EightK, etc.) — access `document.sections` which triggers the detection chain; pass `form` to `HybridSectionDetector`

---

### Gotchas & Notable Behaviors

1. **TOC confidence inflation / cross-validation is expensive** — TOC detection assigns 0.95 confidence without verifying content. Cross-validation (comparing TOC vs pattern) is opt-in via `DetectionThresholds.enable_cross_validation`; it calls `SectionExtractor.extract()` on the whole document as a side effect.

2. **`original_html` is mandatory for TOC detection** — `TOCSectionDetector` and `SECSectionExtractor` both gate on `getattr(document.metadata, 'original_html', None)`. If HTML is not stored (e.g., documents parsed without the streaming path), TOC detection silently returns None and falls to heading/pattern detection.

3. **Circular recursion guard in `_extract_section_fallback`** — `SECSectionExtractor._extract_section_fallback()` deliberately returns `None` with a comment explaining that calling `document.sections` from inside section detection would cause infinite recursion — `:459`.

4. **10-Q item disambiguation** — 10-Q filings have Item 1 in Part I (Financial Statements) AND Item 1 in Part II (Legal Proceedings). `TOCAnalyzer._make_section_key()` generates `"part_i_item_1"` / `"part_ii_item_1"` keys to distinguish them. Pattern extractor uses `_detect_10q_parts()` for the same purpose.

5. **Agent-specific TOC parsing** — `HybridSectionDetector._detect_agent()` reads `document.metadata.original_html` to detect the filing agent (Workiva, Donnelley, Novaworks, Toppan Merrill). TOC structure differs significantly per agent (UUID hrefs, semantic hrefs, split cells, zero-width spaces). Generic fallback handles unknown agents.

6. **FastTableRenderer `simple` style has max_col_width=500** — This was raised from 200 specifically for AI/LLM processing contexts to avoid truncating long financial labels.

7. **TableMatrix special-case for colspan=2 numeric values** — `_place_cells()` has a special path for `colspan==2` numeric values (>50% digit ratio, contains comma separator) that shifts content to the second position for alignment with `$167,045`-style cells — `:135`. This is labeled "Table 15-style alignment."

8. **`SectionExtractor` does NOT auto-detect form type** — `_detect_form()` was removed. Form type must be provided explicitly via `SectionExtractor(form=...)`, `document.metadata.form`, or `document._config.form`. Unknown form types return empty `{}`.

9. **Pattern extractor prefers uppercase headers** — The `_is_main_section_header()` check: `ITEM` (uppercase) is a main header; `Item` (mixed case) in the TOC region is likely a cross-reference. When all candidates for a section are TOC entries, the extractor searches the raw HTML directly via `_find_actual_section_after_toc()`.

10. **BM25 index is rebuilt when node list identity changes** — `BM25Engine` compares `self._corpus_nodes != nodes` (Python identity check `is not`). New list instances trigger rebuild even if content is identical.

11. **AnchorCache allows 2 occurrences of each navigation pattern** — `filter_with_cached_patterns()` allows up to `max_allowed_per_pattern=2` occurrences to preserve legitimate document structure headers while filtering repetitive navigation links (SEC filings average ~48 "Table of Contents" links per filing).

12. **Streaming parser does NOT clear elements during table processing** — `elem.clear()` is skipped when `self._table_depth > 0` because `_end_table()` needs the full `<table>` subtree to extract `tr/td` children. This prevents memory savings during large embedded tables.

13. **`Section.parse_section_name()` used across extractors** — All three detectors call `Section.parse_section_name(section_name)` to populate `part` and `item` fields on the resulting `Section` object. This normalization is defined in `edgar/documents/document.py:69`.

14. **Style cache is shared across all `StyleParser` instances** — `StyleParser.__init__()` calls `get_cache_manager().style_cache`, which returns the module-level singleton. Effective for repeated parsing of the same filing but means cache is never cleared within a session unless `CacheManager.clear_all()` is called.

15. **Body-header detection is 10-K-only** — `_expected_item_floor()` returns 8 only for 10-K/10-K/A; all other forms return 0, so the body-header fallback never triggers for 10-Q, 20-F, etc. The `_BODY_ITEM_HEADER` pattern (`^Item N[letter]. Title`) is 10-K-shaped.

16. **`TOCAnalyzer` form-awareness is data-driven, not branching** — All `if self.form in (...)` conditional logic was replaced by `FormSchema` lookups. The `schema` attribute drives: bare-item cap, text-keyword vocabulary, `skip_unmatched_text`, part-inference ranges, and `seed_part` for TOC walk initialization. Adding support for a new form means adding a `FormSchema` entry in `form_schema.py`, not editing `toc_analyzer.py`.

17. **Part I seeding for 10-Q TOC walks** — All agent-specific parsers and the generic scanner initialize `current_part = self.schema.seed_part`. For 10-Q, this is `"Part I"`, so items appearing before any explicit Part header row are correctly attributed to Part I. For 10-K, `seed_part` is `None` (part inferred from item number instead).

18. **Part label leak fix in `_item_from_anchor`** — The part regex requires a left word boundary (`^|[_\s#-]`) before the `part` token. Without this, anchor IDs like `counterparties_section` would match as `Part I` and corrupt all subsequent item keys in the walk.

19. **`Section.tables()` and `Section.markdown()` share `section_slicer`** — Both now delegate HTML slicing to `edgar.documents.utils.section_slicer.extract_section_html()`. This fixes issue #826 (duplicate nested tables) and orphaned `<tr>`/`<td>` fragments. See `documents-parsing.md` → `section_slicer` section.
