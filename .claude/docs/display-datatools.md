# EdgarTools Rich Display & Data Utilities — Reference Doc

## Overview

Three layers form the shared presentation and data-processing foundation used library-wide:

| Layer | Module(s) | Purpose |
|---|---|---|
| Rich rendering | `edgar/richtools.py` | Convert rich objects to string/SVG/PNG, terminal printing |
| Design language | `edgar/display/` | Unified color palette, symbols, statement styles, formatting helpers |
| DataFrame utils | `edgar/datatools.py` | DataFrame/PyArrow manipulation, pagination |
| XML helpers | `edgar/xmltools.py` | BeautifulSoup tag traversal for all XML-based form parsers |

---

## 1. `edgar/richtools.py`

**Exports:** `repr_rich`, `rich_to_text`, `strip_ansi_text`, `df_to_rich_table`, `colorize_words`, `print_xml`, `print_rich`, `Docs`

### Core rendering pipeline

The canonical pattern for all `__repr__` methods across the library:
1. Class implements `__rich__(self)` returning a Rich renderable (Panel, Table, Tree, etc.)
2. `__repr__` calls `repr_rich(self.__rich__())`

#### `repr_rich(renderable, strip_ansi=False, **console_args) -> str`
Renders any Rich renderable to a captured string via `Console.capture()`. Passes `**console_args` through to `Console()` — use `force_terminal=False` for plain-text output, `width=N` for fixed-width. Used in virtually every `__repr__` in the library.

#### `rich_to_text(rich_object, width=None) -> str`
Calls `repr_rich(..., force_terminal=False)` then strips ANSI. Use when you need layout-preserving plain text (e.g., filing text extraction, XBRL statement export). Called by `_filings.py` (width=500 for tables), `attachments.py`, `xbrl/rendering.py`, `sgml/filing_summary.py`, `company_reports/`.

#### `strip_ansi_text(text) -> str`
Strips ANSI escape sequences via regex. Used internally by `rich_to_text`.

#### `rich_to_svg(rich_object, width=120) -> str`
Exports Rich renderable to SVG via `Console(record=True).export_svg()`. Uses `color_system="standard"`.

#### `rich_to_png(rich_object, width=120, output_path=None) -> Optional[bytes]`
SVG → PNG via `cairosvg` (optional dependency). Returns bytes or saves to file.

### DataFrame rendering

#### `df_to_rich_table(df, index_name=None, title="", title_style="", max_rows=20, table_box=box.SIMPLE) -> Table`
Accepts `pd.DataFrame` or `pa.Table` (auto-converts pyarrow). Applies `table_styles` dict for per-column coloring (e.g., `filingDate` → `deep_sky_blue1`, `form` → `dark_sea_green4`). Truncates to `max_rows` with `...` separator showing head + tail halves.

**`table_styles` column-name-to-color map** (defined at module level):
- `form`, `document` → `dark_sea_green4`
- `filingDate`, `filing_date`, `filed`, `Shares`, `Reporting Owner`, `issuer`, `fact`, `industry` → `deep_sky_blue1`

### XML display

#### `print_xml(xml: str)`
Prints XML with `XMLHighlighter` (inline regex) and `xml_theme`. Colors: namespaces=magenta, tag names=light_goldenrod3, attributes=grey70, values/URLs=green, comments=grey58. Used by `attachments.py` for raw XML document display.

### Utility

#### `colorize_words(words, colors=None) -> Text`
Cycles through `["deep_sky_blue3", "red3", "dark_sea_green4"]` (or supplied list) over a word list. Returns `Text.assemble()` result.

#### `print_rich(rich_object, **args)`
Convenience wrapper around `Console(**args).print(rich_object)`.

### `Docs` class

Documentation browser attached to major user-facing objects via a `.docs` property.

**Attachment points** (objects that expose `.docs`):
- `Filing`, `Filings` — `_filings.py`
- `Company`, `Entity` — `entity/core.py`, `entity/filings.py`
- `XBRL` — `xbrl/xbrl.py`
- `Statement` — `xbrl/statements.py`
- `FormC` — `offerings/formc.py`

**Content resolution order:**
1. Markdown file at `<module_dir>/docs/<ClassName>.md`
2. `obj.__doc__`
3. Fallback string

**`__rich__()`** renders as `Panel(Markdown(...) or Text(...), border_style="blue")`. Detects markdown by presence of `` ``` ``, `#`, or `*`.

