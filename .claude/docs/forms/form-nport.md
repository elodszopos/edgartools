# Form NPORT-P — Fund Portfolio Holdings

**SEC form codes**: NPORT-P, NPORT-EX, N-PORT, N-PORT/A
**Python class**: `FundReport`
**Access**: `filing.obj()` -> `FundReport`
**Source**: `edgar/funds/reports.py`

> N-PORT and N-PORT/A are in `NPORT_FORMS` but NOT dispatched by `edgar/__init__.py`. Only NPORT-P and NPORT-EX are dispatched.

## Complete Field Reference

### FundReport — Top-Level Fields

#### Instance Attributes (set in `__init__`)
| Attribute | Type | Description |
|-----------|------|-------------|
| `header` | `Header` | Submission type, confidentiality, filer info |
| `general_info` | `GeneralInfo` | Registrant name, CIK, address, series info, period dates |
| `fund_info` | `FundInfo` | Total assets/liabilities, metrics, return info, flows |
| `investments` | `List[InvestmentOrSecurity]` | All positions (securities + derivatives) |
| `fund_company` | `FundCompany` | Constructed from `general_info.cik` and `general_info.name` |
| `_filing` | `Optional[Filing]` | Source filing; `None` if not created via `from_filing()` |

#### Properties
| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `filing` | `Optional[Filing]` | no | Source Filing object |
| `cik` | `str` | no | From `general_info.cik` |
| `series_id` | `Optional[str]` | no | From `general_info.series_id` |
| `reporting_period` | `Optional[str]` | no | From `general_info.rep_period_date` (YYYY-MM-DD) |
| `name` | `str` | no | `"{general_info.name} - {general_info.series_name}"` |
| `has_investments` | `bool` | no | `len(investments) > 0` |
| `derivatives` | `List[InvestmentOrSecurity]` | no | Only positions where `is_derivative` is True |
| `non_derivatives` | `List[InvestmentOrSecurity]` | no | Only non-derivative positions |
| `fund_info_table` | `Table` | no | Rich table: fund/series/date/fiscal-year |
| `fund_summary_table` | `Table` | no | Rich table: assets/liabilities/net-assets/position counts |
| `metrics_table` | `Table` | no | Rich table: interest rate sensitivity DV01/DV100 |
| `credit_spread_table` | `Table` | no | Rich table: credit spread risk IG/non-IG |
| `investments_table` | `Table` | cached | Rich table of non-derivative investments; uses `_SENTINEL` cache |
| `derivatives_table` | `Table` | cached | Rich table of derivative positions; uses `_SENTINEL` cache |

