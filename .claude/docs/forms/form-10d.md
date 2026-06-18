# Form 10-D — ABS Distribution Report

**SEC form codes**: 10-D, 10-D/A
**Python class**: `TenD` (no base class)
**Access**: `filing.obj()` → `TenD` (EX-102 guard is in `obj()` dispatch in `edgar/__init__.py`; `TenD` itself accepts any 10-D)
**Base fields**: See `_base-filing.md`
**Source**: `edgar/abs/ten_d.py`, `edgar/abs/cmbs.py`, `edgar/abs/abs_ee.py`

## Complete Field Reference

### From Filing (inherited)
See `_base-filing.md`

### TenD-Specific Fields

#### Immediate Properties (no lazy load)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing` | `Filing` | no | Underlying Filing object |
| `form` | `str` | no | `'10-D'` or `'10-D/A'` from `_filing.form` |
| `company` | `str` | no | Filer company name from `_filing.company` |
| `filing_date` | `date` | no | Filing date from `_filing.filing_date` |
| `accession_number` | `str` | no | Accession number from `_filing.accession_number` |

#### Lazy Properties (parsed on first access via `_ensure_header_parsed()`)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `issuing_entity` | `Optional[ABSEntity]` | lazy | ABS issuing entity parsed from HTML header |
| `depositor` | `Optional[ABSEntity]` | lazy | Depositor parsed from HTML header |
| `sponsors` | `List[ABSEntity]` | lazy | Sponsor list parsed from HTML header |
| `distribution_period` | `Optional[DistributionPeriod]` | lazy | Distribution date range from HTML header |
| `security_classes` | `List[str]` | lazy | Security class names from "title of class" table |

#### Cached Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `abs_type` | `ABSType` | cached | ABS type detection: CMBS if EX-102 present, else keyword match on company/issuer name |
| `has_asset_data` | `bool` | cached | True when EX-102 attachment found |
| `asset_data` | `Optional[CMBSAssetData]` | cached | CMBS asset parser; None if not CMBS or EX-102 absent |

#### Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `loans` | `pd.DataFrame` | no | Convenience: `asset_data.loans` or empty DataFrame |
| `properties` | `pd.DataFrame` | no | Convenience: `asset_data.properties` or empty DataFrame |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `__init__` | `filing` | — | Validates form in `('10-D', '10-D/A')`, raises `ValueError` otherwise |
| `to_context` | `detail: str = 'standard'` | `str` | AI context. `'minimal'`: issuer + date + abs_type. `'standard'`: + depositor + sponsors + security classes. `'full'`: + all security class names. |

## Nested Objects

### ABSType (Enum)

| Value | Detection Logic |
|-------|----------------|
| `CMBS` | EX-102 attachment present (checked first, before name keywords) |
| `AUTO` | Company/issuer name contains auto/vehicle/car/motor/fleet/lease receivable |
| `CREDIT_CARD` | Contains credit card/card receivable/charge card |
| `STUDENT_LOAN` | Contains student loan/education loan |
| `RMBS` | Contains mortgage/rmbs/residential |
| `UTILITY` | Contains utility/restoration/securitization funding/ratepayer |
| `OTHER` | Fallback when no keywords match |

### ABSEntity (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Entity name (issuer, depositor, or sponsor) |
| `cik` | `Optional[str]` | EDGAR CIK (leading zeros stripped) |
| `file_number` | `Optional[str]` | Commission file number |

### DistributionPeriod (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `start_date` | `Optional[date]` | Distribution period start |
| `end_date` | `Optional[date]` | Distribution period end |

`__str__` returns `"Mon DD, YYYY to Mon DD, YYYY"` format when both dates are present.

### CMBSAssetData (`edgar/abs/cmbs.py`)

Initialized with raw EX-102 XML string. XML namespace: `http://www.sec.gov/edgar/document/absee/cmbs/assetdata`.

