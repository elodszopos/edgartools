# Form 424B — Prospectus

**SEC form codes**: 424B1, 424B2, 424B3, 424B4, 424B5, 424B7, 424B8 (and /A amendments)
**Python class**: `Prospectus424B`
**Access**: `filing.obj()` -> `Prospectus424B`
**Source**: `edgar/offerings/prospectus.py`

## Variant Guide

| Form | Primary Use |
|------|------------|
| 424B1 | Exchange offers, IPOs (Rule 424(b)(1)) |
| 424B2 | Structured notes, bank debt (CUSIP-level, large banks) |
| 424B3 | Resale prospectuses, PIPE resales, rights offerings |
| 424B4 | Final priced prospectuses, IPOs, shelf takedowns |
| 424B5 | Shelf takedowns, ATM, firm commitment, PIPE |
| 424B7 | WKSI selling stockholder base updates (hardcoded to `base_prospectus_update`) |
| 424B8 | Prospectus supplements |

## Complete Field Reference

### Properties (immediate — set at construction)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing` | `Filing` | no | Underlying Filing object |
| `cover_page` | `CoverPageData` | no | Parsed cover page (eager, from `filing.parse()`) |
| `offering_type` | `OfferingType` | no | Classified offering type enum |
| `form` | `str` | no | Filing form string (e.g. "424B4", "424B5/A") |
| `variant` | `str` | no | Form without '/A' suffix |
| `company` | `str` | no | Company name from filing |
| `filing_date` | `str` | no | Filing date |
| `accession_number` | `str` | no | From `filing.accession_no` |
| `is_amendment` | `bool` | no | True if '/A' in form |
| `amendment_number` | `Optional[int]` | no | Parsed from "Amendment No. X" in form name |
| `registration_number` | `Optional[str]` | no | 333-XXXXXX from cover page |
| `is_preliminary` | `bool` | no | From `cover_page.is_preliminary` |
| `is_atm` | `bool` | no | From `cover_page.is_atm` |
| `is_supplement` | `bool` | no | From `cover_page.is_supplement` |
| `ticker` | `Optional[str]` | no | Exchange ticker from cover page |
| `offering_amount` | `Optional[str]` | no | Raw string from cover page |
| `offering_price` | `Optional[str]` | no | Raw string from cover page |

### Properties (cached_property — lazy, parse/network on first access)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `sections` | `Sections` | cached | Document sections dict (`.text()`, `.tables()` per section); returns empty `Sections({})` if parse failed |
| `pricing` | `Optional[PricingData]` | cached | Pricing table; None for ATM and resale |
| `offering_terms` | `Optional[OfferingTerms]` | cached | Key-value terms from "The Offering" section |
| `selling_stockholders` | `Optional[SellingStockholdersData]` | cached | Merged from all selling stockholder tables |
| `structured_note_terms` | `Optional[StructuredNoteTerms]` | cached | Merged from all key_terms tables (424B2 only) |
| `dilution` | `Optional[DilutionData]` | cached | Per-share dilution table |
| `capitalization` | `Optional[CapitalizationData]` | cached | Actual vs. as-adjusted cap table |
| `underwriting` | `Optional[UnderwritingInfo]` | cached | Table-first, falls back to text extraction |
| `filing_fees` | `FilingFeesData` | cached | XBRL filing fees exhibit; always returns object (never None; check `has_exhibit`) |
| `lifecycle` | `Optional[ShelfLifecycle]` | network | Shelf position, expiry, takedown cadence; None if related filings unavailable |
| `shelf_registration` | `Optional[Filing]` | network | S-3/F-3/S-1 filing; delegates to `lifecycle` |
| `related_filings` | `Optional[Filings]` | network | All filings under same file number; delegates to `lifecycle` |
| `related_8k` | `Optional[Filing]` | network | 8-K filed same day; delegates to `lifecycle` |
| `deal` | `Deal` | cached | Always returns `Deal` (never None); individual fields may be None |

### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing: Filing` | `Prospectus424B` | Class method; calls `filing.parse()` once; eager cover + classification |
| `to_context` | `detail: str = 'standard'` | `str` | LLM-optimized; detail: minimal/standard/full |
| `__rich__` | — | `Panel` | Rich terminal rendering with cover, pricing, underwriting |
| `__repr__` | — | `str` | Delegates to `repr_rich(__rich__())` |
| `__str__` | — | `str` | `Prospectus424B(form=..., company=..., offering_type=..., date=...)` |

## Nested Objects

### OfferingType (str, Enum)
Source: `edgar/offerings/prospectus.py:41`

