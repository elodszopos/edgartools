# Form S-1 — Registration Statement (IPO)

**SEC form codes**: S-1, S-1/A, F-1, F-1/A
**Python class**: `RegistrationS1`
**Access**: `filing.obj()` -> `RegistrationS1`
**Source**: `edgar/offerings/registration_s1.py`

## Complete Field Reference

### RegistrationS1-Specific Fields

#### Properties (immediate — set at construction)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing` | `Filing` | no | Underlying Filing object |
| `cover_page` | `S1CoverPage` | no | Parsed cover page (eager at construction) |
| `offering_type` | `S1OfferingType` | no | Classified offering type enum |
| `form` | `str` | no | Filing form string (e.g. "S-1", "S-1/A", "F-1") |
| `company` | `str` | no | Company name from filing |
| `filing_date` | `str` | no | Filing date |
| `accession_number` | `str` | no | Accession number from `filing.accession_no` |
| `is_amendment` | `bool` | no | True if '/A' in form |
| `registration_number` | `Optional[str]` | no | 333-XXXXXX from cover page |
| `state_of_incorporation` | `Optional[str]` | no | State from cover page |
| `sic_code` | `Optional[str]` | no | SIC code from cover page |
| `ein` | `Optional[str]` | no | Employer ID number from cover page |
| `fee_table` | `RegistrationFeeTable \| None` | no | Exhibit 107 fee table (None if absent) |
| `total_offering` | `Optional[float]` | no | `fee_table.total_offering_amount` or None |
| `net_fee` | `Optional[float]` | no | `fee_table.net_fee_due` or None |
| `securities` | `List[FeeTableSecurity]` | no | `fee_table.securities` or `[]` |

#### Properties (cached_property — lazy, network on first access)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `selling_stockholders` | `Optional[SellingStockholdersData]` | cached | Extracted from parsed document; None if no table found |
| `dilution` | `Optional[DilutionData]` | cached | Per-share dilution table; None if not present |
| `capitalization` | `Optional[CapitalizationData]` | cached | Actual vs. as-adjusted cap table; None if not present |
| `underwriting` | `Optional[UnderwritingInfo]` | cached | Underwriter syndicate info; None if no table |
| `takedowns` | `Optional[Filings]` | network | 424B1-B8 filings under this file number; None if no `registration_number` |
| `related_filings` | `Optional[Filings]` | network | All filings sharing registration file number |
| `effective_date` | `Optional[str]` | network | Date of EFFECT filing; triggers `related_filings` |
| `is_effective` | `bool` | network | True if `effective_date` is not None |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing: Filing` | `RegistrationS1` | Class method; primary entry point |
| `to_context` | `detail: str = 'standard'` | `str` | LLM-optimized context; detail: minimal/standard/full |
| `__rich__` | — | `Panel` | Rich terminal rendering |
| `__repr__` | — | `str` | Delegates to `repr_rich(__rich__())` |
| `__str__` | — | `str` | `RegistrationS1(form=..., company=..., offering_type=..., date=...)` |

## Nested Objects

### S1OfferingType (str, Enum)
Source: `edgar/offerings/registration_s1.py:47`

| Value | String | display_name |
|-------|--------|-------------|
| `IPO` | `"ipo"` | Initial Public Offering |
| `SPAC` | `"spac"` | SPAC IPO |
| `RESALE` | `"resale"` | Resale Registration |
| `DEBT` | `"debt"` | Debt Offering |
| `FOLLOW_ON` | `"follow_on"` | Follow-On Offering |
| `UNKNOWN` | `"unknown"` | Unknown |

Properties: `display_name -> str`

### S1CoverPage (Pydantic BaseModel)
Source: `edgar/offerings/registration_s1.py:73`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `company_name` | `str` | required | Issuer company name |
| `registration_number` | `Optional[str]` | None | 333-XXXXXX format |
| `state_of_incorporation` | `Optional[str]` | None | State/jurisdiction |
| `sic_code` | `Optional[str]` | None | SIC code |
| `ein` | `Optional[str]` | None | Employer ID number (XX-XXXXXXX) |
| `is_large_accelerated_filer` | `Optional[bool]` | None | Checkbox: large accelerated filer |
| `is_accelerated_filer` | `Optional[bool]` | None | Checkbox: accelerated filer |
| `is_non_accelerated_filer` | `Optional[bool]` | None | Checkbox: non-accelerated filer |
| `is_smaller_reporting_company` | `Optional[bool]` | None | Checkbox: SRC |
| `is_emerging_growth_company` | `Optional[bool]` | None | Checkbox: EGC |
| `is_rule_415` | `bool` | False | Rule 415 delayed/continuous offering |
| `is_rule_462b` | `bool` | False | Rule 462(b) automatic effectiveness |
| `is_rule_462e` | `bool` | False | Rule 462(e) auto-shelf |
| `security_description` | `Optional[str]` | None | Security type description from cover |
| `confidence` | `str` | `"low"` | Extraction quality: low/medium/high |

### RegistrationFeeTable (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:357`

| Field | Type | Description |
|-------|------|-------------|
| `total_offering_amount` | `Optional[float]` | Total registered amount in dollars |
| `net_fee_due` | `Optional[float]` | Net SEC registration fee |
| `total_fees_previously_paid` | `Optional[float]` | Carry-forward fee credits |
| `securities` | `List[FeeTableSecurity]` | Per-security breakdowns |
| `carry_forwards` | `List[FeeTableSecurity]` | Carry-forward securities |
| `has_carry_forward` | `bool` | True if carry-forward entries present |
| `fee_deferred` | `bool` | True when all securities use Rule 457(r) |
| `exhibit_url` | `Optional[str]` | URL to EX-FILING FEES attachment |

