## Documents — HTML Model & Parsing

### Overview

`edgar/documents` (v2.0.0) is the modern, high-performance HTML parsing subsystem for SEC filings. It ingests raw HTML/XHTML, builds a typed node tree, detects document sections (10-K, 10-Q, 8-K, 20-F), extracts tables with DataFrame export, provides multi-mode search with BM25 ranking, and exposes a `Document` object consumed by all form-specific report classes. It replaces the legacy `edgar.files.html.SECHTMLParser` and is the canonical parsing path for the library.

---

### Public API surface

| Symbol | file:line | Purpose |
|---|---|---|
| `parse_html(html, config)` | `__init__.py:47` | Module-level convenience: `HTMLParser(config).parse(html)` |
| `HTMLParser` | `parser.py:24` | Main parser orchestrator — accepts HTML/bytes, returns `Document` |
| `Document` | `document.py:599` | Root parsed-document object |
| `ParserConfig` | `config.py:31` | All parser tunables with defaults |
| `ParserConfig.for_performance()` | `config.py:161` | Factory: speed-optimized config |
| `ParserConfig.for_accuracy()` | `config.py:177` | Factory: accuracy-optimized config |
| `ParserConfig.for_ai()` | `config.py:198` | Factory: LLM/AI-optimized config |
| `DocumentSearch` | `search.py:52` | All search modes + BM25 ranked search |
| `SearchResult` (search.py) | `search.py:31` | Raw node + offset result from `search()` |
| `SearchResult` (types.py) | `types.py:199` | Rich result with section context from `ranked_search()` |
| `SearchMode` | `search.py:22` | Enum: TEXT, REGEX, SEMANTIC, XPATH |
| `NodeType` | `types.py:11` | Enum of all node kinds in the tree |
| `SemanticType` | `types.py:27` | Enum of semantic roles |
| `TableType` | `types.py:42` | Enum: FINANCIAL, METRICS, REFERENCE, GENERAL, TABLE_OF_CONTENTS, EXHIBIT_INDEX |
| `CrossReferenceIndex` | `cross_reference_index.py:113` | Parses GE/Citigroup-style cross-reference index tables |
| `IndexEntry` | `cross_reference_index.py:95` | One item in a cross-ref index (item num, title, page ranges) |
| `PageRange` | `cross_reference_index.py:19` | Start/end page pair |
| `detect_cross_reference_index(html)` | `cross_reference_index.py:377` | Convenience: detect cross-ref index presence |
| `parse_cross_reference_index(html)` | `cross_reference_index.py:391` | Convenience: parse and return `{item_id: IndexEntry}` |
| `MarkdownRenderer`, `TextRenderer` | `renderers/` | Convert `Document` to Markdown or plain text |
| `ParsingError` | `exceptions.py:8` | Base parsing exception |

---

### Key classes

#### `HTMLParser` — `parser.py:24`
Orchestrates the full parsing pipeline. Initialized with `ParserConfig`.

- `__init__(config)` — validates config, creates `HTMLPreprocessor`, `DocumentPostprocessor`, initializes strategies (header detection, table processing, XBRL extraction) — `parser.py:32`
- `parse(html: str|bytes) -> Document` — main entry point; size-checks, preprocesses, lxml-parses, builds `DocumentNode` tree, postprocesses, records timing — `parser.py:80`
- `_parse_streaming(html)` — delegates to `StreamingParser` when `doc_size > streaming_threshold` — `parser.py:270`
- `_extract_xbrl_pre_process(html)` — extracts XBRL facts **before** preprocessing to capture `ix:hidden` content — `parser.py:277`
- `parse_file(file_path) -> Document` — reads file, calls `parse()` — `parser.py:331`
- `parse_url(url) -> Document` — fetches via `requests`, calls `parse()` — `parser.py:349`
- `create_for_performance()` / `create_for_accuracy()` / `create_for_ai()` — class-method factories — `parser.py:369-385`

#### `Document` — `document.py:599`
The root result object. A `@dataclass` with `root: Node` + `metadata: DocumentMetadata`.