| Value | String | display_name |
|-------|--------|-------------|
| `FIRM_COMMITMENT` | `"firm_commitment"` | Firm Commitment |
| `ATM` | `"atm"` | At-the-Market |
| `BEST_EFFORTS` | `"best_efforts"` | Best Efforts / PIPE |
| `PIPE_RESALE` | `"pipe_resale"` | Resale (PIPE) |
| `RIGHTS_OFFERING` | `"rights_offering"` | Rights Offering |
| `EXCHANGE_OFFER` | `"exchange_offer"` | Exchange Offer |
| `STRUCTURED_NOTE` | `"structured_note"` | Structured Note |
| `DEBT_OFFERING` | `"debt_offering"` | Debt Offering |
| `BASE_PROSPECTUS_UPDATE` | `"base_prospectus_update"` | Base Prospectus Update |
| `UNKNOWN` | `"unknown"` | Unknown |

Properties:
- `is_equity -> bool` — True for FIRM_COMMITMENT, ATM, BEST_EFFORTS, PIPE_RESALE, RIGHTS_OFFERING
- `has_fixed_price -> bool` — True for FIRM_COMMITMENT, BEST_EFFORTS, RIGHTS_OFFERING
- `has_selling_stockholders -> bool` — True for PIPE_RESALE, BASE_PROSPECTUS_UPDATE

**Classifier notes**: 424B7 is always hardcoded to `BASE_PROSPECTUS_UPDATE`. Structured notes detected first via `pricing_supplement` in first 3000 chars. Classifier accuracy: 12/12 validation set.

### CoverPageData (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:99`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `company_name` | `str` | required | Issuer name |
| `registration_number` | `Optional[str]` | None | 333-XXXXXX; used for lifecycle lookup |
| `is_supplement` | `bool` | False | True if "supplement" in cover |
| `is_preliminary` | `bool` | False | True if "preliminary" in cover |
| `is_atm` | `bool` | False | True if ATM-indicator found |
| `rule_number` | `Optional[str]` | None | Rule cited (e.g., "424(b)(5)") |
| `security_description` | `Optional[str]` | None | Security type description |
| `offering_amount` | `Optional[str]` | None | Raw string; can be sentinel like "at-the-market" |
| `offering_price` | `Optional[str]` | None | Raw string; can be "market-price" |
| `exchange_ticker` | `Optional[str]` | None | Exchange ticker symbol |
| `base_prospectus_date` | `Optional[str]` | None | Date of base prospectus (for supplements) |

Computed properties:
- `offering_amount_float -> Optional[float]` — None for sentinel strings ("exchange-offer", "at-the-market", "preliminary-TBD", "market-price"); handles "$1.2 billion" etc.
- `offering_price_float -> Optional[float]` — None if starts with "at", "exchange", "preliminary", "market"

### PricingData (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:170`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `columns` | `List[PricingColumnData]` | `[]` | Per-column pricing data |
| `fee_type` | `Optional[str]` | None | "underwriting_discount" or "placement_agent_fees" |
| `is_percentage_price` | `bool` | False | True for percentage-based pricing |
| `raw_rows` | `List[List[str]]` | `[]` | Raw extracted table rows |

### PricingColumnData (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:163`

| Field | Type | Description |
|-------|------|-------------|
| `column_label` | `Optional[str]` | Column header (e.g., "Per Share", "Total") |
| `offering_price` | `Optional[str]` | Price or aggregate amount (raw) |
| `fee_or_discount` | `Optional[str]` | Underwriting discount/placement fee (raw) |
| `proceeds` | `Optional[str]` | Net proceeds (raw) |

### OfferingTerms (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:177`

| Field | Type | Description |
|-------|------|-------------|
| `shares_offered` | `Optional[str]` | Shares offered (raw) |
| `pre_funded_warrants_offered` | `Optional[str]` | Pre-funded warrants (raw) |
| `warrants_offered` | `Optional[str]` | Warrants offered (raw) |
| `use_of_proceeds_summary` | `Optional[str]` | Brief use of proceeds text |
| `trading_symbol` | `Optional[str]` | Trading symbol |
| `listing_exchange` | `Optional[str]` | Exchange name |
| `additional_terms` | `dict` | Any other key-value pairs extracted |

### SellingStockholdersData, SellingStockholderEntry
See `form-s1.md` — identical models. Note: `Prospectus424B.selling_stockholders` merges multiple tables (e.g., common shares + warrants tables).

### StructuredNoteTerms (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:280`
Primary use: 424B2 structured note supplements.