### FeeTableSecurity (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:345`

| Field | Type | Description |
|-------|------|-------------|
| `security_type` | `Optional[str]` | Category (e.g., "Equity") |
| `security_title` | `Optional[str]` | Description (e.g., "Common Stock") |
| `fee_rule` | `Optional[str]` | Rule applied (e.g., "457(c)") |
| `amount_registered` | `Optional[str]` | Number of shares/units as raw string |
| `price_per_unit` | `Optional[float]` | Price per share/unit |
| `max_aggregate_amount` | `Optional[float]` | Maximum aggregate offering amount |
| `fee_rate` | `Optional[float]` | Fee rate applied |
| `fee_amount` | `Optional[float]` | Fee for this security |

### SellingStockholdersData (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:228`

| Field | Type | Description |
|-------|------|-------------|
| `stockholders` | `List[SellingStockholderEntry]` | Individual rows |
| `total_shares_offered` | `Optional[str]` | Total row value (raw string) |
| `notes` | `Optional[str]` | Footnotes from table |

Properties: `count -> int`, `is_populated -> bool`

Method: `to_dataframe() -> pd.DataFrame`

### SellingStockholderEntry (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:187`

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Stockholder name |
| `shares_before_offering` | `Optional[str]` | Raw string |
| `pct_before_offering` | `Optional[str]` | Raw string |
| `shares_offered` | `Optional[str]` | Raw string |
| `shares_after_offering` | `Optional[str]` | Raw string |
| `pct_after_offering` | `Optional[str]` | Raw string |
| `warrants_or_convertible` | `Optional[str]` | Raw string |

Numeric properties (return None on parse failure):
`shares_before -> Optional[int]`, `shares -> Optional[int]`, `shares_after -> Optional[int]`, `pct_before -> Optional[float]`, `pct_after -> Optional[float]`, `warrants -> Optional[int]`

### DilutionData (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:300`

| Field | Type | Description |
|-------|------|-------------|
| `public_offering_price` | `Optional[str]` | Raw string |
| `ntbv_before_offering` | `Optional[str]` | Net tangible book value before |
| `ntbv_increase` | `Optional[str]` | NTBV increase from offering |
| `ntbv_after_offering` | `Optional[str]` | NTBV after offering |
| `dilution_per_share` | `Optional[str]` | Dilution per share (raw) |
| `dilution_percentage` | `Optional[str]` | Dilution % (raw) |
| `shares_outstanding_before` | `Optional[str]` | Shares before (raw) |
| `shares_outstanding_after` | `Optional[str]` | Shares after (raw) |

### CapitalizationData (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:311`

| Field | Type | Description |
|-------|------|-------------|
| `rows` | `List[dict]` | All extracted rows as key-value dicts |
| `cash_actual` | `Optional[str]` | Cash actual (raw) |
| `cash_as_adjusted` | `Optional[str]` | Cash as-adjusted (raw) |
| `total_stockholders_equity_actual` | `Optional[str]` | SE actual (raw) |
| `total_stockholders_equity_as_adjusted` | `Optional[str]` | SE as-adjusted (raw) |
| `total_capitalization_actual` | `Optional[str]` | Total cap actual (raw) |
| `total_capitalization_as_adjusted` | `Optional[str]` | Total cap as-adjusted (raw) |

### UnderwritingInfo (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:264`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `underwriters` | `List[UnderwriterEntry]` | `[]` | Syndicate members |
| `fee_type` | `str` | `"underwriting_discount"` | `"underwriting_discount"` or `"placement_agent_fees"` |
| `overallotment_shares` | `Optional[str]` | None | Greenshoe shares (raw) |
| `overallotment_amount` | `Optional[str]` | None | Greenshoe dollar amount (raw) |
| `lock_up_days` | `Optional[int]` | None | Lock-up period |

Properties: `is_underwritten -> bool`, `lead_manager -> Optional[str]`

### UnderwriterEntry (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:258`

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Underwriter or placement agent name |
| `shares_allocated` | `Optional[str]` | Shares allocated (raw) |
| `dollar_amount` | `Optional[str]` | Dollar allocation (raw) |

## DataFrame Schemas

### selling_stockholders.to_dataframe() columns

| Column | Type | Description |
|--------|------|-------------|
| `name` | `str` | Stockholder name |
| `shares_before` | `Optional[int]` | Shares before offering |
| `pct_before` | `Optional[float]` | % owned before |
| `shares_offered` | `Optional[int]` | Shares offered |
| `shares_after` | `Optional[int]` | Shares after offering |
| `pct_after` | `Optional[float]` | % owned after |
| `warrants` | `Optional[int]` | Warrants or convertible shares |

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.html()` returns None | `cover_page` has only `company_name`; confidence="low" |
| No Exhibit 107 attachment | `fee_table` is None; `total_offering`, `net_fee`, `securities` return None/[] |
| No `registration_number` on cover | `takedowns` returns None; `related_filings` returns None; `effective_date` returns None |
| `filing.parse()` fails | `_document` is None; all table properties return None |
| No dilution/cap/selling table found | Respective property returns None (not raised) |
| `takedowns`/`related_filings` network error | Returns None with debug log; never raises |
| `from_filing` fee table extraction fails | `fee_table` silently set to None |

## Access Patterns

- `filing.obj()` — preferred entry point via dispatch
- `RegistrationS1.from_filing(filing)` — direct construction
- `s1.cover_page.registration_number` — 333-XXXXXX file number key for lifecycle navigation
- `s1.takedowns` — forward navigation to all 424B filings under this registration
- `s1.effective_date` — requires `related_filings` network call; may be slow
- `s1.selling_stockholders.to_dataframe()` — tabular format for resale registrations
