# Form CORRESP / UPLOAD — SEC Correspondence

**SEC form codes**: CORRESP, UPLOAD
**Python class**: `Correspondence` (no base class); `CorrespondenceThread`
**Access**: `filing.obj()` → `Correspondence`; `corresp.thread` → `CorrespondenceThread`
**Base fields**: See `_base-filing.md`
**Source**: `edgar/correspondence.py`

## Complete Field Reference

### From Filing (inherited)
See `_base-filing.md`

### Correspondence-Specific Fields

#### Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing` | `Filing` | no | Underlying Filing object |
| `form` | `str` | no | `'CORRESP'` or `'UPLOAD'`; delegated from `_filing.form` |
| `company` | `str` | no | Filer company name; delegated from `_filing.company` |
| `cik` | `int` | no | Filer CIK; delegated from `_filing.cik` |
| `filing_date` | `str` | no | Filing date string; delegated from `_filing.filing_date` |
| `accession_no` | `str` | no | Accession number; delegated from `_filing.accession_no` |
| `correspondence_type` | `CorrespondenceType` | no | Enum classification — passed as constructor parameter; `_classify_correspondence()` runs in `from_filing()` before construction |
| `sender` | `str` | no | `'sec'` when form is UPLOAD, `'company'` for CORRESP |
| `referenced_file_number` | `Optional[str]` | no | SEC file number from Re: block, e.g. `'001-36743'`; None if not found |
| `referenced_form` | `Optional[str]` | no | Form being discussed, e.g. `'10-K'`, `'S-1'`; None if not found |
| `response_date` | `Optional[str]` | no | `'Response dated ...'` string from Re: block; None if absent |
| `fiscal_year_end` | `Optional[str]` | no | `'fiscal year ended ...'` string from Re: block; None if absent |
| `body` | `Optional[str]` | no | Full text content of the letter; None if text extraction failed |
| `thread` | `Optional[CorrespondenceThread]` | cached | Lazy thread reconstruction — triggers network calls for all company correspondence |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing: Filing` | `Correspondence` | Classmethod. Extracts text, classifies, returns instance. Always returns (never None). |
| `to_context` | `detail: str = 'standard'` | `str` | AI context string. `'minimal'`: identity only. `'standard'`: + metadata + available actions. `'full'`: + first 1000 chars of body. |

## Nested Objects

### CorrespondenceType (Enum)

| Value | Display Name | Trigger |
|-------|-------------|---------|
| `company_response` | Company Response | CORRESP + response pattern match |
| `acceleration_request` | Acceleration Request | CORRESP + Rule 461 / accelerat keyword |
| `sec_comment` | SEC Comment Letter | UPLOAD + numbered items or "please explain" language |
| `review_complete` | Review Complete | UPLOAD + "completed our review" / "no further comments" |
| `no_review` | No Review Notice | UPLOAD + "will not review" pattern |
| `company_letter` | Company Letter | CORRESP fallback |
| `sec_letter` | SEC Letter | UPLOAD fallback |

`.display_name` property returns the human-readable string.

### CorrespondenceThread

| Field | Type | Description |
|-------|------|-------------|
| `file_number` | `str` | SEC file number linking the thread, e.g. `'001-36743'` |
| `referenced_form` | `Optional[str]` | Form under review, e.g. `'10-K'` |
| `entries` | `List[Correspondence]` | All letters in chronological order (sorted by `filing_date`) |
| `is_resolved` | `bool` | True if last entry has type `REVIEW_COMPLETE` |
| `duration_days` | `Optional[int]` | Days from first to last entry; None if fewer than 2 entries |
| `comment_count` | `int` | Number of `SEC_COMMENT` entries |
| `response_count` | `int` | Number of `COMPANY_RESPONSE` or `ACCELERATION_REQUEST` entries |

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_correspondence` | `corresp: Correspondence` | `Optional[CorrespondenceThread]` | Classmethod. Fetches all CORRESP/UPLOAD for company CIK, filters by file number and referenced form. Returns None if `referenced_file_number` is absent or no entries match. |
| `to_context` | `detail: str = 'standard'` | `str` | AI context. `'minimal'`: stats only. `'standard'`: + per-entry timeline. |
| `__len__` | — | `int` | Number of entries |

## Error Paths

| Condition | Behavior |
|-----------|----------|
| Text extraction fails for a filing | `body` is None; metadata fields are None; `correspondence_type` defaults to `SEC_LETTER` or `COMPANY_LETTER` based on form |
| `referenced_file_number` is absent | `thread` returns None; `CorrespondenceThread.from_correspondence()` returns None |
| Thread network call fails | `from_correspondence()` returns None; exception is logged as warning |
| `duration_days` with < 2 entries | Returns None |

## Access Patterns

- `filing.obj()` → `Correspondence`
- `Correspondence.from_filing(filing)` — always returns, never None
- `corresp.thread` — may return None; first access triggers network (fetches all company CORRESP/UPLOAD)
- `filing.correspondence()` in `_filings.py:2223` — works on any form type using EDGAR metadata file number
- Thread reconstruction can be slow for prolific filers (many round trips)