#### Methods
| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing(filing)` | `filing: Filing` | `FundReport` or `None` | Classmethod; calls `filing.xml()` then `parse_fund_xml()`; returns None if no XML |
| `parse_fund_xml(xml)` | `xml: str\|bytes` | `Dict` | Classmethod; lxml parser (10-20x faster than BS4); `XMLParser(recover=True)` fallback for malformed XML |
| `investment_data(include_derivatives, include_ticker_metadata)` | `bool, bool` | `pd.DataFrame` | Main holdings DataFrame; cached by `(include_derivatives, include_ticker_metadata)` tuple; sorted by `abs(value_usd)` desc |
| `securities_data()` | — | `pd.DataFrame` | Alias for `investment_data(include_derivatives=False)` |
| `derivatives_data()` | — | `pd.DataFrame` | Derivative positions only; sorted by `abs(unrealized_pnl)` desc; uses `_SENTINEL` cache |
| `swaps_data()` | — | `pd.DataFrame` | Swap positions with full receive/pay leg columns |
| `swaptions_data()` | — | `pd.DataFrame` | Swaption positions with nested swap fields |
| `options_data()` | — | `pd.DataFrame` | Option positions; dynamic columns added per nested type (fwd/fut/swap) |
| `forwards_data()` | — | `pd.DataFrame` | FX forward positions |
| `futures_data()` | — | `pd.DataFrame` | Futures positions with reference entity identifiers |
| `get_fund_series()` | — | `FundSeries` | Constructs FundSeries from `general_info` |
| `get_tickers_for_series()` | — | `List[str]` | All tickers for this series via `get_mutual_fund_tickers()` |
| `get_ticker_for_series()` | — | `Optional[str]` | First ticker from `get_tickers_for_series()` |
| `matches_ticker(ticker)` | `ticker: str` | `bool` | Case-insensitive check against all series tickers |
| `to_context(detail)` | `detail: str = 'standard'` | `str` | AI-optimized string; levels: 'minimal'/'standard'/'full' |

## DataFrame Schemas

### `investment_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Issuer name |
| `title` | str | Security title/description |
| `lei` | str | Legal Entity Identifier |
| `cusip` | str | CUSIP identifier |
| `ticker` | Optional[str] | Resolved ticker (via `TickerResolutionService`) |
| `isin` | Optional[str] | ISIN identifier |
| `balance` | Optional[Decimal] | Share/face/notional balance |
| `units` | Optional[str] | Unit type (e.g., "NS" shares) |
| `desc_other_units` | Optional[str] | Description of non-standard units |
| `value_usd` | Decimal | Fair value in USD |
| `pct_value` | Optional[Decimal] | % of net assets |
| `payoff_profile` | Optional[str] | "Long" or "Short" |
| `asset_category` | Optional[str] | Asset category code (e.g., "EC", "DBT", "DCR", "DIR") |
| `issuer_category` | Optional[str] | Issuer category code |
| `currency_code` | Optional[str] | ISO currency code |
| `investment_country` | Optional[str] | Country of investment |
| `restricted` | bool | Is restricted security |
| `is_derivative` | bool | True if derivative position |
| `maturity_date` | datetime/str/pd.NA | From `debt_security`; pd.NA for non-debt |
| `annualized_rate` | Optional[Decimal]/pd.NA | Coupon/annualized rate; pd.NA for non-debt |
| `is_default` | bool/pd.NA | In default status; pd.NA for non-debt |
| `cash_collateral` | str/pd.NA | From `security_lending`; pd.NA if no lending |
| `non_cash_collateral` | str/pd.NA | From `security_lending`; pd.NA if no lending |
| `derivative_type` | str/pd.NA | FWD/SWP/FUT/OPT/SWO; pd.NA for non-derivatives |
| `notional_amount` | Optional[Decimal] | Extracted from derivative-specific fields |
| `counterparty` | Optional[str] | Counterparty name from derivative |

When `include_ticker_metadata=True`, two additional columns:
| Column | Type | Description |
|--------|------|-------------|
| `ticker_resolution_method` | str | Resolution method used |
| `ticker_resolution_confidence` | float | Confidence score (1.0=direct, 0.85=CUSIP, 0.0=failed) |

### `derivatives_data()` columns (base fields, all derivative types)
| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Issuer name |
| `title` | str | Security title |
| `asset_category` | str | Asset category code |
| `issuer_category` | str | Issuer category code |
| `investment_country` | str | Country code |
| `restricted` | bool | Restricted security flag |
| `fair_value_level` | str | ASC 820 fair value level |
| `balance` | Optional[Decimal] | Balance/notional |
| `units` | str | Unit type |
| `pct_value` | Optional[Decimal] | % of net assets |
| `value_usd` | Optional[Decimal] | Fair value in USD |
| `lei` | str | LEI |
| `cusip` | str | CUSIP |
| `ticker` | Optional[str] | Resolved ticker |
| `isin` | Optional[str] | ISIN |
| `currency_code` | str | ISO currency |
| `exchange_rate` | Optional[Decimal] | Exchange rate if non-USD |
| `derivative_type` | str | FWD/SWP/FUT/OPT/SWO |
| `subtype` | str | Human-readable (e.g., "Credit Default Swap", "FX Forward") |
| `payoff_profile` | Optional[str] | Long/Short |
| `counterparty` | Optional[str] | Counterparty name |
| `counterparty_lei` | Optional[str] | Counterparty LEI |
| `notional_amount` | Optional[Decimal] | Notional |
| `currency` | str | Currency (prefers `currency_conditional_code`) |
| `unrealized_pnl` | Optional[Decimal] | Unrealized gain/loss |
| `termination_date` | str | Termination/expiration date or "N/A" |
| `reference` | str | Reference entity/index name or currency pair |