| Property/Method | Returns | Description |
|-----------------|---------|-------------|
| `loans` | `pd.DataFrame` | Loan-level data (cached_property) |
| `properties` | `pd.DataFrame` | Property-level data (cached_property) |
| `summary()` | `CMBSSummary` | Aggregate pool statistics |
| `__len__()` | `int` | Number of loans |

## DataFrame Schemas

### `loans` columns

| Column | Type | Description |
|--------|------|-------------|
| `loan_id` | `str` | Prospectus loan identifier (`assetNumber`) |
| `loan_id_type` | `str` | Loan ID type code (`assetTypeNumber`) |
| `period_start` | `date` | Reporting period start |
| `period_end` | `date` | Reporting period end |
| `originator` | `str` | Loan originator name |
| `origination_date` | `date` | Loan origination date |
| `original_amount` | `float` | Original loan amount |
| `original_term_months` | `int` | Original term in months |
| `maturity_date` | `date` | Loan maturity date |
| `original_rate` | `float` | Original interest rate |
| `securitization_rate` | `float` | Interest rate at securitization |
| `accrual_method` | `str` | Interest accrual method code |
| `rate_type` | `str` | Interest rate type code |
| `io_term_months` | `int` | Interest-only term months |
| `first_payment_date` | `date` | First payment due date |
| `lien_position` | `str` | Lien position code |
| `loan_structure` | `str` | Loan structure code |
| `payment_type` | `str` | Payment type code |
| `scheduled_balance` | `float` | Scheduled principal balance at securitization |
| `payment_frequency` | `str` | Payment frequency code |
| `num_properties_securitization` | `int` | Number of properties at securitization |
| `num_properties` | `int` | Current number of properties |
| `grace_days` | `int` | Grace period days |
| `is_interest_only` | `bool` | Interest-only indicator |
| `is_balloon` | `bool` | Balloon payment indicator |
| `has_prepayment_premium` | `bool` | Prepayment premium indicator |
| `has_negative_amortization` | `bool` | Negative amortization indicator |
| `is_modified` | `bool` | Loan modification indicator |
| `lockout_end_date` | `date` | Prepayment lockout end date |
| `yield_maintenance_end_date` | `date` | Yield maintenance end date |
| `prepayment_premium_end_date` | `date` | Prepayment premium end date |
| `period_begin_balance` | `float` | Beginning of period schedule balance |
| `scheduled_pi_due` | `float` | Scheduled principal + interest due |
| `current_rate` | `float` | Current interest rate |
| `servicer_fee_rate` | `float` | Servicer/trustee fee rate |
| `scheduled_interest` | `float` | Scheduled interest amount |
| `scheduled_principal` | `float` | Scheduled principal amount |
| `unscheduled_principal` | `float` | Unscheduled principal collected |
| `actual_balance` | `float` | Actual balance at period end |
| `scheduled_end_balance` | `float` | Scheduled balance at period end |
| `paid_through_date` | `date` | Paid through date |
| `servicing_advance_method` | `str` | Servicing advance method code |
| `pi_advances_outstanding` | `float` | P&I advances outstanding |
| `ti_advances_outstanding` | `float` | Tax/insurance advances outstanding |
| `other_advances_outstanding` | `float` | Other advances outstanding |
| `payment_status` | `str` | Payment status code (0=current) |
| `primary_servicer` | `str` | Primary servicer name |
| `subject_to_demand` | `bool` | Asset subject to demand indicator |

### `properties` columns

