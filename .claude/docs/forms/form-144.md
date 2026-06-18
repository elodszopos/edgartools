# Form 144 — Restricted Stock Sale Notice

**SEC form codes**: `144`, `144/A`
**Python class**: `Form144`
**Access**: `filing.obj()` → `Form144`
**Base fields**: See `_base-filing.md`
**Source**: `edgar/form144.py`

---

## Complete Field Reference

### From Filing (inherited)
See `_base-filing.md`

### Form144-Specific Fields

#### Instance Attributes (set in `__init__`)

| Field | Type | Description |
|-------|------|-------------|
| `filer` | `Filer` | SEC filer credentials (CIK, entity name, file number) |
| `contact` | `Contact` | Contact name, phone, email |
| `issuer_cik` | `str` | Issuer company CIK |
| `issuer_name` | `str` | Issuer company name |
| `sec_file_number` | `str` | SEC file number of the issuer |
| `issuer_contact_phone` | `str` | Issuer's contact phone number |
| `person_selling` | `str` | Name of person on whose account securities are to be sold |
| `relationships` | `List[str]` | Relationships to issuer (e.g. `["Director", "Officer"]`) |
| `address` | `Address` | Issuer's registered address |
| `nothing_to_report` | `bool` | `nothingToReportFlagOnSecuritiesSoldInPast3Months` XML flag |
| `remarks` | `str` | Free-text remarks field |
| `notice_signature` | `NoticeSignature` | Signature block including plan adoption dates |

#### Properties — Immediate (no network)

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `is_amendment` | `bool` | no | True if `'/A'` in `_filing.form` |
| `filing_date` | `str` | no | Delegates to `_filing.filing_date` |
| `company` | `Company` | network | `Company(self.issuer_cik)` — not cached; constructs on every access |
| `num_securities` | `int` | no | Count of rows in `securities_information` |
| `is_multi_security` | `bool` | no | True if more than one security in filing |

#### Properties — DataFrame Access (backward-compatible)

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `securities_information` | `pd.DataFrame` | no | Raw securities information DataFrame |
| `securities_to_be_sold` | `pd.DataFrame` | no | Raw securities to be sold DataFrame |
| `securities_sold_past_3_months` | `pd.DataFrame` | no | Raw past 3-month sales DataFrame |

#### Properties — Holder Access (new API)

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `securities_info` | `SecuritiesInformationHolder` | no | Securities with aggregation methods |
| `securities_selling` | `SecuritiesToBeSoldHolder` | no | Acquisition history with aggregation |
| `recent_sales` | `SecuritiesSoldPast3MonthsHolder` | no | Past 3-month sales with aggregation |

#### Properties — Aggregation (delegate to holders)

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `total_units_to_be_sold` | `int` | no | Sum of `units_to_be_sold` across all securities |
| `total_market_value` | `float` | no | Sum of `market_value` across all securities |
| `total_amount_acquired` | `int` | no | Sum of `amount_acquired` from securities_to_be_sold |
| `total_amount_sold_past_3_months` | `int` | no | Sum of `amount_sold` from past-3-months |
| `total_gross_proceeds_past_3_months` | `float` | no | Sum of `gross_proceeds` from past-3-months |
| `units_to_be_sold` | `int` | no | Alias for `total_units_to_be_sold` |
| `market_value` | `float` | no | Alias for `total_market_value` |

#### Properties — Convenience (first-security shortcuts)

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `approx_sale_date` | `Optional[str]` | no | `approx_sale_date` from first security row; `None` if empty |
| `security_class` | `Optional[str]` | no | `security_class` from first security row |
| `broker_name` | `Optional[str]` | no | `broker_name` from first security row |
| `exchange_name` | `Optional[str]` | no | `exchange_name` from first security row |

