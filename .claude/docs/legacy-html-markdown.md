## Legacy HTML Files & Markdown

### Overview

This domain is the **deprecated/fallback HTML parsing subsystem** in `edgar/files/`. It provides BeautifulSoup-based HTML-to-node parsing (`SECHTMLParser`/`Document`), block-based chunking (`HtmlDocument`/`ChunkedDocument`), page-break detection, style/heading inference, table processing, and two distinct HTML-to-markdown conversion paths. Company reports (`TenK`, `TenQ`, `EightK`) still use `ChunkedDocument` as the primary or fallback path for the `list_items()` / item-retrieval API. The newer `edgar/documents/` subsystem (`HTMLParser`) is the replacement target for v6.0. `DeprecationWarning` is deferred to class instantiation time (not import time) via `edgar/files/_deprecation.py` and is suppressed for internal edgartools callers.

---

### Public API surface

| Symbol | file:line | Purpose |
|---|---|---|
| `SECHTMLParser` | `edgar/files/html.py:564` | Parses raw HTML into `Document` node tree |
| `Document` | `edgar/files/html.py:500` | Node-list container; `.parse()`, `.to_markdown()`, `.tables`, `.headings` |
| `DocumentNode` | `edgar/files/html.py:469` | Legacy dataclass node (heading/text_block/table) |
| `HtmlDocument` | `edgar/files/html_documents.py:343` | Block-based legacy document; `.from_html()`, `.text`, `.markdown`, `.generate_chunks()` |
| `ChunkedDocument` | `edgar/files/htmltools.py:334` | Chunks HTML by item/part; `.list_items()`, `[item]`, `.chunks_for_item()` |
| `DocumentData` | `edgar/files/html_documents.py:64` | Inline XBRL header parser; `.parse_header()`, `.parse_inline_data()` |
| `detect_page_breaks` | `edgar/files/page_breaks.py:154` | Public function — returns list of page break dicts from HTML string |
| `mark_page_breaks` | `edgar/files/page_breaks.py:229` | Returns HTML string with `_is_page_break` attributes stamped |
| `PageBreakDetector` | `edgar/files/page_breaks.py:14` | Class with `.mark_page_breaks()`, `._is_page_like_div()` |
| `to_markdown` | `edgar/files/markdown.py:184` | HTML string → markdown string via `Document.parse()` + `MarkdownRenderer` |
| `MarkdownRenderer` | `edgar/files/markdown.py:10` | Renders `Document` to markdown string |
| `process_content` | `edgar/markdown.py:1128` | HTML → LLM-optimized markdown (used by notes/statements) |
| `html_to_json` | `edgar/markdown.py:618` | HTML table → intermediate JSON records for markdown generation |
| `list_of_dicts_to_table` | `edgar/markdown.py:908` | Converts JSON records to GFM markdown table |
| `create_markdown_table` | `edgar/markdown.py:867` | Low-level: builds markdown table from headers + rows lists |
| `html_to_markdown` | `edgar/_markdown.py:92` | Wrapper: `HtmlDocument.from_html(html).markdown` |
| `MarkdownContent` | `edgar/_markdown.py:105` | Container wrapping markdown string with `.view()` rich console output |
| `chunks2df` | `edgar/files/htmltools.py:270` | Chunks list → DataFrame with Item/Part/Toc/Signature columns |
| `decimal_chunk_fn` | `edgar/files/htmltools.py:329` | Partial of `chunks2df` for decimal item patterns (8-K: "1.02") |
| `html_sections` | `edgar/files/htmltools.py:67` | Splits HTML into text sections via `HtmlDocument.generate_text_chunks()` |
| `AssembleText` | `edgar/files/html_documents_id_parser.py:17` | Assembles item text from anchor IDs in HTML |
| `ParsedHtml10K` | `edgar/files/html_documents_id_parser.py:196` | Extracts 10-K items via TOC link anchors |
| `ParsedHtml10Q` | `edgar/files/html_documents_id_parser.py:509` | Extracts 10-Q items via TOC link anchors (part-aware) |
| `PlainDocument`, `XmlDocument`, `JsonDocument` | `edgar/files/text.py:12,57,73` | Simple wrappers for non-HTML content types |