| Column | Type | Description |
|--------|------|-------------|
| `loan_id` | `str` | Associated loan ID (from parent asset) |
| `name` | `str` | Property name |
| `address` | `str` | Street address |
| `city` | `str` | City |
| `state` | `str` | State code |
| `zip` | `str` | ZIP code |
| `county` | `str` | County |
| `property_type` | `str` | Property type code (MF/OF/RT/IN/MH/SS/LO/WH/SE/HC/SB) |
| `units` | `int` | Number of units/beds/rooms |
| `units_securitization` | `int` | Units at securitization |
| `sqft` | `int` | Net rentable square feet |
| `sqft_securitization` | `int` | Square feet at securitization |
| `year_built` | `int` | Year property was built |
| `year_renovated` | `int` | Year last renovated |
| `valuation` | `float` | Property valuation at securitization |
| `valuation_source` | `str` | Valuation source code |
| `valuation_date` | `date` | Date of securitization valuation |
| `occupancy_securitization` | `float` | Physical occupancy at securitization |
| `occupancy_current` | `float` | Most recent physical occupancy |
| `status` | `str` | Property status code |
| `defeased_status` | `str` | Defeasance status code |
| `tenant_1_name` | `str` | Largest tenant name |
| `tenant_1_sqft` | `int` | Largest tenant square feet |
| `tenant_1_lease_exp` | `date` | Largest tenant lease expiration |
| `tenant_2_name` | `str` | Second largest tenant name |
| `tenant_2_sqft` | `int` | Second largest tenant square feet |
| `tenant_2_lease_exp` | `date` | Second largest tenant lease expiration |
| `tenant_3_name` | `str` | Third largest tenant name |
| `tenant_3_sqft` | `int` | Third largest tenant square feet |
| `tenant_3_lease_exp` | `date` | Third largest tenant lease expiration |
| `financials_date_securitization` | `date` | Financial statement date at securitization |
| `financials_start_date` | `date` | Most recent financials start date |
| `financials_end_date` | `date` | Most recent financials end date |
| `revenue_securitization` | `float` | Revenue at securitization |
| `revenue_current` | `float` | Most recent revenue |
| `opex_securitization` | `float` | Operating expenses at securitization |
| `opex_current` | `float` | Most recent operating expenses |
| `noi_securitization` | `float` | NOI at securitization |
| `noi_current` | `float` | Most recent NOI |
| `ncf_securitization` | `float` | Net cash flow at securitization |
| `ncf_current` | `float` | Most recent net cash flow |
| `debt_service_current` | `float` | Most recent debt service |
| `dscr_noi_securitization` | `float` | DSCR (NOI) at securitization |
| `dscr_noi_current` | `float` | Most recent DSCR (NOI) |
| `dscr_ncf_securitization` | `float` | DSCR (NCF) at securitization |
| `dscr_ncf_current` | `float` | Most recent DSCR (NCF) |

### `CMBSSummary` fields

| Field | Type | Description |
|-------|------|-------------|
| `num_loans` | `int` | Total loan count |
| `num_properties` | `int` | Total property count |
| `total_loan_balance` | `float` | Sum of `actual_balance` |
| `total_original_loan_amount` | `float` | Sum of `original_amount` |
| `avg_interest_rate` | `Optional[float]` | Mean of `current_rate` |
| `avg_dscr` | `Optional[float]` | Mean of `dscr_noi_securitization` |
| `avg_occupancy` | `Optional[float]` | Mean of `occupancy_securitization` |
| `property_types` | `Dict[str, int]` | Property type code → count |
| `states` | `Dict[str, int]` | State code → count (excludes 'NA') |
| `delinquent_loans` | `int` | Count of loans with `payment_status != '0'` |
| `modified_loans` | `int` | Count of loans with `is_modified == True` |

## AutoLeaseAssetData (`edgar/abs/abs_ee.py`)

Available directly from ABS-EE filings (not via TenD). XML namespaces: autolease `http://www.sec.gov/edgar/document/absee/autolease/assetdata`, autoloan equivalent.

| Property/Method | Returns | Description |
|-----------------|---------|-------------|
| `from_filing(filing)` | `Optional[AutoLeaseAssetData]` | Classmethod; scans attachments for EX-102 by document_type |
| `assets` | `pd.DataFrame` | Asset-level data (parsed at init, not cached_property) |
| `summary()` | `AutoLeaseSummary` | Aggregate statistics |
| `__len__()` | `int` | Number of assets |

### `assets` columns