**`search(query, use_bm25=True)`** splits content at `## ` headings, runs `BM25Search` or `RegexSearch` from `edgar.search.textsearch`.

---

## 2. `edgar/display/` — Design Language

### `edgar/display/__init__.py`

Re-exports from `styles.py`: `PALETTE`, `SYMBOLS`, `get_style`, `styled`, `label_value`, `company_title`, `identifier`, `get_statement_styles`, `source_text`.

### `edgar/display/styles.py`

#### `PALETTE` dict — semantic color map

Categories and key entries:

| Category | Key examples | Value |
|---|---|---|
| Primary | `company_name` | `"bold green"` |
| Primary | `ticker` | `"bold gold1"` |
| Identifiers | `cik`, `accession` | `"dodger_blue1"` |
| Structure | `section_header` | `"bold"` |
| Labels/Values | `label` | `"grey70"` |
| Metadata | `metadata`, `hint`, `date`, `source` | `"dim"` / `"dim italic"` |
| Source variants | `source_entity_facts` | `"cyan"` |
| Source variants | `source_xbrl` | `"gold1"` |
| Borders | `border`, `separator` | `"grey50"` |
| Status | `positive`, `negative`, `warning`, `info` | `"green"`, `"red"`, `"yellow"`, `"cyan"` |
| Status | `foreign`, `canadian` | `"magenta"`, `"red"` |
| Stmt rows | `stmt_abstract`, `stmt_abstract_top` | `"bold cyan"` |
| Stmt rows | `stmt_total`, `stmt_subtotal` | `"bold"`, `"bold dim"` |
| Stmt rows | `stmt_item_low_confidence` | `"dim italic"` |
| Stmt values | `stmt_value_negative` | `"red"` |
| Comparison | `stmt_increase`, `stmt_decrease` | `"green"`, `"red"` |
| Badges (form) | `badge_10k`, `badge_10q`, `badge_8k` | `"bold white on dodger_blue1/green/dark_orange"` |
| Badges (source) | `badge_source_xbrl` | `"bold white on gold3"` |
| Badges (source) | `badge_source_entity_facts` | `"bold white on cyan"` |

**Design principles** (from module docstring):
- Professional, balanced colors
- Card-based layout with single outer borders
- Weight-based typography (bold/dim, no font-size changes)
- No emojis — Unicode symbols only

#### `SYMBOLS` dict — Unicode symbol map

| Key | Char | Use |
|---|---|---|
| `arrow_right` | → | Navigation, `entity/core.py` period ranges |
| `bullet` | • | List items, inline separators |
| `pipe` | │ | Inline separator |
| `check` / `cross` | ✓/✗ | Status badges |
| `warning` / `info` | ⚠/ℹ | Status badges |
| `increase` / `decrease` | ▲/▼ | Financial comparison indicators |
| `low_confidence` | ◦ | Hollow bullet for low-confidence XBRL items |
| `ellipsis` | … | Truncation (`entity/core.py`) |

#### Style utility functions

- `get_style(name) -> str` — lookup from PALETTE, returns `""` for unknown keys
- `styled(text, style_name) -> Text` — creates `Text(text, style=get_style(style_name))`
- `label_value(label, value, label_style="label", value_style="value") -> Text` — assembles `"label value"` pair
- `company_title(name, ticker=None) -> Text` — green bold name + gold ticker
- `identifier(value, id_type="cik") -> Text` — dodger_blue1 for CIK/accession
- `source_text(source) -> Text` — `"Source: <name>"` in dim italic

#### `get_statement_styles() -> dict`

Returns a structured dict consumed by `xbrl/rendering.py`, `entity/enhanced_statement.py`, `ttm/statement.py`. Top-level keys: `header`, `row`, `value`, `structure`, `metadata`, `comparison`. The `comparison` values embed both `symbol` (from `SYMBOLS`) and `style` (from `PALETTE`).

#### Status message printers (module-level, use `_console`)

`print_warning(message, details=None)`, `print_error(...)`, `print_info(...)`, `print_success(...)`
Each wraps message in a `Padding` with badge style and optional dim details line. Called from `_filings.py`.

### `edgar/display/formatting.py`

Formatting helpers for terminal display and AI output.

#### Numeric/currency

- `moneyfmt(value, places=0, curr='$', sep=',', dp='.', pos='', neg='-') -> str` — Decimal-precise money formatting with configurable separators. Used for exact financial display.
- `format_currency_short(value, currency='$') -> str` — Scale-abbreviated: `≥1B` → `$X.XB`, `≥1M` → `$X.XM`, `≥1000` → `$X,XXX`, else 2 dp. Handles `None`/NaN → `""`. Used throughout `proxy/core.py`, `company_reports/`, `form144.py`, `ttm/`.