`detect_page_breaks` and `mark_page_breaks` are re-exported at `edgar/__init__.py:44` as top-level public API. `Document` is re-exported at `edgar/__init__.py:45`.

---

### Key classes

**`SECHTMLParser`** — Stateful parser that walks a BeautifulSoup tree and emits `BaseNode` objects.

- `__init__(root, extract_data, include_page_breaks)` — `edgar/files/html.py:565`
- `parse() -> Optional[Document]` — entry point; finds body, optionally marks page breaks, calls `_parse_element`, returns `Document(nodes=...)` — `edgar/files/html.py:574`
- `_process_element(element) -> Optional[Union[BaseNode, List[BaseNode]]]` — central dispatch; checks page-break marker, marks table ancestor divs with `has_table`, merges styles, dispatches to specialized handlers — `edgar/files/html.py:1019`
- `_process_table(element) -> Optional[BaseNode]` — builds `TableNode` with `TableRow`/`TableCell` objects; handles colspan expansion, nested tables, entity replacement — `edgar/files/html.py:1238`
- `_process_paragraph(element, style) -> Optional[BaseNode]` — walks children, collects text parts, returns `text_block` node — `edgar/files/html.py:1408`
- `_process_structured_content(element, style)` — structure-preserving mode for divs containing tables — `edgar/files/html.py:1081`
- `_process_inline_content(element, style)` — content-combining mode for divs without tables — `edgar/files/html.py:1126`
- `_merge_adjacent_nodes(nodes) -> List[BaseNode]` — merges compatible consecutive `text_block` nodes — `edgar/files/html.py:1633`
- `_handle_page_break_element(element)` — emits `PageBreakNode`, then processes contained content — `edgar/files/html.py:825`

**`Document`** — Thin container around `List[BaseNode]`.

- `parse(html, include_page_breaks) -> Optional[Document]` — classmethod; calls `HtmlDocument.get_root()` then `SECHTMLParser(root).parse()` — `edgar/files/html.py:529`
- `to_markdown(start_page_number) -> str` — delegates to `MarkdownRenderer(self).render()` — `edgar/files/html.py:535`
- `tables`, `headings` — filtered views of `self.nodes` by type — `edgar/files/html.py:519,525`

**`HtmlDocument`** — Block-based older document.

- `from_html(html, extract_data) -> Optional[HtmlDocument]` — classmethod; calls `get_root()`, `extract_data()`, `clean_html_root()`, `extract_text()` — `edgar/files/html_documents.py:470`
- `get_root(html) -> Tag` — strips `<DOCUMENT><TEXT>` wrapper if present, parses with lxml, runs `fixup_soup()` — `edgar/files/html_documents.py:459`
- `extract_text(start_element) -> List[Block]` — removes page numbers, calls `extract_and_format_content()`, compresses blocks — `edgar/files/html_documents.py:436`
- `generate_chunks(ignore_tables) -> Generator[List[Block], None, None]` — yields `List[Block]` segments; splits on Item/Part headers and table boundaries — `edgar/files/html_documents.py:499`
- `generate_text_chunks(ignore_tables) -> Generator[str, None, None]` — text version of `generate_chunks` — `edgar/files/html_documents.py:495`
- `.text` — concatenates all block `.get_text()` — `edgar/files/html_documents.py:354`
- `.markdown` — concatenates all block `.to_markdown()` with `is_header()` spacing — `edgar/files/html_documents.py:363`

**`ChunkedDocument`** — Primary legacy access layer for `TenK`/`TenQ`/`EightK`.

