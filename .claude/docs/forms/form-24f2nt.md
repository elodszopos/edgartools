# Form 24F-2NT — Annual Fee Notice

**SEC form codes**: 24F-2NT, 24F-2NT/A
**Python class**: `FundFeeNotice` (extends `XmlFiling`)
**Access**: `filing.obj()` -> `FundFeeNotice`
**Source**: `edgar/funds/twentyfourf.py`

> `FundFeeNotice` inherits `from_filing()` from `XmlFiling` — it does NOT define its own `from_filing()`. All data is accessed through `self._form_data` (from `XmlFiling`). Two filing patterns: fund-level (~98%, 1 block) and per-class (~2%, N blocks).

## Complete Field Reference

### FundFeeNotice — Inherited from `XmlFiling`

These fields are available from the parent class:
| Property | Type | Description |
|----------|------|-------------|
| `company` | str | Filer company name |
| `filing_date` | str | Filing date |
| `form` | str | Form type string |
| `cik` | str | CIK |
| `_form_data` | dict | Parsed XML data |
| `to_html()` | method | SEC XSLT-rendered HTML |

### FundFeeNotice — Specific Fields

#### `cached_property` Accessors
| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `_filing_info_blocks` | `List[dict]` | cached | All `annualFilingInfo` blocks; length=1 for fund-level, N for per-class |
| `series` | `List[SeriesInfo]` | cached | Series reported; deduplicates by `series_id` across blocks |
| `class_fees` | `List[FundClassFee]` | cached | Per-class breakdown; **empty list for fund-level filings** |

#### Properties (no caching)
| Property | Type | Description |
|----------|------|-------------|
| `is_per_class` | bool | `len(_filing_info_blocks) > 1` |
| `fund_name` | Optional[str] | From `item1.nameOfIssuer` |
| `fund_address` | Optional[dict] | From `item1.addressOfIssuer` dict |
| `investment_company_act_file_number` | Optional[str] | From `item3.investmentCompActFileNo` (811-XXXXX) |
| `fiscal_year_end` | Optional[str] | From `item4.lastDayOfFiscalYear` (e.g., '12/31/2025') |
| `is_filed_late` | bool | From `item4.isThisFormBeingFiledLate` |
| `is_final_filing` | bool | From `item4.isThisTheLastTimeIssuerFilingThisForm` |
| `aggregate_sales` | Optional[float] | `item5.aggregateSalePriceOfSecuritiesSold` summed across blocks |
| `redemptions_current_year` | Optional[float] | `item5.aggregatePriceOfSecuritiesRedeemedOrRepurchasedInFiscalYear` summed |
| `redemptions_prior_years` | Optional[float] | `item5.aggregatePriceOfSecuritiesRedeemedOrRepurchasedAnyPrior` summed |
| `total_redemption_credits` | Optional[float] | `item5.totalAvailableRedemptionCredits` summed |
| `net_sales` | Optional[float] | `item5.netSales` summed across blocks |
| `unused_redemption_credits` | Optional[float] | `item5.redemptionCreditsAvailableForUseInFutureYears` summed |
| `fee_multiplier` | Optional[float] | `item5.multiplierForDeterminingRegistrationFee`; from first block only |
| `registration_fee` | Optional[float] | `item5.registrationFeeDue` summed across blocks |
| `interest_due` | Optional[float] | `item6.interestDue` summed across blocks |
| `total_due` | Optional[float] | `item7.totalOfRegistrationFeePlusAnyInterestDue` summed |

#### Methods
| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `to_context(detail)` | `detail: str = 'standard'` | str | AI-optimized string; levels: 'minimal'/'standard'/'full' |

## Nested Objects

### `SeriesInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `series_name` | str | Series name |
| `series_id` | str | Series ID (S000xxxxx) |
| `include_all_classes` | bool | `includeAllClassesFlag` parsed as bool |

### `FundClassFee` (frozen dataclass)
Only populated for per-class filings (`is_per_class == True`).
| Field | Type | Description |
|-------|------|-------------|
| `series_or_class_id` | str | `item5.seriesOrClassId` |
| `series_id` | Optional[str] | Parent series ID from `item2.rptSeriesClassInfo.seriesId` |
| `class_name` | Optional[str] | Class name from `item2.rptSeriesClassInfo.classInfo.className` |
| `aggregate_sales` | Optional[float] | Aggregate sale price of securities sold |
| `aggregate_redemptions_in_fy` | Optional[float] | Redemptions in fiscal year |
| `aggregate_redemptions_any_prior` | Optional[float] | Redemptions from prior years |
| `total_available_redemption_credits` | Optional[float] | Total redemption credits |
| `net_sales` | Optional[float] | Net sales |
| `redemption_credits_for_future` | Optional[float] | Credits available for future years |
| `multiplier_for_fee` | Optional[float] | Fee multiplier |
| `registration_fee_due` | Optional[float] | Registration fee due |
| `interest_due` | Optional[float] | Interest due (from `item6`) |
| `total_due` | Optional[float] | Total due (from `item7`) |

## Two Filing Patterns

### Fund-level (single block, ~98%)
| Aspect | Behavior |
|--------|----------|
| `_filing_info_blocks` | List of length 1 |
| `is_per_class` | `False` |
| `class_fees` | Returns `[]` |
| Typed properties | Read directly from `item5` of the single block |

### Per-class (multiple blocks, ~2%)
| Aspect | Behavior |
|--------|----------|
| `_filing_info_blocks` | List of length N (one per share class) |
| `is_per_class` | `True` |
| `class_fees` | Returns `List[FundClassFee]` with N entries |
| Typed properties | `_sum_item5()` aggregates across all N blocks |
| `series` | Deduplicates — same parent series appears only once |
| `fund_name`, file numbers, fiscal year | Taken from first block only (identical across blocks) |

## Error Paths
| Condition | Behavior |
|-----------|----------|
| `_form_data.annualFilings` absent or wrong type | `_filing_info_blocks` returns `[]` |
| `_filing_info_blocks` empty | All typed properties return None |
| Numeric strings with parentheses like `(123.45)` | `_parse_float()` converts to `-123.45` |
| Field is None in `item5` | `_sum_item5()` excludes from sum; returns None if all None |
| `class_fees` called on fund-level filing | Returns empty list; caller must check `is_per_class` first |

## Access Patterns

- `filing.obj()` or direct via `XmlFiling.from_filing()` (inherited)
- `notice.aggregate_sales` — total securities sold (float)
- `notice.net_sales` — aggregate_sales minus redemption credits
- `notice.registration_fee` — SEC fee due
- `notice.fiscal_year_end` — e.g., "12/31/2025"
- `notice.series` — `List[SeriesInfo]`
- `notice.is_per_class` — check before accessing `class_fees`
- `notice.class_fees` — `List[FundClassFee]`; empty for fund-level filings
- `notice.class_fees[0].aggregate_sales` — per-class sales
- `notice.to_html()` — XSLT-rendered HTML (inherited from `XmlFiling`)
