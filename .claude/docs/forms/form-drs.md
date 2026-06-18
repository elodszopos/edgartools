# Form DRS — Draft Registration Statement

**SEC form codes**: DRS, DRS/A
**Python class**: `DraftRegistrationStatement`
**Access**: `filing.obj()` -> `DraftRegistrationStatement`
**Source**: `edgar/offerings/drs.py`

## Overview

DRS filings are confidential draft submissions to the SEC. The EDGAR metadata only records "DRS" — the underlying public form type (S-1, F-1, S-3, etc.) must be detected from the document text. Registration numbers use the **377-XXXXXX** prefix (not 333-XXXXXX used by public registrations).

## Complete Field Reference

### Properties (immediate — set at construction)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing` | `Filing` | no | Underlying Filing object |
| `form` | `str` | no | "DRS" or "DRS/A" |
| `underlying_form` | `str` | no | Detected form type; see detection table below |
| `company` | `str` | no | Company name |
| `company_name` | `str` | no | Alias for `company` |
| `filing_date` | `str` | no | Filing date |
| `accession_number` | `str` | no | From `filing.accession_no` |
| `is_amendment` | `bool` | no | True if '/A' in form |
| `amendment_number` | `Optional[int]` | no | Parsed from "Amendment No. X" in cover text |
| `registration_number` | `Optional[str]` | no | 377-XXXXXX (confidential DRS prefix) |
| `underlying_object` | `RegistrationS1 \| RegistrationS3 \| None` | no | Delegated data object |

### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing: Filing` | `DraftRegistrationStatement` | Class method; detects form, extracts number, builds delegate |
| `to_context` | `detail: str = 'standard'` | `str` | LLM-optimized; includes underlying object context at standard/full |
| `__rich__` | — | `Panel` | Rich terminal rendering with underlying details |
| `__repr__` | — | `str` | Delegates to `repr_rich(__rich__())` |
| `__str__` | — | `str` | `DraftRegistrationStatement(form=..., underlying=..., company=..., date=...)` |

## Underlying Form Detection

Source: `edgar/offerings/drs.py:45`

Detection scans first 8000 chars of cover page text. Patterns are tested in this **exact order** (compound forms before simple to avoid prefix collision):

| Order | Pattern Matched | `underlying_form` |
|-------|----------------|-------------------|
| 1 | `FORM S-4` | `"S-4"` |
| 2 | `FORM F-4` | `"F-4"` |
| 3 | `FORM S-3` | `"S-3"` |
| 4 | `FORM F-3` | `"F-3"` |
| 5 | `FORM F-1` | `"F-1"` |
| 6 | `FORM S-1` | `"S-1"` |
| 7 | `FORM 20-F` | `"20-F"` |
| 8 | `FORM 40-F` | `"40-F"` |
| 9 | `GENERAL FORM FOR REGISTRATION OF SECURITIES` | `"Form 10"` |
| 10 | `FORM 10\b` | `"Form 10"` |
| none matched | — | `"Unknown"` |

All patterns use `re.IGNORECASE`. Detection uses BeautifulSoup `lxml` (not xml) to handle malformed draft HTML.

## Underlying Object Delegation

| `underlying_form` | `underlying_object` type |
|-------------------|--------------------------|
| `"S-1"` or `"F-1"` | `RegistrationS1` (built via `RegistrationS1.from_filing(filing)`) |
| `"S-3"` | `RegistrationS3` (built via `RegistrationS3.from_filing(filing)`) |
| Any other value | `None` (S-4, F-4, 20-F, 40-F, Form 10 have no delegated object) |

Construction exceptions for `underlying_object` are silently caught; result is None.

## Registration Number Extraction

Source: `edgar/offerings/drs.py:141`

Two-step extraction:
1. `filing.header.file_numbers` — looks for entries starting with `"377-"`
2. Fallback: regex `377-\d{5,7}` search in HTML

**Critical distinction**: DRS uses `377-XXXXXX` prefix; public S-1/S-3 use `333-XXXXXX`.

## Accessing Underlying Object Fields

When `underlying_form` is "S-1" or "F-1", `underlying_object` is `RegistrationS1`. When "S-3", it is `RegistrationS3`. All fields from those types are accessible via `underlying_object`:

| Access Path | Description |
|------------|-------------|
| `drs.underlying_object.cover_page` | S1CoverPage or S3CoverPage |
| `drs.underlying_object.offering_type` | S1OfferingType or S3OfferingType |
| `drs.underlying_object.fee_table` | RegistrationFeeTable or None |
| `drs.underlying_object.total_offering` | float or None |
| `drs.underlying_object.securities` | List[FeeTableSecurity] |
| `drs.underlying_object.state_of_incorporation` | str or None |
| `drs.underlying_object.sic_code` | str or None (S-1 only) |
| `drs.underlying_object.ein` | str or None |
| `drs.underlying_object.takedowns` | Filings or None (network) |
| `drs.underlying_object.related_filings` | Filings or None (network) |

For S-1 specifically:
| Access Path | Description |
|------------|-------------|
| `drs.underlying_object.selling_stockholders` | SellingStockholdersData or None (network) |
| `drs.underlying_object.dilution` | DilutionData or None (network) |
| `drs.underlying_object.capitalization` | CapitalizationData or None (network) |
| `drs.underlying_object.underwriting` | UnderwritingInfo or None (network) |
| `drs.underlying_object.effective_date` | str or None (network) |

For full field references of nested types, see `form-s1.md` and `form-s3.md`.

## Error Paths

| Condition | Behavior |
|-----------|----------|
| No pattern matches in first 8000 chars | `underlying_form = "Unknown"`, `underlying_object = None` |
| `underlying_form` is S-4, F-4, 20-F, 40-F, Form 10 | `underlying_object = None` (not delegated) |
| `RegistrationS1.from_filing` raises | `underlying_object = None` with debug log |
| `RegistrationS3.from_filing` raises | `underlying_object = None` with debug log |
| No 377-XXXXXX in header or HTML | `registration_number = None` |
| `filing.html()` returns empty string | Detection runs on empty string → "Unknown" |
| `amendment_number` not found in cover | `amendment_number = None` (does not affect `is_amendment`) |

## Access Patterns

- `filing.obj()` — dispatch entry point
- `DraftRegistrationStatement.from_filing(filing)` — direct construction
- `drs.underlying_form` — check which type before accessing `underlying_object`
- `drs.underlying_object` — always check `is not None` before field access
- `drs.registration_number` — 377-XXXXXX; needed for SEC correspondence tracking
- `drs.amendment_number` — 1-based amendment counter (separate from `is_amendment`)

## Notes

- DRS filings are visible on EDGAR before the company files a public registration; the company may never file publicly
- The 377-XXXXXX registration number is the confidential identifier; once public, a separate 333-XXXXXX is assigned
- `underlying_object` shares the same `Filing` object as `DraftRegistrationStatement`; accessing network properties on either object will make the same network calls
- `to_context` at standard/full detail includes `underlying_object.to_context('minimal')` when available