- `__init__(html, chunk_fn, prefix_src)` — calls `chunk(html)` (which calls `HtmlDocument.generate_chunks()`), then `chunk_fn(self.chunks)` to build `_chunked_data` DataFrame — `edgar/files/htmltools.py:339`
- `list_items() -> List[str]` — returns unique non-empty Items from `_chunked_data` — `edgar/files/htmltools.py:368`
- `__getitem__(item)` — by int: returns chunk text; by str: calls `chunks_for_item(item)` — `edgar/files/htmltools.py:565`
- `chunks_for_item(item) -> Iterator` — filters `_chunked_data` by Item column with regex — `edgar/files/htmltools.py:440`
- `get_item_with_part(part, item, markdown)` — calls `_chunks_mul_for(part, item)`, assembles text or markdown — `edgar/files/htmltools.py:489`
- `get_introduction(markdown)` — content before first Part/Item — `edgar/files/htmltools.py:522`
- `get_signature(markdown)` — signature-flagged chunks — `edgar/files/htmltools.py:505`
- `tables()` — generator over `TableBlock` objects in all chunks — `edgar/files/htmltools.py:458`
- `as_dataframe()` — returns `_chunked_data` with caching — `edgar/files/htmltools.py:354`

**`DocumentData`** — iXBRL header/data extraction.

- `parse_header(ix_header_element) -> DocumentData` — extracts contexts, units, hidden properties from `ix:header` tag; decomposes the header after parsing — `edgar/files/html_documents.py:123`
- `parse_inline_data(start_element)` — finds all `ix:nonfraction/nonnumeric/fraction` tags, merges into `.data` DataFrame — `edgar/files/html_documents.py:193`
- `__getitem__(name)` — lookup by name in `.data` — `edgar/files/html_documents.py:81`
- `__contains__(item)` — membership test on `.data.name` — `edgar/files/html_documents.py:87`

**`MarkdownRenderer`** — Renders `Document` nodes to markdown.

- `render() -> str` — iterates nodes, dispatches per type, joins with `\n\n`, cleans spacing — `edgar/files/markdown.py:18`
- `_render_heading(node) -> str` — `#`-prefixed per `node.level` — `edgar/files/markdown.py:71`
- `_render_text_block(node) -> str` — applies bold/center wrappers from `node.style`; checks `is_note`/`is_quote` metadata — `edgar/files/markdown.py:85`
- `_render_table(processed) -> str` — GFM table with `:---:` alignment markers — `edgar/files/markdown.py:107`
- `_render_page_break(node) -> str` — `{N}---...---` delimiter format — `edgar/files/markdown.py:178`

**Node types** (`edgar/files/html.py`):

- `HeadingNode(content, style, level)` — levels 1-4 — `edgar/files/html.py:67`
- `TextBlockNode(content, style)` — `edgar/files/html.py:136`
- `TableNode(content, style)` — holds `List[TableRow]`; `_processed` cached property calls `TableProcessor.process_table()` — `edgar/files/html.py:235`
- `PageBreakNode(page_number)` — `edgar/files/html.py:329`

**Block types** (`edgar/files/html_documents.py`):

- `Block` — base; `.get_text()`, `.to_markdown()`, `.is_empty()`, `.is_linebreak()` — `edgar/files/html_documents.py:225`
- `TextBlock(text, inline)` — cached `.num_words`, `.is_header`, `.analyze()` → `TextAnalysis` — `edgar/files/html_documents.py:278`
- `TableBlock(table_element)` — wraps BS4 Tag; `.to_dataframe()`, `.to_markdown()` uses pandas `.to_markdown()` — `edgar/files/html_documents.py:308`
- `LinkBlock(text, tag, alt, src)` — image/link blocks — `edgar/files/html_documents.py:254`

---

### Class hierarchy

```
BaseNode (ABC)                        Block
  HeadingNode                           TextBlock
  TextBlockNode                         TableBlock
  TableNode                             LinkBlock
  PageBreakNode

DocumentNode (dataclass, legacy)      HtmlDocument
Document                                ChunkedDocument
  └─ constructed by SECHTMLParser

DocumentData
  (standalone, no inheritance)

MarkdownRenderer (standalone)
  └─ renders Document

TableProcessor (static methods)
ColumnOptimizer
ProcessedTable (dataclass)
StyleInfo (dataclass)
StyleUnit (dataclass)
Width (dataclass)
```

---

### Configuration & options