### `swaps_data()` columns (all base fields plus)
| Column | Type | Description |
|--------|------|-------------|
| `counterparty` | str | Counterparty name |
| `counterparty_lei` | str | Counterparty LEI |
| `reference_entity` | str | Reference entity (CDS) |
| `reference_entity_isin` | str | Reference entity ISIN |
| `reference_entity_ticker` | str | Reference entity ticker |
| `swap_flag` | str | Swap flag value |
| `notional_amount` | Decimal | Notional amount |
| `currency` | str | Currency code |
| `termination_date` | str | Termination date |
| `upfront_payment` | Decimal | Upfront payment |
| `payment_currency` | str | Payment currency |
| `upfront_receipt` | Decimal | Upfront receipt |
| `receipt_currency` | str | Receipt currency |
| `unrealized_pnl` | Decimal | Unrealized appreciation |
| `fixed_rate_receive` | Decimal | Fixed rate on receive leg |
| `fixed_amount_receive` | Decimal | Fixed amount on receive leg |
| `fixed_currency_receive` | str | Currency of fixed receive |
| `floating_index_receive` | str | Floating index (e.g., SOFR) on receive leg |
| `floating_spread_receive` | Decimal | Spread on floating receive |
| `floating_amount_receive` | Decimal | Amount on floating receive |
| `floating_currency_receive` | str | Currency of floating receive |
| `floating_tenor_receive` | str | Tenor of floating receive |
| `floating_tenor_unit_receive` | str | Tenor unit (e.g., "Months") |
| `floating_reset_date_tenor_receive` | str | Reset date tenor |
| `floating_reset_date_unit_receive` | str | Reset date unit |
| `other_description_receive` | str | Other leg description |
| `other_type_receive` | str | fixedOrFloating attribute |
| `fixed_rate_pay` | Decimal | Fixed rate on pay leg |
| `fixed_amount_pay` | Decimal | Fixed amount on pay leg |
| `fixed_currency_pay` | str | Currency of fixed pay |
| `floating_index_pay` | str | Floating index on pay leg |
| `floating_spread_pay` | Decimal | Spread on floating pay |
| `floating_amount_pay` | Decimal | Amount on floating pay |
| `floating_currency_pay` | str | Currency of floating pay |
| `floating_tenor_pay` | str | Tenor of floating pay |
| `floating_tenor_unit_pay` | str | Tenor unit |
| `floating_reset_date_tenor_pay` | str | Reset date tenor |
| `floating_reset_date_unit_pay` | str | Reset date unit |
| `other_description_pay` | str | Other leg description |
| `other_type_pay` | str | fixedOrFloating attribute |

### `swaptions_data()` columns (all base fields plus)
| Column | Type | Description |
|--------|------|-------------|
| `put_or_call` | str | "Put" or "Call" |
| `written_or_purchased` | str | "Written" or "Purchased" |
| `share_number` | Decimal | Number of shares/contracts |
| `exercise_price` | Decimal | Strike price |
| `exercise_price_currency` | str | Strike currency |
| `expiration_date` | str | Expiration date |
| `delta` | Decimal/str | Option delta; may be 'XXXX' |
| `main_internal_id` | str | First `identifiers.other` value |
| `main_internal_id_desc` | str | First `identifiers.other` key |
| `underlying_swap_counterparty` | str | Nested swap counterparty |
| `underlying_swap_notional` | Decimal | Nested swap notional |
| `underlying_swap_currency` | str | Nested swap currency |
| `underlying_swap_termination` | str | Nested swap termination date |
| `underlying_swap_fixed_rate_receive` | Decimal | Nested swap fixed receive |
| `underlying_swap_fixed_currency_receive` | str | Nested swap fixed receive currency |
| `underlying_swap_fixed_rate_pay` | Decimal | Nested swap fixed pay |
| `underlying_swap_fixed_currency_pay` | str | Nested swap fixed pay currency |
| `underlying_swap_floating_index_receive` | str | Nested swap floating index receive |
| `underlying_swap_floating_currency_receive` | str | Nested swap floating currency receive |
| `underlying_swap_floating_spread_receive` | Decimal | Nested swap floating spread receive |
| `underlying_swap_floating_tenor_receive` | str | Nested swap tenor receive |
| `underlying_swap_floating_tenor_unit_receive` | str | Nested swap tenor unit receive |
| `underlying_swap_floating_index_pay` | str | Nested swap floating index pay |
| `underlying_swap_floating_currency_pay` | str | Nested swap floating currency pay |
| `underlying_swap_floating_spread_pay` | Decimal | Nested swap floating spread pay |
| `underlying_swap_floating_tenor_pay` | str | Nested swap tenor pay |
| `underlying_swap_floating_tenor_unit_pay` | str | Nested swap tenor unit pay |
| `underlying_swap_upfront_payment` | Decimal | Nested swap upfront payment |
| `underlying_swap_payment_currency` | str | Nested swap payment currency |
| `underlying_swap_upfront_receipt` | Decimal | Nested swap upfront receipt |
| `underlying_swap_receipt_currency` | str | Nested swap receipt currency |
| `underlying_swap_internal_id` | str | `deriv_addl_identifier` from nested swap |
| `underlying_swap_value_usd` | Decimal | `deriv_addl_value_usd` from nested swap |
| `underlying_swap_balance` | Decimal | `deriv_addl_balance` from nested swap |
| `underlying_swap_units` | str | `deriv_addl_units` from nested swap |

