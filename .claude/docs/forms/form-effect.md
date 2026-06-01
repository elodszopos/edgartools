# Form EFFECT — Effectiveness Notice

**SEC form codes**: `EFFECT`
**Python class**: `Effect`
**Access**: `filing.obj()` → `Effect`
**Base fields**: See `_base-filing.md`
**Source**: `edgar/effect.py`

---

## Complete Field Reference

### From Filing (inherited)
See `_base-filing.md`

### Effect-Specific Fields

#### Instance Attributes (set in `__init__`)

| Field | Type | Description |
|-------|------|-------------|
| `submission_type` | `str` | Always `'EFFECT'` from `<submissionType>` element |
| `effectiveness_data` | `EffectiveData` | Core effectiveness data container |
| `is_live` | `bool` | True if `<testOrLive>` text is `'LIVE'`; False if element missing |
| `schema_version` | `Optional[str]` | From `<schemaVersion>` element (e.g. `'X0101'`) |

#### Properties — Immediate (no network)

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `effective_date` | `str` | no | `effectiveness_data.final_effective_date` |
| `cik` | `Optional[str]` | no | `effectiveness_data.filer.cik`; `None` if no filer |
| `entity` | `Optional[str]` | no | `effectiveness_data.filer.entity_name`; `None` if no filer |
| `source_submission_type` | `str` | no | `effectiveness_data.submission_type or effectiveness_data.form or ""`; handles both XML path variants |
| `source_accession_no` | `Optional[str]` | no | `effectiveness_data.accession_no` |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_xml` | `submission_xml: str` | `Effect` | Classmethod; parses `<edgarSubmission>` XML via BeautifulSoup XML mode |
| `get_source_filing` | — | `Optional[Filing]` | Live API calls; no caching; tries `accession_no` first, then `file_number + form`; returns `None` on failure |
| `summary` | — | `pd.DataFrame` | Manual `_cached_summary` attribute (not `cached_property`); indexed by `entity` |
| `to_context` | `detail: str = 'standard'` | `str` | AI-optimized text; detail: `'minimal'`/`'standard'`/`'full'` |

---

## Nested Objects

### `EffectiveData` (plain class)
Data container for the `<effectiveData>` XML element.

| Field | Type | Description |
|-------|------|-------------|
| `final_effective_date` | `str` | `<finalEffectivenessDispDate>` (e.g. `'2022-11-22'`) |
| `file_number` | `Optional[str]` | `<fileNumber>` from filer element (e.g. `'333-237642'`) |
| `accession_no` | `Optional[str]` | `<accessionNumber>` of the registration statement that became effective |
| `submission_type` | `Optional[str]` | `<submissionType>` within `<effectiveData>` (e.g. `'POS AM'`) |
| `form` | `Optional[str]` | `<form>` within `<effectiveData>` — alternative path for submission type |
| `filer` | `Filer` | Filer identity from `<filer>` element (from `edgar._party`) |

### `Filer` (from `edgar._party`) — `effectiveness_data.filer`

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `str` | Filer CIK (e.g. `'0000038723'`) |
| `entity_name` | `str` | Entity name (e.g. `'1st FRANKLIN FINANCIAL CORP'`) |
| `file_number` | `str` | SEC file number (e.g. `'333-237642'`) |

---

## DataFrame Schemas

### `summary()` columns

| Column | Type | Description |
|--------|------|-------------|
| `cik` | `str` | Filer CIK |
| `entity` | `str` | Entity name (used as DataFrame index) |
| `source` | `str` | `source_submission_type` |
| `live` | `bool` | `is_live` flag |
| `effective` | `str` | `effective_date` |

DataFrame is indexed by `entity` (`.set_index("entity")` applied).

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `<testOrLive>` element missing from XML | `is_live = False` (element checked with `and`) |
| `effectiveness_data.filer` is `None` | `cik` and `entity` properties return `None` |
| `submission_type` in `<effectiveData>` absent | `source_submission_type` falls back to `effectiveness_data.form` |
| Both `submission_type` and `form` absent | `source_submission_type` returns `""` |
| `source_accession_no` is `None` | `get_source_filing` falls back to `file_number + form` path |
| `file_number` and `form` both absent | `get_source_filing` returns `None` |
| `get_source_filing` network error | Returns `None` silently (no caching on failure) |
| `summary()` called multiple times | Returns cached `_cached_summary` after first call (manual cache, not `cached_property`) |

---

## Access Patterns

- `filing.obj()` → `Effect` (dispatch: `filing.xml()` → `Effect.from_xml(xml)`)
- `effect.effective_date` — when the registration became effective
- `effect.source_submission_type` — form type that triggered effectiveness (e.g. "S-1", "POS AM")
- `effect.source_accession_no` — accession number of the source filing
- `effect.get_source_filing()` — navigate back to the registration statement (network call)
- `effect.summary()` — one-row DataFrame for tabular display
- `effect.is_live` — verify this is a live (not test) submission