| Field | Type | Description |
|-------|------|-------------|
| `issuer` | `Optional[str]` | Note issuer |
| `guarantor` | `Optional[str]` | Guarantor entity |
| `cusip` | `Optional[str]` | CUSIP number |
| `pricing_date` | `Optional[str]` | Pricing date (raw) |
| `issue_date` | `Optional[str]` | Issue date (raw) |
| `maturity_date` | `Optional[str]` | Maturity date (raw) |
| `underlying` | `Optional[str]` | Reference asset/index |
| `denominations` | `Optional[str]` | Minimum denomination |
| `term` | `Optional[str]` | Term length |
| `principal_amount` | `Optional[str]` | Principal/aggregate offering amount |
| `upside_participation_rate` | `Optional[str]` | Upside participation % |
| `max_return` | `Optional[str]` | Maximum return cap |
| `threshold_value` | `Optional[str]` | Barrier or threshold level |
| `buffer_amount` | `Optional[str]` | Buffer/barrier % |
| `coupon_rate` | `Optional[str]` | Coupon rate |
| `coupon_frequency` | `Optional[str]` | Payment frequency |
| `additional_terms` | `dict` | Any other extracted key-value pairs |

Note: `structured_note_terms` merges multiple key_terms tables; later tables fill None fields from earlier ones; additional_terms accumulate across all tables.

### DilutionData, CapitalizationData, UnderwritingInfo, UnderwriterEntry
See `form-s1.md` — identical models.

### FilingFeesData (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:330`
Coverage: ~43% of 424B2, ~23% of 424B5, ~7% of 424B3; 424B1 and 424B4 have 0% coverage. Available only from 2022+ (SEC Rule 408).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `has_exhibit` | `bool` | False | False if no EX-FILING FEES exhibit found |
| `exhibit_url` | `Optional[str]` | None | URL to iXBRL exhibit |
| `form_type` | `Optional[str]` | None | Form type from XBRL |
| `registration_file_number` | `Optional[str]` | None | File number from XBRL |
| `total_offering_amount` | `Optional[str]` | None | Total aggregate (raw) |
| `total_fee_amount` | `Optional[str]` | None | Total SEC fee (raw) |
| `offering_rows` | `List[FilingFeesRow]` | `[]` | Per-security rows |
| `is_final_prospectus` | `bool` | True | From `ffd:FnlPrspctsFlg` XBRL element |

### FilingFeesRow (Pydantic BaseModel)
Source: `edgar/offerings/prospectus.py:321`

| Field | Type | Description |
|-------|------|-------------|
| `security_type` | `Optional[str]` | Security category |
| `security_title` | `Optional[str]` | Security description |
| `max_aggregate_offering_price` | `Optional[str]` | Max aggregate (raw) |
| `fee_rate` | `Optional[str]` | SEC fee rate (raw) |
| `fee_amount` | `Optional[str]` | Fee amount (raw) |
| `fee_rule` | `Optional[str]` | Applicable fee rule |

### RegistrationFeeTable, FeeTableSecurity
See `form-s1.md`. Used by `ShelfLifecycle.shelf_capacity`.

### ShelfLifecycle
Source: `edgar/offerings/prospectus.py:394`
Constructed lazily on `Prospectus424B.lifecycle` access. All properties are `cached_property`.