### `options_data()` columns (all base fields plus)
| Column | Type | Description |
|--------|------|-------------|
| `option_type` | str | "Put" or "Call" |
| `option_position` | str | "Written" or "Purchased" |
| `option_quantity` | Decimal | Number of contracts |
| `exercise_price` | Decimal | Strike price |
| `exercise_currency` | str | Strike currency |
| `expiration_date` | str | Expiration date |
| `delta` | Decimal/str | Option delta; may be 'XXXX' |
| `reference_entity` | str | Reference entity name (options on single securities) |
| `reference_entity_title` | str | Reference entity title |
| `reference_entity_isin` | str | Reference entity ISIN |
| `reference_entity_ticker` | str | Reference entity ticker |
| `reference_entity_cusip` | str | Reference entity CUSIP |
| `reference_entity_other_id` | str | Reference entity other ID |
| `index_name` | str | Index name (index options) |
| `index_identifier` | str | Index identifier (index options) |
| `has_nested_derivative` | bool | True if option has nested forward/future/swap |
| `nested_derivative_type` | str | "Forward", "Future", or "Swap" |
| `primary_exposure_usd` | Optional[Decimal] | USD exposure from nested derivative |
| `nested_fwd_currency_sold` | str | FX forward: currency sold (when nested_forward exists) |
| `nested_fwd_amount_sold` | Decimal | FX forward: amount sold |
| `nested_fwd_currency_purchased` | str | FX forward: currency purchased |
| `nested_fwd_amount_purchased` | Decimal | FX forward: amount purchased |
| `nested_fwd_settlement_date` | str | FX forward: settlement date |
| `nested_fwd_internal_id` | str | FX forward: internal ID |
| `nested_fwd_unrealized_pnl` | Decimal | FX forward: unrealized P&L |
| `nested_fwd_exchange_rate` | Decimal | FX forward: derived exchange rate |
| `nested_fx_pair` | str | FX forward: "{sold}/{purchased}" |
| `nested_fut_payoff_profile` | str | Future: payoff profile (when nested_future exists) |
| `nested_fut_expiration_date` | str | Future: expiration date |
| `nested_fut_notional_amount` | Decimal | Future: notional |
| `nested_fut_currency` | str | Future: currency |
| `nested_fut_unrealized_pnl` | Decimal | Future: unrealized P&L |
| `nested_fut_internal_id` | str | Future: other ID |
| `nested_fut_reference_entity` | str | Future: reference entity name |
| `nested_swp_notional_amount` | Decimal | Swap: notional (when nested_swap exists) |
| `nested_swp_currency` | str | Swap: currency |
| `nested_swp_termination_date` | str | Swap: termination date |
| `nested_swp_unrealized_pnl` | Decimal | Swap: unrealized P&L |
| `nested_swp_internal_id` | str | Swap: internal ID |
| `nested_swp_fixed_rate_receive` | Decimal | Swap: fixed rate receive |
| `nested_swp_fixed_rate_pay` | Decimal | Swap: fixed rate pay |
| `nested_swp_floating_index_receive` | str | Swap: floating index receive |
| `nested_swp_floating_index_pay` | str | Swap: floating index pay |