#### Date/size

- `datefmt(value, fmt="%Y-%m-%d") -> str` — Accepts datetime or string (`%Y%m%d`, `%Y%m%d%H%M%S`, `%Y-%m-%d`). Used in `company_reports/ten_k.py`, `ten_q.py`, `forty_f.py`.
- `display_size(size) -> str` — Uses `humanize.naturalsize` (binary, strips "i"), empty string for falsy input. Used in `_filings.py`, `headers.py`, `entity/filings.py`.
- `accepted_time_text(accepted_datetime) -> Text` — Color-codes filing time: pre-market=bright_cyan, regular=bright_green, 4-5pm=yellow, after-hours=bright_red. Used in `current_filings.py`.

#### Name/string utilities

- `reverse_name(name: str) -> str` — Converts SEC-style `"LAST FIRST [MIDDLE] [SUFFIX]"` to `"First [Middle] Last [Suffix]"`. Handles multi-word surnames (Van, De, Del), suffixes (Jr, III, MD, PhD), title prefixes (Dr, Prof). Used in `entity/core.py` for insider names.
- `split_camel_case(item) -> str` — Splits camelCase to spaced words, preserves consecutive uppercase.
- `yes_no(value: bool) -> str` — `"Yes"` / `"No"`. Used in `offerings/formc.py`.

#### Rich Text identifiers

- `cik_text(cik) -> Text` — Pads to 10 digits, dims leading zeros, bolds value.
- `accession_number_text(accession) -> Text` — Splits `CIK-YEAR-SEQ`, dims leading zeros in CIK/SEQ, colors year in `dodger_blue1`.
- `datefmt`, `display_size`, `accepted_time_text` — all return plain strings or `Text` objects for inline embedding.

### `edgar/display/demo.py`

Run with `python -m edgar.display.demo` to preview the full design language. Contains mockups for company cards, filing cards, filings tables, financial statements with source attribution, and reference tables for all palette entries, symbols, and identifier formatting. Not imported at runtime — development/iteration tool only.

---

## 3. `edgar/datatools.py`

**Exports:** `compress_dataframe`, `table_html_to_dataframe`, `table_tag_to_dataframe`, `markdown_to_dataframe`, `dataframe_to_text`, `clean_column_text`, `convert_to_numeric`, `describe_dataframe`, `na_value`, `replace_all_na_with_empty`, `convert_to_pyarrow_backend`, `drop_duplicates_pyarrow`, `repr_df`, `DataPager`, `PagingState`

### DataFrame I/O

- `table_html_to_dataframe(html_str) -> pd.DataFrame` — lxml xpath parse, handles `td`/`th`, calls `clean_column_text` + `compress_dataframe`.
- `table_tag_to_dataframe(table_tag) -> pd.DataFrame` — BeautifulSoup Tag version (no compress).
- `markdown_to_dataframe(markdown_table) -> pd.DataFrame` — Pipe-delimited markdown, skips separator row (index 1), calls `compress_dataframe`.
- `dataframe_to_text(df, include_index=False, include_headers=False) -> str` — Tab-separated plain text, column-width-padded. For text embedding/export.

### DataFrame cleaning

- `compress_dataframe(df) -> pd.DataFrame` — Replaces `""` with `pd.NA`, drops all-NA rows and columns, refills with `""`.
- `clean_column_text(text) -> str` — Strips newlines, collapses whitespace: `'Per\nShare'` → `'Per Share'`.
- `adjust_column_headers(df)` — Replaces integer column names (default pandas index) with `""`.
- `should_promote_to_header(df) -> bool` — Heuristic: checks first row for header keywords and distinctiveness vs second row.
- `replace_all_na_with_empty(df_or_series)` — Replaces all-NA columns/series with `""` strings (avoids mixed-type issues).
- `na_value(value, default_value='') -> object` — Returns `default_value` if `pd.isna(value)`.

### Type conversion

- `convert_to_numeric(series)` — `pd.to_numeric` with fallback to original series on ValueError.
- `convert_to_pyarrow_backend(data: pd.DataFrame)` — Converts object/string cols to str, float to float32, then `convert_dtypes(dtype_backend="pyarrow")`. Used before PyArrow operations.
- `describe_dataframe(df) -> pd.DataFrame` — Returns dtypes + memory usage per column including index, with total row.
- `repr_df(df, hide_index=True) -> str` — Thin `df.to_string()` wrapper.