| Column | Type | Description |
|--------|------|-------------|
| `asset_id` | `str` | Asset identifier |
| `asset_type` | `str` | Asset type code |
| `period_start` | `date` | Reporting period start (MM-DD-YYYY) |
| `period_end` | `date` | Reporting period end |
| `originator` | `str` | Originator name |
| `origination_date` | `str` | Origination date (MM/YYYY) |
| `acquisition_cost` | `float` | Vehicle acquisition cost |
| `original_term_months` | `int` | Original lease term |
| `termination_date` | `str` | Scheduled termination (MM/YYYY) |
| `first_payment_date` | `str` | First payment date (MM/YYYY) |
| `grace_period_days` | `int` | Grace period days |
| `payment_type_code` | `str` | Payment type code |
| `vehicle_manufacturer` | `str` | Vehicle manufacturer name |
| `vehicle_model` | `str` | Vehicle model name |
| `vehicle_new_used` | `str` | New/used indicator |
| `vehicle_year` | `int` | Vehicle model year |
| `vehicle_type_code` | `str` | Vehicle type code (1=Car, 2=SUV, 3=Truck, etc.) |
| `vehicle_value` | `float` | Vehicle value |
| `base_residual_value` | `float` | Base residual value |
| `contract_residual_value` | `float` | Contract residual value |
| `credit_score_type` | `str` | Credit score type description |
| `credit_score` | `int` | Lessee credit score |
| `income_verification_code` | `str` | Income verification level code |
| `employment_verification_code` | `str` | Employment verification code |
| `payment_to_income_ratio` | `float` | Payment-to-income percentage |
| `lessee_state` | `str` | Lessee geographic location (state) |
| `has_co_lessee` | `bool` | Co-lessee present indicator |
| `scheduled_payment` | `float` | Scheduled payment amount |
| `actual_payment` | `float` | Actual payment amount |
| `paid_through_date` | `str` | Paid through date (MM/YYYY) |
| `zero_balance_code` | `str` | Zero balance code |
| `zero_balance_date` | `str` | Zero balance effective date (MM/YYYY) |
| `delinquency_status` | `int` | Current delinquency status |
| `remaining_term_months` | `int` | Remaining term to maturity |
| `securitization_balance` | `float` | Balance at securitization |
| `beginning_balance` | `float` | Beginning of period balance |
| `ending_balance` | `float` | End of period actual balance |

### `AutoLeaseSummary` fields

| Field | Type | Description |
|-------|------|-------------|
| `num_assets` | `int` | Total asset count |
| `total_acquisition_cost` | `float` | Sum of acquisition_cost |
| `total_residual_value` | `float` | Sum of contract_residual_value |
| `avg_credit_score` | `Optional[float]` | Mean credit score |
| `avg_lease_term` | `Optional[float]` | Mean original term in months |
| `vehicle_makes` | `Dict[str, int]` | Manufacturer → count |
| `vehicle_types` | `Dict[str, int]` | Vehicle type label → count |
| `model_years` | `Dict[int, int]` | Model year → count |
| `states` | `Dict[str, int]` | State → count |

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form` not in `('10-D', '10-D/A')` | `TenD.__init__` raises `ValueError` |
| `filing.obj()` on non-CMBS 10-D | Returns None — dispatch in `__init__.py:334-341` guards on EX-102 presence |
| `filing.html()` returns None | `_parsed_html` fails; all lazy header properties return None/empty |
| `abs_type == CMBS` but EX-102 content is empty | `asset_data` returns None; `loans`/`properties` return empty DataFrame |
| XML parse error in EX-102 | `_parse_xml()` catches ET.ParseError; returns empty DataFrames |
| `AutoLeaseAssetData.from_filing()` finds no EX-102 | Returns None |

## Access Patterns

- `filing.obj()` → `TenD` (CMBS 10-D with EX-102 only) or None
- `ten_d.abs_type` — no network; uses attachments already loaded
- `ten_d.asset_data` — triggers EX-102 text read; cached after first access
- `ten_d.loans` / `ten_d.properties` — convenience; return empty DataFrame if no asset data
- `ten_d.issuing_entity` — triggers HTML parse on first access; shares `_parsed_html` with other header fields
- `AutoLeaseAssetData.from_filing(filing)` — for ABS-EE filings directly (not via TenD)