### `forwards_data()` columns (all base fields plus)
| Column | Type | Description |
|--------|------|-------------|
| `currency_sold` | str | Currency sold (from leg) |
| `amount_sold` | Decimal | Amount sold |
| `currency_purchased` | str | Currency purchased |
| `amount_purchased` | Decimal | Amount purchased |
| `settlement_date` | str | Settlement date |

### `futures_data()` columns (all base fields plus)
| Column | Type | Description |
|--------|------|-------------|
| `reference_entity` | str | Reference entity issuer name |
| `reference_entity_title` | str | Reference entity title |
| `reference_entity_cusip` | str | Reference entity CUSIP |
| `reference_entity_isin` | str | Reference entity ISIN |
| `reference_entity_ticker` | str | Reference entity ticker |
| `reference_entity_other_id` | str | Reference entity other identifier |
| `reference_entity_other_id_type` | str | Other identifier type |
| `expiration_date` | str | Futures expiration date |

## Nested Objects

### `Header` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `submission_type` | str | Form type string |
| `is_confidential` | bool | Confidential treatment flag |
| `filer_info` | `FilerInfo` | Filer credentials and series/class info |

### `FilerInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `issuer_credentials` | `IssuerCredentials` | CIK and CCC (CIK Confirmation Code) |
| `series_class_info` | `Optional[SeriesClassInfo]` | Series/class IDs |
| `series_id` | str (property) | From `series_class_info.series_id` |
| `class_id` | str (property) | From `series_class_info.class_id` |

### `GeneralInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Registrant name |
| `cik` | str | Registrant CIK |
| `file_number` | str | Investment Company Act file number |
| `reg_lei` | Optional[str] | Registrant LEI |
| `street1` | str | Address street line 1 |
| `street2` | Optional[str] | Address street line 2 |
| `city` | Optional[str] | City |
| `state` | Optional[str] | State code |
| `country` | Optional[str] | Country code |
| `zip_or_postal_code` | Optional[str] | Postal code |
| `phone` | Optional[str] | Phone number |
| `series_name` | Optional[str] | Series name |
| `series_lei` | Optional[str] | Series LEI |
| `series_id` | Optional[str] | Series ID (S000xxxxx) |
| `fiscal_year_end` | Optional[str] | End of reporting period (repPdEnd) |
| `rep_period_date` | Optional[str] | Report period date (YYYY-MM-DD) |
| `is_final_filing` | Optional[bool] | Final filing flag |

### `FundInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `total_assets` | Decimal | Total assets (USD) |
| `total_liabilities` | Decimal | Total liabilities (USD) |
| `net_assets` | Optional[Decimal] | Net assets (USD) |
| `assets_attr_misc_sec` | Optional[Decimal] | Assets attributed to misc securities |
| `assets_invested` | Optional[Decimal] | Assets invested |
| `amt_pay_one_yr_banks_borr` | Optional[Decimal] | Payable within 1yr: bank borrowings |
| `amt_pay_one_yr_ctrld_comp` | Optional[Decimal] | Payable within 1yr: controlled companies |
| `amt_pay_one_yr_oth_affil` | Optional[Decimal] | Payable within 1yr: other affiliates |
| `amt_pay_one_yr_other` | Optional[Decimal] | Payable within 1yr: other |
| `amt_pay_aft_one_yr_banks_borr` | Optional[Decimal] | Payable after 1yr: bank borrowings |
| `amt_pay_aft_one_yr_ctrld_comp` | Optional[Decimal] | Payable after 1yr: controlled companies |
| `amt_pay_aft_one_yr_oth_affil` | Optional[Decimal] | Payable after 1yr: other affiliates |
| `amt_pay_aft_one_yr_other` | Optional[Decimal] | Payable after 1yr: other |
| `delay_deliv` | Optional[Decimal] | When-issued or delayed-delivery securities |
| `stand_by_commit` | Optional[Decimal] | Standby commitments |
| `liquidity_pref` | Optional[Decimal] | Liquidation preference |
| `cash_not_report_in_cor_d` | Optional[Decimal] | Cash not in Cor-D |
| `current_metrics` | `Dict[str, CurrentMetric]` | Interest rate sensitivity keyed by currency |
| `credit_spread_risk_investment_grade` | Optional[PeriodType] | Credit spread risk (IG) |
| `credit_spread_risk_non_investment_grade` | Optional[PeriodType] | Credit spread risk (non-IG) |
| `is_non_cash_collateral` | Optional[bool] | Non-cash collateral flag |
| `return_info` | Optional[ReturnInfo] | Monthly returns and realized changes |
| `monthly_flow1` | Optional[MonthlyFlow] | Month 1 flows (redemption/reinvestment/sales) |
| `monthly_flow2` | Optional[MonthlyFlow] | Month 2 flows |
| `monthly_flow3` | Optional[MonthlyFlow] | Month 3 flows |