- `sections -> Sections` — lazy, triggers `HybridSectionDetector` for 10-K/10-Q/8-K/20-F, falls back to `PatternSectionExtractor`; result cached in `_sections` — `document.py:620`
- `tables -> List[TableNode]` — lazy; walks `root.find(isinstance TableNode)`, cached in `_tables` — `document.py:663`
- `headings -> List[Node]` — lazy; cached in `_headings` — `document.py:670`
- `xbrl_facts -> List[XBRLFact]` — lazy; scans nodes for `ix_tag` metadata — `document.py:678`
- `text(clean, include_tables, include_metadata, max_length, table_max_col_width) -> str` — delegates to `TextExtractor`, applies navigation/TOC link filtering, caches simple call — `document.py:685`
- `search(query, top_k=10)` — quick wrapper over `DocumentSearch.search()` — `document.py:745`
- `get_section(section_name, part=None) -> Section|None` — name-based or part+item lookup, raises `ValueError` for ambiguous 10-Q items — `document.py:760`
- `get_sec_section(section_name, clean, include_subsections) -> str|None` — anchor-based extraction via `SECSectionExtractor` — `document.py:818`
- `get_available_sec_sections()` — lists extractable sections — `document.py:845`
- `to_markdown()` — `MarkdownRenderer().render(self)` — `document.py:879`
- `to_json(include_content) -> dict` — structure + content as dict — `document.py:885`
- `to_dataframe() -> pd.DataFrame` — concatenates all tables with `_table_index`, `_table_type` columns — `document.py:924`
- `chunks(chunk_size=512, overlap=128)` — yields `DocumentChunk` via `ChunkExtractor` — `document.py:949`
- `prepare_for_llm(max_tokens, preserve_structure, focus_sections)` — `LLMOptimizer().optimize()` — `document.py:964`
- `extract_key_information()` — summary dict: company, form, sections list, table counts — `document.py:988`
- `validate()` — returns list of structural issues — `document.py:1061`
- `walk()`, `find_nodes(pred)`, `find_first_node(pred)` — tree traversal delegates — `document.py:1034-1044`

#### `DocumentMetadata` — `document.py:29`
Dataclass: `source`, `form`, `company`, `cik`, `accession_number`, `filing_date`, `report_date`, `url`, `size`, `parse_time`, `parser_version`, `xbrl_data`, `preserve_whitespace`, `original_html` (stored for anchor analysis).

#### `Section` — `document.py:69`
One detected filing section.

- Fields: `name`, `title`, `node: SectionNode`, `start_offset`, `end_offset`, `confidence`, `detection_method`, `validated`, `part`, `item`, `warnings: list`, `_text_extractor`, `_html_source`, `_section_extractor`
- `text(**kwargs) -> str` — uses `_text_extractor` callback if TOC-based, else `TextExtractor.extract_from_node()`; cleans boundary artifacts (page numbers, next-section bleeds) — `document.py:104`
- `markdown() -> str` — renders section to Markdown preserving table/list structure. For TOC sections: slices HTML via `section_slicer`, re-parses, renders with `MarkdownRenderer`. Falls back to `text()` if slice fails — `document.py:119`
- `tables() -> List[TableNode]` — for TOC sections, parses section HTML directly via `TableProcessor` (uses `section_slicer` for clean anchor-bounded slicing); for heading/pattern sections, walks node tree — `document.py:182`
- `search(query) -> List[SearchResult]` — simple substring search returning `SearchResult` — `document.py:300`
- `parse_section_name(section_name) -> (part, item)` — static; parses "part_i_item_1", "Item 1A", "Part II Item 9A" etc. — `document.py:324`
- `warnings: list` — extraction warnings attached by size-band guardrail; non-empty means content length was anomalous (too short = anchor pointed at heading; too long = boundary overshot adjacent item)

#### `Sections` — `document.py:378`
`Dict[str, Section]` subclass with rich display and flexible access.

- `get_item(item, part=None) -> Section|None` — access by "1A", "Item 1A" with optional part — `document.py:469`
- `get_part(part) -> Dict[str, Section]` — all sections in a part — `document.py:507`
- `get(key, default=None)` — overridden; tries dict key, then `get_item()`, then tuple `(part, item)` — `document.py:531`
- `__getitem__(key)` — same flexibility + raises `KeyError` — `document.py:567`
- `__rich__()` — renders terminal table sorted by part/item with confidence, detection method, part/item columns — `document.py:386`

