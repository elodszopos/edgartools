# Form S-3 — Shelf Registration Statement

**SEC form codes**: S-3, S-3/A, S-3ASR, S-3ASR/A, S-3D, S-3DPOS, F-3, F-3/A, F-3ASR, F-3ASR/A
**Python class**: `RegistrationS3`
**Access**: `filing.obj()` -> `RegistrationS3`
**Source**: `edgar/offerings/registration_s3.py`

Note: S-3D and S-3DPOS (direct registration system variants) also dispatch to `RegistrationS3`.

## Complete Field Reference

### RegistrationS3-Specific Fields

#### Properties (immediate — set at construction)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing` | `Filing` | no | Underlying Filing object |
| `cover_page` | `S3CoverPage` | no | Parsed cover page (eager at construction) |
| `offering_type` | `S3OfferingType` | no | Classified offering type enum |
| `form` | `str` | no | Filing form string (e.g. "S-3", "S-3ASR", "F-3") |
| `company` | `str` | no | Company name from filing |
| `filing_date` | `str` | no | Filing date |
| `accession_number` | `str` | no | Accession number from `filing.accession_no` |
| `is_amendment` | `bool` | no | True if '/A' in form |
| `is_auto_shelf` | `bool` | no | True if 'ASR' in form or `offering_type == AUTO_SHELF` |
| `registration_number` | `Optional[str]` | no | 333-XXXXXX from cover page |
| `state_of_incorporation` | `Optional[str]` | no | State from cover page |
| `ein` | `Optional[str]` | no | Employer ID from cover page |
| `fee_table` | `RegistrationFeeTable \| None` | no | Exhibit 107 fee table (None if absent) |
| `total_offering` | `Optional[float]` | no | `fee_table.total_offering_amount` or None |
| `net_fee` | `Optional[float]` | no | `fee_table.net_fee_due` or None |
| `fee_deferred` | `bool` | no | True for S-3ASR (Rule 457(r) deferred fees) |
| `securities` | `List[FeeTableSecurity]` | no | `fee_table.securities` or `[]` |

#### Properties (cached_property — lazy, network on first access)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `takedowns` | `Optional[Filings]` | network | 424B1-B8 filings under this file number; None if no `registration_number` |
| `related_filings` | `Optional[Filings]` | network | All filings sharing registration file number |

**Key difference from S-1**: S-3 has NO `effective_date`, NO `selling_stockholders`, NO `dilution`, NO `capitalization`, NO `underwriting` table extraction. Financials are incorporated by reference from 10-K/10-Q.

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing: Filing` | `RegistrationS3` | Class method; primary entry point |
| `to_context` | `detail: str = 'standard'` | `str` | LLM-optimized context; detail: minimal/standard/full |
| `__rich__` | — | `Panel` | Rich terminal rendering |
| `__repr__` | — | `str` | Delegates to `repr_rich(__rich__())` |
| `__str__` | — | `str` | `RegistrationS3(form=..., company=..., offering_type=..., date=...)` |

## Nested Objects

### S3OfferingType (str, Enum)
Source: `edgar/offerings/registration_s3.py:42`

| Value | String | display_name |
|-------|--------|-------------|
| `UNIVERSAL_SHELF` | `"universal_shelf"` | Universal Shelf |
| `RESALE` | `"resale"` | Resale Registration |
| `DEBT` | `"debt"` | Debt Offering |
| `AUTO_SHELF` | `"auto_shelf"` | Automatic Shelf (S-3ASR) |
| `UNKNOWN` | `"unknown"` | Unknown |

Properties: `display_name -> str`

**Classification logic** (inline, not a separate file):
1. 'ASR' in form name → AUTO_SHELF
2. `fee_table.fee_deferred` is True → AUTO_SHELF
3. cover text contains 'resale' or 'selling stockholder' → RESALE
4. cover text has 'debt securities' but not equity → DEBT
5. Default → UNIVERSAL_SHELF

### S3CoverPage (Pydantic BaseModel)
Source: `edgar/offerings/registration_s3.py:65`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `company_name` | `str` | required | Issuer company name |
| `registration_number` | `Optional[str]` | None | 333-XXXXXX format |
| `state_of_incorporation` | `Optional[str]` | None | State/jurisdiction |
| `ein` | `Optional[str]` | None | Employer ID (XX-XXXXXXX) |
| `is_large_accelerated_filer` | `Optional[bool]` | None | Checkbox |
| `is_accelerated_filer` | `Optional[bool]` | None | Checkbox |
| `is_non_accelerated_filer` | `Optional[bool]` | None | Checkbox |
| `is_smaller_reporting_company` | `Optional[bool]` | None | Checkbox |
| `is_emerging_growth_company` | `Optional[bool]` | None | Checkbox |
| `is_rule_415` | `bool` | False | Rule 415 delayed/continuous offering |
| `is_rule_462b` | `bool` | False | Rule 462(b) automatic effectiveness |
| `is_rule_462e` | `bool` | False | Auto-shelf; set True if 'S-3ASR' in form |
| `confidence` | `str` | `"low"` | Extraction quality: low/medium/high |

**Difference from S1CoverPage**: no `sic_code` field, no `security_description` field.

**Confidence scoring**: high if ≥4 of {registration_number, state_of_incorporation, ein, is_large_accelerated, is_smaller_reporting} are non-None; medium if ≥2; low otherwise.

### RegistrationFeeTable, FeeTableSecurity
See `form-s1.md` — identical models shared from `edgar/offerings/prospectus.py:345,357`.

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.html()` returns None | `cover_page` has only `company_name`; confidence="low" |
| No Exhibit 107 attachment | `fee_table` is None; `fee_deferred` returns False |
| No `registration_number` on cover | `takedowns` and `related_filings` return None |
| `takedowns`/`related_filings` network error | Returns None with debug log; never raises |
| `from_filing` fee table extraction fails | `fee_table` silently set to None |
| HTML scanning fails in classifier | Defaults to UNIVERSAL_SHELF |

## Access Patterns

- `filing.obj()` — preferred entry point via dispatch
- `RegistrationS3.from_filing(filing)` — direct construction
- `s3.is_auto_shelf` — quick check for S-3ASR variant
- `s3.fee_deferred` — True signals Rule 457(r) deferred fee regime
- `s3.takedowns` — all 424B filings issued against this shelf
- `s3.cover_page.registration_number` — key for `ShelfLifecycle` navigation in prospectuses