### `CurrentMetric` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `currency` | str | Currency code |
| `intrstRtRiskdv01` | `PeriodType` | Dollar value of a basis point (DV01) |
| `intrstRtRiskdv100` | `PeriodType` | Dollar value of 100bps |

### `PeriodType` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `period3Mon` | Decimal | 3-month sensitivity |
| `period1Yr` | Decimal | 1-year sensitivity |
| `period5Yr` | Decimal | 5-year sensitivity |
| `period10Yr` | Decimal | 10-year sensitivity |
| `period30Yr` | Decimal | 30-year sensitivity |

### `ReturnInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `monthly_total_returns` | `List[MonthlyTotalReturn]` | Per-class monthly returns (3 months) |
| `other_mon1` | `RealizedChange` | Month 1 realized/unrealized changes |
| `other_mon2` | `RealizedChange` | Month 2 realized/unrealized changes |
| `other_mon3` | `RealizedChange` | Month 3 realized/unrealized changes |

### `MonthlyTotalReturn` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `class_id` | Optional[str] | Share class ID |
| `return1` | Optional[Decimal/str] | Month 1 return (or "N/A") |
| `return2` | Optional[Decimal/str] | Month 2 return (or "N/A") |
| `return3` | Optional[Decimal/str] | Month 3 return (or "N/A") |

### `RealizedChange` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `net_realized_gain` | Optional[Decimal/str] | Net realized gain (or "N/A") |
| `net_unrealized_appreciation` | Optional[Decimal/str] | Net unrealized appreciation (or "N/A") |

### `MonthlyFlow` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `redemption` | Optional[Decimal/str] | Redemptions (or "N/A") |
| `reinvestment` | Optional[Decimal/str] | Reinvestments (or "N/A") |
| `sales` | Optional[Decimal/str] | Sales (or "N/A") |

### `InvestmentOrSecurity` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Issuer name |
| `lei` | str | LEI |
| `title` | str | Security title |
| `cusip` | str | CUSIP |
| `identifiers` | `Identifiers` | Additional identifiers (ticker, ISIN, other) |
| `balance` | Optional[Decimal] | Balance/shares |
| `units` | Optional[str] | Unit type |
| `desc_other_units` | Optional[str] | Other units description |
| `currency_code` | Optional[str] | Currency code |
| `currency_conditional_code` | Optional[str] | Conditional currency code |
| `exchange_rate` | Optional[Decimal] | Exchange rate |
| `value_usd` | Decimal | USD value |
| `pct_value` | Optional[Decimal] | % of net assets |
| `payoff_profile` | Optional[str] | Long/Short |
| `asset_category` | Optional[str] | Asset category (EC, DBT, DCR, DIR, DCO, DFE, DE, etc.) |
| `issuer_category` | Optional[str] | Issuer category |
| `investment_country` | Optional[str] | Country code |
| `is_restricted_security` | bool | Restricted security flag |
| `fair_value_level` | Optional[str] | ASC 820 level (1/2/3) |
| `debt_security` | Optional[DebtSecurity] | Debt-specific fields |
| `security_lending` | Optional[SecurityLending] | Securities lending flags |
| `derivative_info` | Optional[DerivativeInfo] | Derivative data |