---

### New modules (parser rework)

#### `FormSchema` / `TextItemRule` — `edgar/documents/form_schema.py`

Declarative per-form TOC schema replacing scattered `if self.form in (...)` branches in `TOCAnalyzer`. Adding a form = adding a table entry, not editing conditionals.

| Symbol | Purpose |
|--------|---------|
| `FormSchema` | Frozen dataclass: `max_bare_item`, `text_rules`, `skip_unmatched_text`, `item_part_ranges`, `repeating_parts` |
| `TextItemRule` | Single keyword→item mapping rule: `required` (all must match), `excluded` (none may match) |
| `TEN_K_SCHEMA` | 10-K: items unique across parts; `item_part_ranges` enables part inference from item number |
| `TEN_Q_SCHEMA` | 10-Q: items repeat across parts; `repeating_parts=("I","II")` seeds TOC walk with Part I |
| `DEFAULT_SCHEMA` | 20-F, 40-F, S-1 etc.: no text rules, raw text returned |
| `get_form_schema(form)` | Resolves form string → `FormSchema`; `None` defaults to 10-K schema |

- `FormSchema.match_text(text_lower, use_exclusions)` — first matching `TextItemRule` wins; `use_exclusions=False` used for sort-order lookup only (preserves historical inconsistency intentionally)
- `FormSchema.part_for_item(item_name)` — infers canonical Part from item number via `item_part_ranges`; returns `None` for 10-Q (items repeat, must detect)
- `FormSchema.seed_part` — Part to start TOC walk from before any Part header is encountered; `"Part I"` for 10-Q, `None` for 10-K

#### `section_size_bands` — `edgar/documents/section_size_bands.py`

Content-size guardrail that flags silent wrong-content failures (anomalous section length → degraded confidence).

| Symbol | Purpose |
|--------|---------|
| `SIZE_BANDS` | `Dict[form, Dict[item_key, {low, high}]]` — enforced items only (10-K: 1,1A,1C,7,8,9A,16; 10-Q: 1,2,6) |
| `ANOMALOUS_CONFIDENCE` | Confidence assigned to anomalous sections (below 0.95 so callers detect degradation) |
| `band_for(form, item_key)` | Returns band dict or `None` if item not enforced |
| `evaluate_size(form, item_key, length)` | Returns human-readable warning string if outside band, `None` if OK; `length <= 0` never flagged |

- Bands are intentionally generous (median/5 .. median×8) — flags gross anomalies only, not normal variation
- Bands tuned to large-cap filers; Item 8 enforceable only for filers that inline financial statements
- Warning string is stored in `Section.warnings`; caller checks `section.warnings` to detect extraction issues
- Size `0` = treated as "unknown" (missing section is handled upstream), not anomalous

#### `section_slicer` — `edgar/documents/utils/section_slicer.py`

Anchor-to-anchor HTML slicing primitive shared by `Section.tables()`, `Section.markdown()`, and 40-F extraction. Centralizes the algorithm previously re-derived (with different bugs) per feature.