### PyArrow utilities

- `drop_duplicates_pyarrow(table, column_name, keep='first') -> pa.Table` — No pandas round-trip: uses `np.unique` on the column array, builds boolean mask, filters with `table.filter(pa.array(mask))`. Used in `_filings.py` and fund/ownership parsers.

### Pagination (`DataPager`, `PagingState`)

`PagingState` in `datatools.py` is a simple `@dataclass` with `page`, `page_size`, `total_items` and properties `start_idx`, `end_idx`, `has_more`. The production `PagingState` used by `_filings.py` and `entity/filings.py` is a more capable version defined in `edgar/core.py` (also imported via `_filings.py`). `DataPager` wraps any `pd.DataFrame` or `pa.Table` with `get_page(page)` slicing. Both are re-exported from `edgar.core` and `edgar._filings`.

---

## 4. `edgar/xmltools.py`

**Exports:** `child_text`, `child_value`, `child_texts`, `find_element`, `get_footnote_ids`, `optional_decimal`, `value_or_footnote`, `extract_child_text`, `extract_child_value`, `value_with_footnotes`

All helpers operate on BeautifulSoup `Tag` objects. Used by every XML-based form parser: `ownership/ownershipforms.py`, `beneficial_ownership/schedule13.py`, `offerings/formd.py`, `offerings/formc.py`, `thirteenf/parsers/primary_xml.py`, `muniadvisors.py`, `effect.py`, `_party.py`.

### Element traversal

- `find_element(xml_tag_or_string, element_name) -> Optional[Tag]` — Accepts Tag or raw XML string. Parses string with `BeautifulSoup(..., features="xml")`, returns Tag or None.
- `child_text(parent, child) -> Optional[str]` — `parent.find(child).text.strip()` or None.
- `child_texts(parent, child) -> List[str]` — `[el.text for el in parent.find_all(child)]`.
- `child_value(parent, child, default_value=None) -> Optional[str]` — Calls `value_with_footnotes` on the found child, returns default if not found.

### SEC footnote handling

SEC XML frequently wraps values with sibling `<footnoteId>` elements:
```xml
<underlyingSecurityTitle>
    <value>Class B Common Stock</value>
    <footnoteId id="F2"/>
    <footnoteId id="F3"/>
</underlyingSecurityTitle>
```

- `get_footnote_ids(tag, sep=',') -> str` — Joins all `footnoteId[@id]` values.
- `value_with_footnotes(tag, footnote_sep=",") -> str` — Returns `"value [F2,F3]"` or just value or just footnotes.
- `value_or_footnote(el) -> Optional[str]` — Returns `<value>` text, else `<footnote>` or `<footnoteId id>`.

### Convenience wrappers

- `optional_decimal(parent, child) -> Optional[Decimal]` — `child_text` → `Decimal`, handles `"N/A"` → None.
- `extract_child_text(tag, key, child_tag_name) -> Tuple[str, Optional[str]]` — Returns `(key, child_text(...))`, for populating dicts in list comprehensions.
- `extract_child_value(tag, key, child_tag_name) -> Tuple[str, Optional[str]]` — Returns `(key, child_value(...))`, same pattern.

---

## Cross-cutting import map

| Consumer | Imports from |
|---|---|
| `_filings.py` | `richtools` (repr_rich, rich_to_text, Docs, print_rich), `display.formatting` (accession_number_text, display_size), `display.styles` (print_info, print_warning), `datatools` (DataPager, PagingState, drop_duplicates_pyarrow) |
| `xbrl/rendering.py` | `richtools` (repr_rich, rich_to_text), `display` (get_statement_styles, get_style, SYMBOLS) |
| `entity/enhanced_statement.py` | `display` (get_statement_styles, SYMBOLS, get_style) |
| `entity/core.py` | `display.formatting` (cik_text, datefmt, reverse_name), `display` (SYMBOLS, get_style) |
| `proxy/core.py` | `display.formatting` (format_currency_short) |
| `company_reports/` | `display.formatting` (datefmt, format_currency_short) |
| `xmltools` consumers | `ownership/ownershipforms.py`, `schedule13.py`, `formd.py`, `formc.py`, `thirteenf/parsers/primary_xml.py`, `muniadvisors.py`, `effect.py`, `_party.py` |
| `datatools` consumers | `core.py`, `files/htmltools.py`, `files/html_documents.py`, `funds/data.py` |