| Field / Property | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing` | `Filing` | no | The current 424B filing |
| `filings` | `Filings` | no | Full related filings set under this shelf |
| `shelf_registration` | `Optional[Filing]` | cached | S-3/F-3/S-1 that started the shelf |
| `shelf_filed_date` | `Optional[str]` | cached | Date the shelf was filed (string) |
| `effective_date` | `Optional[str]` | cached | Date shelf was declared effective (string) |
| `shelf_expires` | `Optional[date]` | cached | Filed date + 3 years (Feb 29 → Feb 28 fallback) |
| `days_to_expiry` | `Optional[int]` | cached | Remaining days; negative if expired |
| `review_period_days` | `Optional[int]` | cached | Days from filed to effective |
| `takedowns` | `List[Filing]` | cached | All 424B* takedowns in chronological order |
| `total_takedowns` | `int` | cached | Count of takedowns |
| `takedown_number` | `Optional[int]` | cached | 1-based position of current filing |
| `is_latest_takedown` | `bool` | cached | True if current == last takedown |
| `avg_days_between_takedowns` | `Optional[float]` | cached | Average cadence; None if fewer than 2 takedowns |
| `related_8k` | `Optional[Filing]` | cached | 8-K filed same day as current |
| `shelf_capacity` | `Optional[RegistrationFeeTable]` | cached | Fee table from shelf registration; triggers network |
| `total_offering_capacity` | `Optional[float]` | cached | `shelf_capacity.total_offering_amount` |

Methods: `to_context(detail='standard') -> str`, `__rich__() -> Panel`, `__repr__() -> str`, `__str__() -> str`

### Deal
Source: `edgar/offerings/prospectus.py:784`
Triangulates across `cover_page`, `pricing`, `offering_terms`, `underwriting`, `dilution`. Always returned (never None). All properties are `cached_property`.

| Property | Type | Triangulation Order | Description |
|----------|------|---------------------|-------------|
| `price` | `Optional[float]` | cover_page → pricing per-unit | Per-unit offering price |
| `shares` | `Optional[int]` | offering_terms → gross/price | Number of shares offered |
| `gross_proceeds` | `Optional[float]` | cover_page → pricing total → price×shares | Gross offering amount |
| `net_proceeds` | `Optional[float]` | pricing total proceeds → gross-fees | Net after underwriting |
| `security_type` | `Optional[str]` | cover_page | Security description |
| `offering_type` | `OfferingType` | prospectus | Offering type enum |
| `is_atm` | `bool` | prospectus | ATM flag |
| `fee_per_share` | `Optional[float]` | pricing per-unit fee column | Per-unit underwriting fee |
| `total_fees` | `Optional[float]` | pricing total fee → fee_per_share×shares | Total underwriting fees |
| `discount_rate` | `Optional[float]` | fee_per_share / price | Fee as fraction |
| `fee_type` | `Optional[str]` | underwriting → pricing | "underwriting_discount" or "placement_agent_fees" |
| `lead_bookrunner` | `Optional[str]` | underwriting.lead_manager | First underwriter name |
| `underwriter_count` | `int` | underwriting | Syndicate size |
| `dilution_per_share` | `Optional[float]` | dilution | Dilution per share (parsed float) |
| `dilution_pct` | `Optional[float]` | dilution | Dilution percentage (parsed float) |
| `shares_before` | `Optional[int]` | dilution | Shares outstanding before |
| `shares_after` | `Optional[int]` | dilution | Shares outstanding after |
| `ntbv_before` | `Optional[float]` | dilution | NTBV per share before |
| `ntbv_after` | `Optional[float]` | dilution | NTBV per share after |

Methods:
- `to_dict() -> dict` — all non-None computed values as flat dict; OfferingType values converted to string
- `to_context(detail='standard') -> str` — LLM-optimized deal summary
- `__rich__() -> Panel`, `__repr__() -> str`, `__str__() -> str`

## DataFrame Schemas

### selling_stockholders.to_dataframe() columns

| Column | Type | Description |
|--------|------|-------------|
| `name` | `str` | Stockholder name |
| `shares_before` | `Optional[int]` | Shares before offering |
| `pct_before` | `Optional[float]` | % before |
| `shares_offered` | `Optional[int]` | Shares offered |
| `shares_after` | `Optional[int]` | Shares after |
| `pct_after` | `Optional[float]` | % after |
| `warrants` | `Optional[int]` | Warrants/convertibles |

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.parse()` fails | `_document` is None; all table properties return None; `sections` returns empty `Sections({})` |
| 424B7 form | `offering_type` hardcoded to `BASE_PROSPECTUS_UPDATE` regardless of content |
| No pricing table found | `pricing` returns None; affects `deal.price`, `deal.net_proceeds` |
| No key_terms table (424B2) | `structured_note_terms` returns None |
| `cover_page.offering_amount` is sentinel | `offering_amount_float` returns None |
| No EX-FILING FEES exhibit | `filing_fees.has_exhibit` is False; all other fields are None/empty |
| `cover_page.registration_number` is None | `lifecycle` falls back to `filing.related_filings()`; may still return None |
| `lifecycle` network fails | Returns None with debug log; `deal`, `shelf_registration`, `related_8k` also None |
| `underwriting` tables empty | Falls back to text extraction from cover; returns None if both fail |
| `selling_stockholders` second table | Merged via `extend`; if `total_shares_offered` absent in first, taken from second |

## Access Patterns

- `filing.obj()` — dispatch entry point
- `Prospectus424B.from_filing(filing)` — direct construction
- `prospectus.deal` — always safe to access; individual deal fields may be None
- `prospectus.deal.to_dict()` — flat dict of all available metrics
- `prospectus.lifecycle.takedown_number` — position in shelf sequence
- `prospectus.lifecycle.shelf_expires` — date object, or None
- `prospectus.structured_note_terms` — 424B2 only; CUSIP, maturity, underlying
- `prospectus.filing_fees.has_exhibit` — check before accessing fee rows
- `prospectus.sections.get('use_of_proceeds')` — section-level text access