| Symbol | Purpose |
|--------|---------|
| `extract_section_html(tree, start_anchor, end_anchor)` | Public entry: returns well-formed `<div>` HTML string for the section, `""` on failure |
| `build_section_subtree(tree, start, end)` | Returns detached lxml `<div>` element; `None` if anchor unresolvable or range empty |
| `collect_range_elements(tree, start, end)` | Raw document-order element list between anchors |
| `top_level_elements(collected)` | Reduces list to elements whose parent is not also collected (prevents nested-table duplication, GH #826 fix) |

- Step 3 (top-level-only) fixes issue #826: serializing a nested table's ancestor already emits the descendant; collecting both duplicated tables
- Step 4 repairs orphaned `<tr>`/`<td>`/`<tbody>` fragments that lxml would silently drop outside a `<table>` context
- `_clone()` uses `copy.deepcopy` not serialize/re-parse — preserves HTML void elements (`<br>`, `<img>`) that XML parser rejects

---

### Node type hierarchy

```
Node (ABC, dataclass)                     nodes.py:16
  ├── DocumentNode (+ CacheableMixin)     nodes.py:144  — tree root, text joins children with \n\n
  ├── TextNode                            nodes.py:175  — leaf, plain string content
  ├── ParagraphNode (+ CacheableMixin)    nodes.py:196  — smart spacing between inline children
  ├── HeadingNode                         nodes.py:295  — level:int (1-6)
  ├── ContainerNode (+ CacheableMixin)    nodes.py:332  — generic div/section, tag_name attr
  │     └── SectionNode                  nodes.py:375  — section_name attr, tag_name='section'
  ├── ListNode                            nodes.py:387  — ordered:bool
  ├── ListItemNode                        nodes.py:413
  ├── LinkNode                            nodes.py:432  — href, title
  └── ImageNode                          nodes.py:459  — src, alt, width, height

table_nodes.py (separate file):
  TableNode (Node + CacheableMixin)       table_nodes.py:141
  Cell (dataclass)                        table_nodes.py:34
  Row (dataclass)                         table_nodes.py:95
```

`NodeType` enum values: DOCUMENT, SECTION, HEADING, PARAGRAPH, TABLE, LIST, LIST_ITEM, LINK, IMAGE, XBRL_FACT, TEXT, CONTAINER.

All nodes share: `id` (UUID), `type`, `parent`, `children`, `content`, `metadata: dict`, `style: Style`, `semantic_type`, `semantic_role`.

Tree traversal on `Node`: `find(pred)`, `find_first(pred)`, `walk()` (depth-first), `xpath(expr)` (subset of XPath), `depth` property, `path` property.

---

### TableNode & table structures — `table_nodes.py`

#### `Cell` — `table_nodes.py:34`
- `content: str|Node`, `colspan`, `rowspan`, `is_header`, `align`
- `text()` — unwraps str or calls `Node.text()`
- `is_numeric` — handles `—`, `–`, `-`, `--`, `N/A`, `NM` as `True` (returns 0.0)
- `numeric_value -> float|None` — strips `$`, `,`, `%`, converts `(x)` → `-x`

#### `Row` — `table_nodes.py:95`
- `cells: List[Cell]`, `is_header: bool`
- `is_numeric_row` — >50% cells numeric
- `is_total_row` — first cell starts with "total", "sum", "subtotal", "grand total"

#### `TableNode` — `table_nodes.py:141`
- Structural fields: `headers: List[List[Cell]]` (multi-level), `rows: List[Row]`, `footer: List[Row]`, `table_type: TableType`
- Meta: `caption`, `summary`
- `text() -> str` — uses `fast_table_rendering` (from `_config`) for `FastTableRenderer(TableStyle.simple())`, else Rich `box.SIMPLE` rendering; result cached via `CacheableMixin`
- `render(width) -> RichTable` — builds `TableMatrix`, removes spacing columns, merges currency symbol columns, auto-detects alignments, merges multi-row headers with `\n`, calculates smart column widths
- `to_dataframe() -> pd.DataFrame` — full colspan/rowspan expansion via `TableMatrix`; currency cells kept as strings; numeric cells converted to `float`; `MultiIndex` for multi-row headers; sets `df.index` when `has_row_headers` is True
- `to_csv()` — delegates to `to_dataframe().to_csv()`
- `to_dict()` — headers/data/footer as `List[List[str]]`
- `find_column(header_text) -> int|None` — searches first header row
- `extract_column(col_idx) -> List[str]`
- `find_row_by_first_cell(text) -> Row|None`
- `get_numeric_columns() -> Dict[str, List[float]]` — cols where >50% data rows are numeric
- `find_totals() -> Dict[str, float]` — rows matching `is_total_row`
- `is_financial_table` — `TableType.FINANCIAL` or header text contains financial keywords
- `row_count`, `col_count`, `has_header`, `has_row_headers` (first col <20% numeric), `numeric_columns`
- `summarize_for_llm(max_tokens=500) -> str` — compact description of type, size, headers, totals

**Table matrix pipeline** (`table_utils.py:15`):
1. `matrix.build_from_rows(headers, rows)` — expand colspan/rowspan
2. `matrix.filter_spacing_columns()` — remove whitespace-only columns
3. `CurrencyColumnMerger.detect_currency_pairs()` + `apply_merges()` — merge `$` symbol columns into adjacent value columns

---

### Configuration & options

#### `ParserConfig` — `config.py:31`

| Option | Type | Default | Effect |
|---|---|---|---|
| `max_document_size` | int | 160MB | Max bytes before `DocumentTooLargeError` |
| `streaming_threshold` | int | 10MB | Size above which streaming parser is used |
| `cache_size` | int | 1000 | Max cached items |
| `enable_parallel` | bool | True | Parallel table processing |
| `max_workers` | int\|None | None | Thread pool size (None = CPU count) |
| `strict_mode` | bool | False | Fail on error vs. best-effort |
| `extract_xbrl` | bool | True | Extract inline XBRL facts |
| `extract_styles` | bool | True | Parse CSS styles into `Style` objects |
| `preserve_whitespace` | bool | False | Preserve original whitespace |
| `normalize_text` | bool | True | Normalize whitespace |
| `extract_links` | bool | True | Parse `<a>` as `LinkNode` |
| `extract_images` | bool | False | Parse `<img>` as `ImageNode` |
| `optimize_for_ai` | bool | True | AI-specific optimizations |
| `max_token_estimation` | int | 100000 | Token budget for AI mode |
| `chunk_size` | int | 512 | Chunk target tokens |
| `chunk_overlap` | int | 128 | Overlap between chunks |
| `table_extraction` | bool | True | Parse `<table>` elements |
| `detect_table_types` | bool | True | Classify table semantic type |
| `extract_table_relationships` | bool | True | Cross-table relationships |
| `fast_table_rendering` | bool | True | Use `FastTableRenderer` (7-10x faster) |
| `detect_sections` | bool | True | Run section detection |
| `eager_section_extraction` | bool | False | Extract during parse vs. lazy on first access |
| `form` | str\|None | None | Filing type for section detection (e.g. '10-K') |
| `detection_thresholds` | `DetectionThresholds` | defaults | Per-strategy confidence thresholds |
| `header_detection_threshold` | float | 0.6 | Min confidence for header detection |
| `header_detection_methods` | list | `['style','pattern','structural','contextual']` | Detection methods to apply |
| `min_text_length` | int | 10 | Minimum text length to keep |
| `merge_adjacent_nodes` | bool | True | Merge adjacent similar nodes |
| `merge_distance` | int | 2 | Max gap between nodes to merge |
| `enable_profiling` | bool | False | Performance profiling |
| `features` | dict | all True | Feature flags (ml_header_detection, semantic_analysis, table_understanding, xbrl_validation, auto_section_detection, smart_text_extraction, footnote_linking, cross_reference_resolution) |

#### `DetectionThresholds` — `config.py:10`

| Option | Default |
|---|---|
| `min_confidence` | 0.6 |
| `cross_validation_boost` | 1.2 |
| `disagreement_penalty` | 0.8 |
| `boundary_overlap_penalty` | 0.9 |
| `enable_cross_validation` | False |

---

### Data flow / lifecycle

- `HTMLParser.parse(html)`:
  1. Size check → `DocumentTooLargeError` if exceeded; streaming if `> streaming_threshold`
  2. Store `original_html` (needed for TOC anchor analysis)
  3. `_extract_xbrl_pre_process(html)` — XBRL extraction **before** preprocessing to capture `ix:hidden`
  4. `HTMLPreprocessor.process(html)` — cleans HTML for rendering
  5. `lxml.html.fromstring()` → `HtmlElement` tree
  6. `_extract_metadata()` — from `<meta>` tags, `<title>`, and heuristic form-type detection; `config.form` takes precedence
  7. `DocumentBuilder.build(tree)` → `DocumentNode` tree — traverses lxml tree, creates typed nodes, processes tables via `TableProcessor`, detects headers via `HeaderDetectionStrategy`
  8. `Document(root=root_node, metadata=metadata)` created; `document._config = self.config`
  9. `DocumentPostprocessor.process(document)` — merges adjacent nodes if `merge_adjacent_nodes`
  10. Timing recorded in `metadata.parse_time`

- `Document.sections` (lazy):
  - If `form in ['10-K','10-Q','8-K','20-F']` → `HybridSectionDetector` (tries TOC 0.95, heading 0.7-0.9, pattern 0.6 in order)
  - Otherwise → `PatternSectionExtractor`
  - Wrapped in `Sections` dict subclass
  - `Section._text_extractor` callback is set for TOC-based sections; `Section.node.children` is empty for these — `tables()` re-parses HTML directly

- `Document.tables` (lazy): single `root.find(isinstance TableNode)` walk, cached.

- `Document.text()`: `TextExtractor.extract(self)` → navigation link filtering via `anchor_cache.filter_with_cached_patterns()` (falls back to `toc_filter.filter_toc_links()`); simple-call result cached in `_text_cache`.

- `Section.text()` boundary cleaning: strips interior page headers (PART + Item mid-document), trailing PART+Item footers, trailing lone Item headers, trailing page numbers.

- `TableNode.to_dataframe()`: `TableMatrix.build_from_rows()` → `filter_spacing_columns()` → `CurrencyColumnMerger` → `pd.DataFrame`; single-level or `MultiIndex` columns; first column becomes index if `has_row_headers`.

---

### Design patterns

- **Strategy pattern** — `HTMLParser._init_strategies()` builds a dict of pluggable strategies (`HeaderDetectionStrategy`, `TableProcessor`, `XBRLExtractor`); `DocumentBuilder` receives the dict.
- **Mixin caching** — `CacheableMixin` provides `_get_cached_text(generator_func)` and recursive `clear_text_cache()`; used by `DocumentNode`, `ParagraphNode`, `ContainerNode`, `TableNode`, `Document`.
- **Lazy evaluation** — all `Document` properties (`sections`, `tables`, `headings`, `xbrl_facts`, `_text_cache`) are computed on first access.
- **Factory class methods** — `ParserConfig.for_performance()`, `for_accuracy()`, `for_ai()`; `HTMLParser.create_for_performance()` etc. for preconfigured instances.
- **Compatibility layer** — `migration.py` provides `LegacyHTMLDocument` and `LegacySECHTMLParser` wrapping new parser with `DeprecationWarning`; `migrate_parser_usage(code)` does string replacement migration; aliases `SECHTMLParser = LegacySECHTMLParser`.
- **Protocol-based duck typing** — `NodeProtocol` in `types.py:102` defines the structural interface; concrete nodes are dataclasses, not Protocol implementors.
- **Two-tier search results** — `search.SearchResult` (raw node + offset) vs. `types.SearchResult` (node + score + snippet + section + `_section_obj` for agent navigation). The latter's `full_context` returns the entire `Section.text()` rather than a fragment.

---

### DocumentSearch API — `search.py:52`

```
DocumentSearch(document, use_cache=True)
  .search(query, mode=TEXT, case_sensitive=False, whole_word=False,
          limit=None, node_types=None, in_section=None) -> List[search.SearchResult]
  .ranked_search(query, algorithm="hybrid", top_k=10, node_types=None,
                 in_section=None, boost_sections=None) -> List[types.SearchResult]
  .find_tables(caption_pattern=None, min_rows=None, min_cols=None) -> List[TableNode]
  .find_headings(level=None, pattern=None) -> List[HeadingNode]
  .get_cache_stats() -> dict
  .clear_cache(memory_only=False)
```

**Search modes**: TEXT (substring, leaf-nodes only to avoid duplicates), REGEX (compiled `re.compile`), SEMANTIC (":"-delimited type prefix: `heading:`, `table:`, `section:`), XPATH (tag + `[@attr=val]` or `[contains(text(),'x')]` or level filter).

**Ranked search** (`ranked_search`): uses `rank_bm25.BM25Okapi`. Three algorithms:
- `BM25Engine` — pure BM25Okapi
- `HybridEngine` — BM25 + semantic structure boosting (`boost_sections` list)
- `SemanticEngine` — pure structure-aware scoring

Index caching: per-`DocumentSearch` instance dict `_ranking_engines`; global `SearchIndexCache` (memory LRU + disk pickle at `~/.edgar_cache/search/`, TTL=24h).

---

### CrossReferenceIndex — `cross_reference_index.py`

Handles a non-standard 10-K format where GE, Citigroup, and others use a `FORM 10-K CROSS-REFERENCE INDEX` table instead of section headings.

- `has_index()` — regex scan for heading + table pattern with `1A / Risk Factors / page#` cells
- `parse() -> Dict[str, IndexEntry]` — finds table (handles heading-inside-table vs. heading-before-table layouts); parses rows for Part headers, item rows, continuation page rows; returns `{item_id: IndexEntry}`
- `get_item(item_id)`, `get_page_ranges(item_id)` — lookup
- `find_page_breaks()` — locates `page-break-after:always` HR/DIV elements as page 1-indexed positions
- `extract_content_by_page_range(PageRange)` — slices raw HTML between page-break positions
- `extract_item_content(item_id)` — convenience: page ranges → concatenated HTML

`PageRange.parse(page_str)` — handles ranges like `"4-7, 9-11, 74-75"`, en-dash HTML entities, footnote `(a)` suffixes, single pages, `"not applicable"`.

---

### Filing agent detection — `agents.py`

`detect_filing_agent(html_content) -> str|None` — scans first 3000 chars for agent signatures.

Recognized agents: Workiva (~35%), Donnelley/DFIN (~26%), Toppan Merrill (~11%), Novaworks/ThunderDome (~9%), CompSci (~3%), Certent (~2%), Broadridge, EDGARsuite, SEC Publisher.

Used by `Filing.agent` cached property (`_filings.py:1576`) and internally by TOC section extraction strategies to select agent-specific parsing logic.

---

### Migration — `migration.py`

| Old | New |
|---|---|
| `from edgar.files.html import SECHTMLParser` | `from edgar.documents import HTMLParser` |
| `parser = SECHTMLParser(config_dict)` | `parser = HTMLParser(ParserConfig(...))` |
| `document.text` (property) | `document.text()` (method) |
| `document.find_all('table')` | `document.root.find(lambda n: n.type == NodeType.TABLE)` |
| `document.to_markdown()` | `MarkdownRenderer().render(document)` |
| `config['extract_tables']` | `ParserConfig(table_extraction=...)` |
| `config['preserve_layout']` | `ParserConfig(preserve_whitespace=...)` |

`LegacySECHTMLParser` / `LegacyHTMLDocument` issue `DeprecationWarning` on use. `migrate_parser_usage(code: str) -> str` does string-level code migration.

---

### Class hierarchy

```
CacheableMixin (cache_mixin.py)
  └── mixed into: DocumentNode, ParagraphNode, ContainerNode, TableNode, Document

Node (ABC, dataclass) (nodes.py)
  ├── DocumentNode(Node, CacheableMixin)
  ├── TextNode(Node)
  ├── ParagraphNode(Node, CacheableMixin)
  ├── HeadingNode(Node)
  ├── ContainerNode(Node, CacheableMixin)
  │     └── SectionNode(ContainerNode)
  ├── ListNode(Node)
  ├── ListItemNode(Node)
  ├── LinkNode(Node)
  └── ImageNode(Node)

TableNode(Node, CacheableMixin) (table_nodes.py)
  Cell (standalone dataclass)
  Row (standalone dataclass)

Document (@dataclass) (document.py)
  root: Node
  metadata: DocumentMetadata
  _sections: Sections (lazy)
  _tables: List[TableNode] (lazy)

Sections(Dict[str, Section]) (document.py)
Section (@dataclass) (document.py)

RankingEngine (ABC) (ranking/ranking.py)
  ├── BM25Engine
  ├── HybridEngine
  └── SemanticEngine
```

---

### Cross-domain interactions

**Imports from other `edgar.*` modules:**
- `edgar.richtools` — `repr_rich`, `rich_to_text` (used in `table_nodes.py`, `document.py`)
- `edgar.paths` — `get_search_cache_directory()` (ranking/cache.py)

**Consumed by:**
- `edgar._filings.Filing.agent` — uses `agents.detect_filing_agent`
- `edgar.company_reports.ten_k.TenK.document` — `HTMLParser(ParserConfig(form='10-K')).parse(html)`
- `edgar.company_reports.ten_q.TenQ.document` — same pattern with `form='10-Q'`
- `edgar.company_reports.current_report.CurrentReport.document` — `form='8-K'`
- `edgar.company_reports.twenty_f.TwentyF.document` — `form='20-F'`
- `edgar.company_reports._base` — base class imports `Document`, `HTMLParser`
- `edgar.earnings` — `parse_html(html_content)` convenience function
- `edgar.offerings.prospectus` — imports `Sections`
- `edgar.offerings._424b_tables` — imports `TableNode`

---

### Gotchas & notable behaviors

- **XBRL must be extracted before preprocessing** — `HTMLPreprocessor` removes `ix:hidden` elements; XBRL extraction runs first on the raw HTML.
- **`original_html` stored on metadata** — needed for TOC-based section extraction which re-parses HTML with anchor analysis. `Section._text_extractor` / `_html_source` / `_section_extractor` are all lazy callbacks stored at parse time.
- **TOC sections have empty `node.children`** — `Section.tables()` detects `detection_method == 'toc'` and re-parses the section HTML directly via `TableProcessor` rather than walking the node tree.
- **Section detection is form-type-gated** — only `10-K`, `10-Q`, `8-K`, `20-F` (and their `/A` amendments) trigger `HybridSectionDetector`; everything else uses `PatternSectionExtractor`.
- **Sections dict flexible access** — `sections["item_1a"]`, `sections["1A"]`, `sections[("I","1")]` all work; ambiguous 10-Q item access without `part=` raises `ValueError` instead of returning `None`.
- **`Document.text()` cache is parameter-sensitive** — only caches when called with default params (`clean=True, include_tables=False, include_metadata=False, max_length=None`).
- **`preserve_whitespace` on metadata disables cleaning** — if `metadata.preserve_whitespace` is set during parse, calling `text(clean=True)` silently switches to `clean=False`.
- **Currency column merging** — `$` symbol columns are detected and merged with adjacent numeric columns during both `render()` and `to_dataframe()` to align financial numbers correctly.
- **`is_numeric` treats `—`, `–`, `N/A`, `NM` as 0.0** — these financial placeholders pass `is_numeric=True` and return `numeric_value=0.0`.
- **BM25 search only caches for `algorithm="bm25"`** — `HybridEngine` and `SemanticEngine` are instance-cached but not persisted to disk.
- **`CrossReferenceIndex` handles two table layouts** — GE style (heading inside table) vs. Citigroup style (heading before table); detects by checking if `<table` is open before the heading position.
- **Document size limit is 160MB** — specifically to handle large NPORT-P filings.
- **`fast_table_rendering=True` by default** — `FastTableRenderer` is 7-10x faster than Rich for text output; configurable to Rich for edge cases.
- **Section boundary artifact cleaning** — `Section._clean_boundary_artifacts()` removes page number + PART header + Item number patterns that appear as interior or trailing artifacts from PDF-to-HTML conversion.
- **`__repr__` renders full text** — `Document.__repr__()` calls `self.text(table_max_col_width=200)`, so printing a document in a REPL produces the full rendered text.
- **`Section.markdown()` falls back to `text()`** — If the section slicer yields an empty result (start anchor unresolvable, or range empty), `markdown()` returns plain text rather than an empty string. Never regresses vs. prior behavior.
- **`Section.warnings` signals extraction anomalies** — Non-empty `warnings` on a section at `confidence=0.95` means the size guardrail fired; the content may be truncated (anchor at heading) or over-captured (boundary overshot). Check before trusting the text.
- **`FormSchema.seed_part` solves 10-Q Part I / Part II collision** — Without seeding, TOC items before the first Part header collapse to bare `item_N` keys which downstream resolves to Part II. The seed preemptively assigns Part I so `part_i_item_1` (Financial Statements) and `part_ii_item_1` (Legal Proceedings) are distinct from the start.
- **StreamingParser `_content_depth` gate** — Structural elements (`p`, `h1–h6`, `section`) increment `_content_depth` at start and decrement at end. `elem.clear()` is suppressed while `_content_depth > 0` because `_end_paragraph` / `_end_heading` read the full subtree via `_get_text_content`; clearing before the end event wipes `.text` and `.tail` and produces empty text silently. This is symmetric to the existing `_table_depth` gate.