**Properties on `InvestmentOrSecurity`:**
| Property | Type | Description |
|----------|------|-------------|
| `ticker` | Optional[str] | Resolved ticker via `TickerResolutionService` |
| `ticker_resolution_info` | `TickerResolutionResult` | Full resolution metadata |
| `isin` | Optional[str] | From `identifiers.isin` |
| `is_derivative` | bool | `derivative_info is not None` |
| `absolute_value` | Decimal | `abs(value_usd)` for sorting |
| `derivative_type` | Optional[str] | FWD/SWP/FUT/OPT/SWO |
| `derivative_subtype` | Optional[str] | Human label (e.g., "Credit Default Swap") |
| `is_credit_derivative` | bool | `asset_category == "DCR"` |
| `is_interest_rate_derivative` | bool | `asset_category == "DIR"` |
| `is_commodity_derivative` | bool | `asset_category == "DCO"` |
| `is_fx_derivative` | bool | `asset_category == "DFE"` |
| `is_equity_derivative` | bool | `asset_category == "DE"` |

### `DebtSecurity` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `maturity_date` | datetime/str | Maturity date or "N/A" |
| `coupon_kind` | str | Fixed/Variable/None/Other |
| `annualized_rate` | Optional[Decimal] | Annualized rate |
| `is_default` | bool | Default flag |
| `are_instrument_payents_in_arrears` | bool | Payments in arrears flag |
| `is_paid_kind` | bool | PIK flag |
| `is_mandatory_convertible` | bool | Mandatory convertible flag |
| `is_continuing_convertible` | bool | Contingent convertible flag |

### `SecurityLending` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `is_cash_collateral` | Optional[str] | "Y"/"N" |
| `is_non_cash_collateral` | Optional[str] | "Y"/"N" |
| `is_loan_by_fund` | Optional[str] | "Y"/"N" |

### `Identifiers` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `ticker` | Optional[str] | Ticker from identifiers block |
| `isin` | Optional[str] | ISIN from identifiers block |
| `other` | Dict | `{otherDesc: value}` for non-standard identifiers |

### `DerivativeInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `derivative_category` | Optional[str] | FWD/SWP/FUT/OPT/SWO/WAR |
| `forward_derivative` | Optional[ForwardDerivative] | FX forward data |
| `swap_derivative` | Optional[SwapDerivative] | Swap data (IRS/CDS/TRS) |
| `future_derivative` | Optional[FutureDerivative] | Futures data |
| `option_derivative` | Optional[OptionDerivative] | Options data (OPT) |
| `swaption_derivative` | Optional[SwaptionDerivative] | Swaption data (SWO) |

### `ForwardDerivative` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `counterparty_name` | Optional[str] | Counterparty name |
| `counterparty_lei` | Optional[str] | Counterparty LEI |
| `currency_sold` | Optional[str] | Currency sold |
| `amount_sold` | Optional[Decimal] | Amount sold |
| `currency_purchased` | Optional[str] | Currency purchased |
| `amount_purchased` | Optional[Decimal] | Amount purchased |
| `settlement_date` | Optional[str] | Settlement date |
| `unrealized_appreciation` | Optional[Decimal] | Unrealized appreciation |
| `deriv_addl_name` | Optional[str] | From `derivAddlInfo` block |
| `deriv_addl_lei` | Optional[str] | From `derivAddlInfo` |
| `deriv_addl_title` | Optional[str] | From `derivAddlInfo` |
| `deriv_addl_cusip` | Optional[str] | From `derivAddlInfo` |
| `deriv_addl_identifier` | Optional[str] | Other identifier from `derivAddlInfo` |
| `deriv_addl_identifier_type` | Optional[str] | Other identifier type |
| `deriv_addl_balance` | Optional[Decimal] | Balance from `derivAddlInfo` |
| `deriv_addl_units` | Optional[str] | Units from `derivAddlInfo` |
| `deriv_addl_currency` | Optional[str] | Currency from `derivAddlInfo` |
| `deriv_addl_value_usd` | Optional[Decimal] | USD value from `derivAddlInfo` |
| `deriv_addl_pct_val` | Optional[Decimal] | % value from `derivAddlInfo` |
| `deriv_addl_asset_cat` | Optional[str] | Asset category from `derivAddlInfo` |
| `deriv_addl_issuer_cat` | Optional[str] | Issuer category from `derivAddlInfo` |
| `deriv_addl_inv_country` | Optional[str] | Country from `derivAddlInfo` |