#### Properties — Analyst Metrics (computed, no network)

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `percent_of_holdings` | `float` | no | `(total_units_to_be_sold / units_outstanding[0]) * 100`; uses first row's `units_outstanding` only |
| `avg_price_per_unit` | `float` | no | `total_market_value / total_units_to_be_sold`; 0.0 if no units |
| `is_10b5_1_plan` | `bool` | no | True when valid (non-1933) `planAdoptionDates` exist in `notice_signature` |
| `days_since_plan_adoption` | `Optional[int]` | no | Days from most recent valid plan date to `approx_sale_date` |
| `cooling_off_compliant` | `Optional[bool]` | no | `days_since_plan_adoption >= 90`; `None` if no plan |
| `holding_period_days` | `Optional[int]` | no | Mean days from `acquired_date` to `approx_sale_date` (filters 1933 placeholders) |
| `holding_period_years` | `Optional[float]` | no | `holding_period_days / 365.25` rounded to 1 decimal |

#### Properties — Anomaly Flags (computed, no network)

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `is_large_liquidation` | `bool` | no | `percent_of_holdings > 5.0` |
| `is_short_hold` | `bool` | no | `holding_period_years < 1.0` |
| `has_multiple_plans` | `bool` | no | Multiple distinct non-1933 `planAdoptionDate` values |
| `anomaly_flags` | `List[str]` | no | List from: `LARGE_LIQUIDATION`, `SHORT_HOLD`, `COOLING_OFF_VIOLATION`, `MULTIPLE_PLANS` |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing: Filing` | `Optional[Form144]` | Factory; asserts `form in ['144','144/A']`; calls `parse_xml`; returns `None` if no XML |
| `parse_xml` | `xml: str` | `Dict[str, object]` | Static; parses `<edgarSubmission>` XML; returns kwargs dict |
| `get_summary` | — | `Dict[str, Any]` | Dict with: person_selling, issuer, issuer_cik, relationships, num_securities, total_units_to_be_sold, total_market_value, security_classes, exchanges, nothing_to_report_past_3_months, total_sold_past_3_months, is_amendment, filing_date |
| `to_analyst_summary` | — | `Dict[str, Any]` | Full screening metrics dict (see schema below) |
| `to_dataframe` | — | `pd.DataFrame` | One row per security from `securities_information`; adds person_selling, issuer, issuer_cik, filing_date, is_amendment columns |
| `to_context` | `detail: str = 'standard'` | `str` | AI-optimized context; detail: `'minimal'`/`'standard'`/`'full'` |

#### Module-level Helpers

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `concat_securities_information` | `form144_lst: List[Form144]` | `pd.DataFrame` | Concat `securities_information` DataFrames across filings |
| `concat_securities_to_be_sold` | `form144_lst: List[Form144]` | `pd.DataFrame` | Concat `securities_to_be_sold` DataFrames across filings |

---

## Nested Objects

### `SecuritiesInformation` (frozen dataclass)
One row per `<securitiesInformation>` XML tag; collected into `securities_information` DataFrame.

| Field | Type | Description |
|-------|------|-------------|
| `security_class` | `str` | Security class title (e.g. "Common stock") |
| `units_to_be_sold` | `int` | `noOfUnitsSold` from XML; defaults to 0 |
| `aggregate_market_value` | `float` | `aggregateMarketValue`; `None` if absent |
| `units_outstanding` | `int` | `noOfUnitsOutstanding`; defaults to 0 |
| `approx_sale_date` | `str` | `approxSaleDate` in MM/DD/YYYY format |
| `exchange_name` | `str` | `securitiesExchangeName` (e.g. "CHX", "NYSE") |
| `broker_name` | `str` | Name from `<brokerOrMarketmakerDetails>` |
| `broker_address` | `Address` | Broker address; `None` if no broker element |

### `SecuritiesToBeSold` (frozen dataclass)
One row per `<securitiesToBeSold>` XML tag; collected into `securities_to_be_sold` DataFrame.

| Field | Type | Description |
|-------|------|-------------|
| `security_class` | `str` | `securitiesClassTitle` |
| `acquired_date` | `str` | `acquiredDate` in MM/DD/YYYY; `'01/01/1933'` = SEC placeholder |
| `nature_of_acquisition_transaction` | `str` | How securities were acquired (e.g. "Employee Stock Award") |
| `name_of_person_from_whom_acquired` | `str` | Transferor name |
| `is_gift_transaction` | `str` | `'Y'` or `'N'` |
| `donar_acquired_date` | `str` | Date donor acquired the securities |
| `amount_of_securities_acquired` | `int` | `amountOfSecuritiesAcquired` |
| `payment_date` | `str` | `paymentDate` |
| `nature_of_payment` | `str` | `natureOfPayment` (e.g. "CASH") |

### `SecuritiesSoldPast3Months` (frozen dataclass)
One row per `<securitiesSoldInPast3Months>` XML tag.

| Field | Type | Description |
|-------|------|-------------|
| `seller_name` | `str` | Name from `<sellerDetails>` |
| `seller_address` | `Address` | Address from `<sellerDetails>` |
| `security_class` | `str` | `securitiesClassTitle` |
| `sale_date` | `str` | `saleDate` in MM/DD/YYYY format |
| `amount_of_securities_sold` | `int` | `amountOfSecuritiesSold` |
| `gross_proceeds` | `float` | `grossProceeds`; `None` if absent |

### `NoticeSignature` (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `notice_date` | `str` | `noticeDate` in MM/DD/YYYY format |
| `plan_adoption_dates` | `List[str]` | All `<planAdoptionDate>` values; includes placeholder `'01/01/1933'` |
| `signature` | `str` | `/s/ Name` signature text |

### `SecuritiesInformationHolder` (SecuritiesHolder subclass)
Wraps `securities_information` DataFrame with aggregation properties.

| Property | Type | Description |
|----------|------|-------------|
| `data` | `pd.DataFrame` | Underlying DataFrame |
| `empty` | `bool` | True if no rows |
| `total_units_to_be_sold` | `int` | Sum of `units_to_be_sold` |
| `total_market_value` | `float` | Sum of `market_value` |
| `security_classes` | `List[str]` | All security class titles |
| `exchanges` | `List[str]` | Unique exchange names |
| `brokers` | `List[str]` | Unique broker names |
| `percent_of_outstanding` | `float` | `(total_units / units_outstanding[0]) * 100` |
| `avg_price_per_unit` | `float` | `total_market_value / total_units_to_be_sold` |

### `SecuritiesToBeSoldHolder` (SecuritiesHolder subclass)
Wraps `securities_to_be_sold` DataFrame.

| Property | Type | Description |
|----------|------|-------------|
| `total_amount_acquired` | `int` | Sum of `amount_acquired` |
| `acquisition_dates` | `List[str]` | Unique `acquired_date` values |
| `has_gift_transactions` | `bool` | True if any `is_gift == 'Y'` |

### `SecuritiesSoldPast3MonthsHolder` (SecuritiesHolder subclass)
Wraps `securities_sold_past_3_months` DataFrame.

| Property | Type | Description |
|----------|------|-------------|
| `total_amount_sold` | `int` | Sum of `amount_sold` |
| `total_gross_proceeds` | `float` | Sum of `gross_proceeds` |
| `sellers` | `List[str]` | Unique seller names |

---

## DataFrame Schemas

### `securities_information` columns (from `SecuritiesInformation.to_dict()`)

| Column | Type | Description |
|--------|------|-------------|
| `security_class` | `str` | Security class title |
| `units_to_be_sold` | `int` | Units planned for sale |
| `market_value` | `float` | Aggregate market value |
| `units_outstanding` | `int` | Total shares outstanding |
| `approx_sale_date` | `str` | Planned sale date MM/DD/YYYY |
| `exchange_name` | `str` | Trading exchange |
| `broker_name` | `str` | Executing broker |

### `securities_to_be_sold` columns (from `SecuritiesToBeSold.to_dict()`)

| Column | Type | Description |
|--------|------|-------------|
| `security_class` | `str` | Security class title |
| `acquired_date` | `str` | Acquisition date (MM/DD/YYYY) |
| `amount_acquired` | `int` | Amount originally acquired |
| `nature_of_acquisition` | `str` | How shares were acquired |
| `acquired_from` | `str` | Transferor name |
| `nature_of_payment` | `str` | Payment method |
| `is_gift` | `str` | `'Y'` or `'N'` |
| `donar_acquired_date` | `str` | Date donor acquired shares |
| `payment_date` | `str` | Payment date |

### `securities_sold_past_3_months` columns (from `SecuritiesSoldPast3Months.to_dict()`)

| Column | Type | Description |
|--------|------|-------------|
| `security_class` | `str` | Security class title |
| `seller_name` | `str` | Seller/broker name |
| `sale_date` | `str` | Date of sale MM/DD/YYYY |
| `amount_sold` | `int` | Shares sold |
| `gross_proceeds` | `float` | Gross proceeds from sale |

### `to_dataframe()` columns (merged output)

| Column | Source |
|--------|--------|
| All `securities_information` columns | `SecuritiesInformation.to_dict()` |
| `person_selling` | `Form144.person_selling` |
| `issuer` | `Form144.issuer_name` |
| `issuer_cik` | `Form144.issuer_cik` |
| `filing_date` | `_filing.filing_date` |
| `is_amendment` | `Form144.is_amendment` |

### `to_analyst_summary()` keys

| Key | Type | Description |
|-----|------|-------------|
| `person_selling` | `str` | Seller name |
| `issuer` | `str` | Issuer name |
| `issuer_cik` | `str` | Issuer CIK |
| `relationships` | `List[str]` | Relationships to issuer |
| `filing_date` | `str` | ISO filing date |
| `units_to_sell` | `int` | Total units planned for sale |
| `market_value` | `float` | Total market value |
| `percent_of_holdings` | `float` | Rounded to 2 decimal places |
| `avg_price_per_unit` | `float` | Rounded to 2 decimal places |
| `sale_date` | `Optional[str]` | Approx sale date |
| `holding_period_years` | `Optional[float]` | Avg years held |
| `is_10b5_1_plan` | `bool` | Under 10b5-1 plan |
| `days_since_plan_adoption` | `Optional[int]` | Days from plan adoption to sale |
| `cooling_off_compliant` | `Optional[bool]` | 90-day rule compliance |
| `sold_past_3_months` | `int` | Units sold in past 3 months |
| `proceeds_past_3_months` | `float` | Gross proceeds past 3 months |
| `anomaly_flags` | `List[str]` | Active flags |
| `is_amendment` | `bool` | Is `144/A` |
| `exchange` | `Optional[str]` | First security's exchange |
| `broker` | `Optional[str]` | First security's broker |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form` not in `['144','144/A']` | `from_filing` raises `AssertionError` |
| `filing.xml()` returns `None` | `from_filing` returns `None` |
| No `brokerOrMarketmakerDetails` XML element | `broker_name` and `broker_address` are `None` |
| `aggregateMarketValue` absent | `aggregate_market_value` is `None` |
| `grossProceeds` absent in past-3-months | `gross_proceeds` is `None` |
| Empty `securities_information` | `approx_sale_date`, `security_class`, `broker_name`, `exchange_name` return `None`; aggregation methods return 0 |
| Plan dates all `01/01/1933` | `is_10b5_1_plan` returns `False`; `days_since_plan_adoption` returns `None` |
| `units_outstanding` is 0 | `percent_of_holdings` returns 0.0 |
| `holding_period_days` computation fails | Returns `None` (ValueError/TypeError caught) |

---

## Access Patterns

- `filing.obj()` → `Form144`
- `Form144.from_filing(filing)` — explicit construction
- `form144.securities_info.total_units_to_be_sold` — aggregated units
- `form144.securities_selling.acquisition_dates` — when shares were acquired
- `form144.recent_sales.total_gross_proceeds` — past 3-month proceeds
- `form144.to_analyst_summary()` — full dict for screening pipelines
- `concat_securities_information([f144_a, f144_b])` — bulk aggregation across filings