| Option | Type | Default | Effect |
|---|---|---|---|
| `SECHTMLParser.extract_data` | `bool` | `True` | Whether to extract iXBRL `DocumentData` from `ix:header` |
| `SECHTMLParser.include_page_breaks` | `bool` | `False` | Enable page-break marking and `PageBreakNode` emission |
| `Document.parse(include_page_breaks)` | `bool` | `False` | Passed through to `SECHTMLParser` |
| `to_markdown(include_page_breaks)` | `bool` | `False` | Passed to `Document.parse()` |
| `to_markdown(start_page_number)` | `int` | `0` | Offset added to page break numbers in output |
| `ChunkedDocument(chunk_fn)` | `Callable` | `chunks2df` | Swap to `decimal_chunk_fn` for 8-K decimal item patterns |
| `ChunkedDocument(prefix_src)` | `str` | `""` | URL prefix prepended to `LinkBlock` src values |
| `HtmlDocument.from_html(extract_data)` | `bool` | `False` | Whether to parse iXBRL header |
| `process_content(track_filtered)` | `bool` | `False` | Returns `(str, dict)` with filter metadata if True |
| `ColumnOptimizer(total_width)` | `int` | `100` | Target total table width in chars |
| `ColumnOptimizer(min_data_col_width)` | `int` | `15` | Minimum width of numeric data columns |
| `ColumnOptimizer(max_left_col_ratio)` | `float` | `0.5` | Max fraction of total width for label column |

---

### Data flow / lifecycle

**Path A — `Filing.markdown()` (the main user-facing path)**

1. `Filing.markdown()` (`edgar/_filings.py:1699`) calls `Filing.html()` to get raw HTML string.
2. `get_clean_html(html)` (`edgar/files/html_documents.py:791`) → `HtmlDocument.get_root()` → strips `<DOCUMENT><TEXT>` wrapper, parses with lxml, runs `fixup_soup()` and `clean_html_root()` (removes `ix:header`, scripts, TOC links, comments), returns cleaned HTML string.
3. `to_markdown(clean_html, include_page_breaks, start_page_number)` (`edgar/files/markdown.py:184`) → `Document.parse(html, include_page_breaks)` → `SECHTMLParser(root, include_page_breaks).parse()` → `Document(nodes=[...])` → `MarkdownRenderer(document, start_page_number).render()`.
4. If parsing fails or HTML is absent, falls back to `text_to_markdown(text_content)` wrapping text in `<pre>` tags.

**Path B — `ChunkedDocument` / company report item access (TenK/TenQ/EightK)**

1. `TenK.chunked_document` (`edgar/company_reports/ten_k.py:329`) — `@cached_property` → `ChunkedDocument(self._filing.html(), prefix_src=self._filing.base_dir)`.
2. `ChunkedDocument.__init__`: calls `chunk(html)` → `HtmlDocument.from_html(html).generate_chunks()` → `List[List[Block]]`.
3. `chunks2df(chunks)` builds a DataFrame with columns: Text, Table, Chars, Signature, TocLink, Toc, Empty, Part, Item.
4. Items detected via regex (`int_item_pattern` / `decimal_item_pattern`); Part via `detect_part()`. Both forward-filled.
5. `list_items()` returns unique Item values. `__getitem__(item_str)` or `chunks_for_item(item)` returns assembled text.
6. `TenK` also has a newer `ParsedHtml10K` path (`edgar/files/html_documents_id_parser.py`) that extracts items via TOC anchor links rather than text chunking — used as primary when available, falls back to `ChunkedDocument`.
7. Rendering: `assemble_block_text()` / `assemble_block_markdown()` streams block `.get_text()` or `.to_markdown()`. Tables in markdown mode use `table_to_markdown()` from `html_documents.py` (ASCII-style pipe table, NOT GFM).

**Path C — `process_content()` (notes/XBRL rendering)**

1. `edgar/xbrl/notes.py` calls `from edgar.markdown import process_content` to render Note HTML → LLM-optimized markdown.
2. `process_content(html, section_title)` (`edgar/markdown.py:1128`): parses with BeautifulSoup, iterates `p/div/table/ul/ol/h1-h6` elements.
3. Tables → `is_xbrl_metadata_table()` filter → `extract_table_title()` (6-source priority: caption, summary, preceding heading, spanning row, inferred, section title) → `html_to_json()` → `list_of_dicts_to_table()` → GFM markdown table with deduplication.
4. `html_to_json()`: copies table soup, preprocesses currency (`[$][100]` → `[$100]`) and percent cells, builds matrix, removes layout rows (`is_width_grid_row`), detects label column via `is_labelish()` heuristics, produces `List[dict]` records.
5. `list_of_dicts_to_table()`: deduplicates columns with identical data signatures, filters placeholder headers (`col_N`), right-aligns numeric columns, bolds total rows.
6. Duplicate tables detected by `(title, keys, first-8-row-values, row-count)` signature hash.