### `SwapDerivative` (Pydantic)
See `swaps_data()` column documentation above for all fields. The Pydantic model directly maps to those columns. Key fields include: `counterparty_name`, `counterparty_lei`, `notional_amount`, `currency`, `unrealized_appreciation`, `termination_date`, `upfront_payment`, `payment_currency`, `upfront_receipt`, `receipt_currency`, `reference_entity_name/title/cusip/isin/ticker`, `swap_flag`, plus all `fixed_rate/floating_*` receive/pay leg fields, plus all `deriv_addl_*` fields (same structure as `ForwardDerivative` plus `deriv_addl_desc_units`).

### `FutureDerivative` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `counterparty_name` | Optional[str] | Counterparty name |
| `counterparty_lei` | Optional[str] | Counterparty LEI |
| `payoff_profile` | Optional[str] | Long/Short |
| `expiration_date` | Optional[str] | Expiration date |
| `notional_amount` | Optional[Decimal] | Notional |
| `currency` | Optional[str] | Currency |
| `unrealized_appreciation` | Optional[Decimal] | Unrealized appreciation |
| `reference_entity_name` | Optional[str] | Reference issuer name |
| `reference_entity_title` | Optional[str] | Reference issue title |
| `reference_entity_cusip` | Optional[str] | Reference CUSIP |
| `reference_entity_isin` | Optional[str] | Reference ISIN |
| `reference_entity_ticker` | Optional[str] | Reference ticker |
| `reference_entity_other_id` | Optional[str] | Other reference ID |
| `reference_entity_other_id_type` | Optional[str] | Other reference ID type |

### `OptionDerivative` (Pydantic)
Fields: `counterparty_name`, `counterparty_lei`, `put_or_call`, `written_or_purchased`, `share_number`, `exercise_price`, `exercise_price_currency`, `expiration_date`, `delta` (Decimal or 'XXXX'), `unrealized_appreciation`, `reference_entity_name/title/cusip/isin/ticker/other_id/other_id_type`, `index_name`, `index_identifier`, `nested_forward: Optional[ForwardDerivative]`, `nested_future: Optional[FutureDerivative]`, `nested_swap: Optional[SwapDerivative]`.

### `SwaptionDerivative` (Pydantic)
Fields: `counterparty_name`, `counterparty_lei`, `put_or_call`, `written_or_purchased`, `share_number`, `exercise_price`, `exercise_price_currency`, `expiration_date`, `delta` (Decimal or 'XXXX'), `unrealized_appreciation`, `nested_swap: Optional[SwapDerivative]`.

## Error Paths
| Condition | Behavior |
|-----------|----------|
| `filing.xml()` returns None | `from_filing()` returns None |
| Malformed XML | `etree.XMLParser(recover=True)` fallback; may lose some elements |
| Empty investments list | `investment_data()` returns DataFrame with minimal columns only |
| No matching derivative type | Specific `*_data()` methods return empty DataFrame |
| `series_id` is None | `get_tickers_for_series()` returns `[]` |
| Derivative with `desc_other_units` containing "notional" | `_get_notional_amount()` uses `balance` as notional |

## Access Patterns

- `filing.obj()` or `FundReport.from_filing(filing)`
- `report.investment_data()` — all holdings as DataFrame
- `report.securities_data()` — non-derivative positions only
- `report.derivatives_data()` — derivatives summary
- `report.swaps_data()` / `report.options_data()` / `report.forwards_data()` / `report.futures_data()` / `report.swaptions_data()` — type-specific derivative frames
- `report.fund_info.net_assets` — net assets as Decimal
- `report.general_info.rep_period_date` — report date string
- `report.investments[0].derivative_info.swap_derivative.notional_amount` — drill into specific position
- `get_fund_portfolio_from_filing(filing)` — convenience wrapper returning `investment_data()` DataFrame; returns empty DataFrame on error