**Page break detection lifecycle**

1. `PageBreakDetector.mark_page_breaks(element)` (`edgar/files/page_breaks.py:91`) stamps `_is_page_break='true'` on:
   - `page-break-before/after: always` CSS (p/div/hr)
   - Class selectors: `BRPFPageBreak`, `pagebreak`, `page-break`
   - HR with `height:3px` style
   - Divs with page-like physical dimensions (842.4pt/792pt/1008pt height + 597.6pt/612pt width + position/overflow)
2. `SECHTMLParser._process_element()` checks `element.get('_is_page_break') == 'true'` before any other processing.
3. On page-break element: `_handle_page_break_element()` emits `PageBreakNode` + processes contained content. After all nodes parsed, sequential renumbering pass assigns `page_number = 0, 1, 2...`.
4. `MarkdownRenderer._render_page_break()` outputs `{N}------------------------------------------------` markers.

---

### Design patterns

- **Dual-mode div processing** — `SECHTMLParser` marks all ancestor divs of tables with `has_table=True` attribute, then dispatches to `_process_structured_content` (structure-preserving) vs `_process_inline_content` (text-combining) based on this flag.
- **Style cascading via stack** — `SECHTMLParser.style_stack` (List of `StyleInfo`) is push/pop around each element visit; child style merges with parent via `StyleInfo.merge()` (child props take precedence).
- **IX tag metadata tracking** — `IXTagTracker` maintains a stack and continuation map for `ix:` namespaced elements; all produced nodes get XBRL context metadata attached via `_apply_metadata_to_nodes()`.
- **Lazy/cached processing** — `TableNode._processed` is a `@cached_property` calling `TableProcessor.process_table()`; `TextBlock.num_words`/`is_header` are `@cached_property`; `ChunkedDocument.as_dataframe()` manual cache with `_cached_dataframe`.
- **Block compression** — `HtmlDocument._compress_blocks()` merges adjacent whitespace-only blocks with preceding blocks, avoiding fragmented output.
- **Signature-based deduplication** — `process_content()` hashes table data (title + column keys + first 8 rows + row count) to skip duplicate tables common in filings with repeated TOC tables.
- **ESCAPE-AFTER-EXTRACTION** pattern — `html_to_json()` extracts structured data (labels, values) from raw cell text before HTML escaping, avoiding corruption of currency/percent values.
- **Frame-gated deprecation warnings** — `edgar/files/_deprecation.py` provides `warn_legacy_html_usage()` which walks the call stack to suppress the `DeprecationWarning` when the instantiation is internal to edgartools (i.e., the first non-transparent frame is any `edgar.*` module). User code, notebooks, and third-party libraries still receive the warning at their own call site. This prevents `-W error` test suites from exploding on every `import edgar` (#832). `html.py`, `html_documents.py`, and `htmltools.py` emit the warning via this helper at class instantiation time (not import time).

---

### Cross-domain interactions

**Imports into edgar/files/**

- `edgar.files.html` imports: `edgar.files.html_documents.DocumentData`, `HtmlDocument`; `edgar.files.styles.*`; `edgar.files.tables.TableProcessor`, `ColumnOptimizer`, `ProcessedTable`; `edgar.richtools.repr_rich`; `edgar.core.log`
- `edgar.files.htmltools` imports: `edgar.files.html_documents.Block`, `HtmlDocument`, `LinkBlock`, `TableBlock`, `table_to_markdown`
- `edgar.files.html_documents_id_parser` imports: `edgar.files.html_documents.*`; `edgar.files.htmltools.ChunkedDocument`
- `edgar.markdown` imports: `bs4.BeautifulSoup` only (no edgar sub-imports at module level)
- `edgar._markdown` imports: `edgar.files.html_documents.HtmlDocument`

**Consumers of edgar/files/ in the rest of the package**

| Consumer | Uses |
|---|---|
| `edgar/_filings.py` | `get_clean_html`, `html_sections`, `to_markdown` (files/markdown), `text_to_markdown` (_markdown) |
| `edgar/attachments.py` | `get_clean_html`, `to_markdown` (files/markdown) |
| `edgar/company_reports/_base.py` | `ChunkedDocument` (deprecated property) |
| `edgar/company_reports/ten_k.py` | `ChunkedDocument`, `ParsedHtml10K` |
| `edgar/company_reports/ten_q.py` | `ChunkedDocument`, `ParsedHtml10Q` |
| `edgar/company_reports/current_report.py` | `ChunkedDocument`, `Document` (html.py), `chunks2df`, `decimal_chunk_fn` |
| `edgar/company_reports/press_release.py` | `HtmlDocument` |
| `edgar/company_reports/sixk.py` | `Document` (html.py) |
| `edgar/xbrl/notes.py` | `edgar.markdown.process_content` |
| `edgar/__init__.py` | `detect_page_breaks`, `mark_page_breaks`, `Document` |

---

### Gotchas & notable behaviors

- **Import-time DeprecationWarning** — importing `edgar.files.html`, `edgar.files.html_documents`, or `edgar.files.htmltools` fires `DeprecationWarning` unconditionally at module load. Code that transitively imports these (e.g., via `edgar.company_reports`) will see the warning unless filtered.

- **Two separate table-to-markdown paths** — `ChunkedDocument.assemble_block_markdown()` uses `table_to_markdown()` from `html_documents.py` (ASCII pipe table, not GFM). `MarkdownRenderer._render_table()` in `files/markdown.py` uses `TableProcessor.process_table()` + GFM. These produce different output from the same HTML.

- **`table_to_markdown` vs `TableBlock.to_markdown()`** — `TableBlock.to_markdown()` calls `self.to_dataframe().to_markdown()` (pandas GFM), while `_render_blocks_using_old_markdown_tables()` in htmltools uses `table_to_markdown()` (the ASCII version). Both exist in parallel.

- **Decimal vs integer item patterns** — `chunks2df` default uses `int_item_pattern` (`Item 1`, `Item 1A`); `decimal_chunk_fn` uses `decimal_item_pattern` (`Item 1.02`). 8-K uses `decimal_chunk_fn` via `current_report.py`.

- **`_chunks_mul_for` non-consecutive index handling** — when the same Part+Item appears at multiple non-consecutive positions (from TOC duplication), it emits a `warnings.warn` and silently discards all but the longest continuous segment.

- **`SECHTMLParser` page-break renumbering** — if no page breaks are detected despite `include_page_breaks=True`, a synthetic page 0 break is inserted at document start. All page breaks are renumbered sequentially after the full parse in a second pass.

- **`get_root()` TEXT wrapper detection** — checks only the first 500 chars for `<TEXT>` to decide whether to strip the SEC submission wrapper (`edgar/files/html_documents.py:461`).

- **`process_content` sparse table guard** — tables with 50+ columns and less than 5% cell fill rate are silently dropped to avoid rendering noise from layout-only tables.

- **`html_to_json` 90th-percentile column cap** — when a table has 5+ rows, `max_cols` is capped at the 90th percentile of row widths to neutralize outlier colspan values (`edgar/markdown.py:659`).

- **`ParsedHtml10K` vs `ChunkedDocument` fallback** — `TenK` tries `ParsedHtml10K` first; if it returns empty items, it falls back to `ChunkedDocument`. The `chunked_document` property on `_base.py` is an explicit deprecated property with its own warning (`edgar/company_reports/_base.py:144`).

- **`fixup_soup()` pre-processing** — replaces `<pre>` tags with `<div>` wrappers before any parsing to prevent lxml from treating pre-formatted blocks differently.

- **`is_header()` heuristic** — title/upper-case detection at 60% threshold; used in `HtmlDocument.markdown` for newline spacing but not in `SECHTMLParser` (which uses `get_heading_level()` with CSS score-based detection).
