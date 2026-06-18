# Form N-MFP — Money Market Fund Portfolio

**SEC form codes**: N-MFP2, N-MFP2/A, N-MFP3, N-MFP3/A
**Python class**: `MoneyMarketFund`
**Access**: `filing.obj()` -> `MoneyMarketFund`
**Source**: `edgar/funds/nmfp3.py`

## Complete Field Reference

### MoneyMarketFund — Top-Level Fields

#### Instance Attributes (set in `__init__`)
| Attribute | Type | Description |
|-----------|------|-------------|
| `general_info` | `GeneralInfo` | Report date, registrant/series name and ID, share class count |
| `series_info` | `SeriesLevelInfo` | Fund category, maturities, net assets, time series data |
| `share_classes` | `List[ShareClassInfo]` | Per-class NAV, flows, yields |
| `securities` | `List[PortfolioSecurity]` | All portfolio holdings |
| `_filing` | `Optional[Filing]` | Source filing; None if not from `from_filing()` |

#### Properties
| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `filing` | `Optional[Filing]` | no | Source Filing object |
| `cik` | str | no | From `general_info.cik` |
| `series_id` | str | no | From `general_info.series_id` |
| `name` | str | no | From `general_info.series_name` |
| `report_date` | str | no | From `general_info.report_date` |
| `fund_category` | Optional[str] | no | From `series_info.fund_category` |
| `net_assets` | Optional[Decimal] | no | From `series_info.net_assets` |
| `num_securities` | int | no | `len(self.securities)` |
| `num_share_classes` | int | no | `len(self.share_classes)` |
| `average_maturity_wam` | Optional[int] | no | Weighted average maturity in days |
| `average_maturity_wal` | Optional[int] | no | Weighted average life in days |

#### Methods
| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing(filing)` | `filing: Filing` | `Optional[MoneyMarketFund]` | Classmethod; calls `filing.xml()` then delegates to `_parse_xml()`; N-MFP2 vs N-MFP3 detection happens inside `_parse_xml()`, not here |
| `parse_nmfp3_xml(xml)` | `xml: str\|Any` | `MoneyMarketFund` | Classmethod; backward-compat alias for `_parse_xml()` |
| `portfolio_data()` | — | `pd.DataFrame` | Holdings sorted by `market_value` desc; cached |
| `share_class_data()` | — | `pd.DataFrame` | Per-class summary; cached |
| `yield_history()` | — | `pd.DataFrame` | 7-day gross yield time series from `series_info.seven_day_gross_yields`; cached |
| `nav_history()` | — | `pd.DataFrame` | Daily NAV per share series from `series_info.daily_nav_per_share`; cached |
| `liquidity_history()` | — | `pd.DataFrame` | Liquid asset % series from `series_info.liquidity_details`; cached |
| `collateral_data()` | — | `pd.DataFrame` | All repo collateral flattened; cached |
| `holdings_by_category()` | — | `pd.DataFrame` | Grouped by `category` with count/total_market_value/total_pct; cached |
| `to_context(detail)` | `detail: str = 'standard'` | str | AI-optimized string; levels: 'minimal'/'standard'/'full' |

## DataFrame Schemas

### `portfolio_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `issuer` | str | Issuer name |
| `title` | str | Security title |
| `cusip` | str | CUSIP (N-MFP2: falls back to `otherUniqueId` if absent) |
| `isin` | str | ISIN |
| `category` | str | Investment category code |
| `maturity_wam` | str | Maturity date for WAM calculation |
| `maturity_wal` | str | Maturity date for WAL calculation |
| `yield` | Optional[Decimal] | Yield as of reporting date |
| `market_value` | Optional[Decimal] | Market value including sponsor support |
| `amortized_cost` | Optional[Decimal] | Amortized cost excluding sponsor support |
| `pct_of_nav` | Optional[Decimal] | % of fund NAV |
| `daily_liquid` | bool | Daily liquid asset flag |
| `weekly_liquid` | bool | Weekly liquid asset flag |
| `has_repo` | bool | True if repurchase agreement present |

### `share_class_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `class_name` | str | Share class full name |
| `class_id` | str | Class ID (C000xxxxx) |
| `min_investment` | Optional[Decimal] | Minimum initial investment |
| `net_assets` | Optional[Decimal] | Net assets of class |
| `shares_outstanding` | Optional[Decimal] | Shares outstanding |

### `yield_history()` columns
N-MFP3 (daily, 20 entries): `date` (str), `gross_yield` (Optional[Decimal])
N-MFP2 (scalar): single row with `date=None`, `gross_yield` (Optional[Decimal])

### `nav_history()` columns
N-MFP3: `date` (str), `nav_per_share` (Optional[Decimal])
N-MFP2: `date` (f"week_{1-5}"), `nav_per_share` (Optional[Decimal]) — from `netAssetValue/fridayWeek1-5`

### `liquidity_history()` columns
| Column | Type | Description |
|--------|------|-------------|
| `date` | str | Date string (N-MFP3) or "friday_{1-5}" (N-MFP2) |
| `daily_liquid_value` | Optional[Decimal] | Total value of daily liquid assets |
| `weekly_liquid_value` | Optional[Decimal] | Total value of weekly liquid assets |
| `pct_daily_liquid` | Optional[Decimal] | % daily liquid assets |
| `pct_weekly_liquid` | Optional[Decimal] | % weekly liquid assets |

### `collateral_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `security_issuer` | str | Parent security issuer name |
| `security_cusip` | str | Parent security CUSIP |
| `collateral_issuer` | str | Collateral issuer name |
| `collateral_cusip` | str | Collateral CUSIP |
| `collateral_lei` | str | Collateral issuer LEI |
| `maturity_date` | str | Collateral maturity date |
| `coupon` | Optional[Decimal] | Coupon rate (N-MFP3: `coupon`; N-MFP2: `couponOrYield`) |
| `principal_amount` | Optional[Decimal] | Principal amount |
| `collateral_value` | Optional[Decimal] | Collateral value |
| `collateral_category` | str | Category of collateral investment |

### `holdings_by_category()` columns
| Column | Type | Description |
|--------|------|-------------|
| `category` | str | Investment category |
| `count` | int | Number of securities |
| `total_market_value` | Optional[Decimal] | Summed market value |
| `total_pct` | Optional[Decimal] | Summed % of NAV |

## Nested Objects

### `GeneralInfo` (Pydantic, nmfp3.py)
| Field | Type | Description |
|-------|------|-------------|
| `report_date` | str | Report date (YYYY-MM-DD) |
| `registrant_name` | str | Fund company name (empty for N-MFP2) |
| `cik` | str | CIK |
| `registrant_lei` | Optional[str] | Registrant LEI (None for N-MFP2) |
| `series_name` | str | Series name (empty for N-MFP2) |
| `series_lei` | Optional[str] | Series LEI (None for N-MFP2) |
| `series_id` | str | Series ID (S000xxxxx) |
| `total_share_classes` | int | Total share classes |
| `final_filing` | bool | Final filing flag |

### `SeriesLevelInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `fund_category` | Optional[str] | Money market fund category (e.g., "Government") |
| `avg_portfolio_maturity` | Optional[int] | WAM in days |
| `avg_life_maturity` | Optional[int] | WAL in days |
| `cash` | Optional[Decimal] | Cash held |
| `total_value_portfolio_securities` | Optional[Decimal] | Total portfolio securities value |
| `amortized_cost_portfolio_securities` | Optional[Decimal] | Amortized cost |
| `total_value_other_assets` | Optional[Decimal] | Other assets value |
| `total_value_liabilities` | Optional[Decimal] | Total liabilities |
| `net_assets` | Optional[Decimal] | Net assets |
| `shares_outstanding` | Optional[Decimal] | Total shares outstanding |
| `seek_stable_price` | bool | Seeks stable $1.00 NAV |
| `stable_price_per_share` | Optional[Decimal] | Stable NAV per share |
| `seven_day_gross_yields` | List[dict] | Yield time series (see `yield_history()` schema) |
| `daily_nav_per_share` | List[dict] | NAV time series (see `nav_history()` schema) |
| `liquidity_details` | List[dict] | Liquidity time series (see `liquidity_history()` schema) |

### `ShareClassInfo` (Pydantic, nmfp3.py)
| Field | Type | Description |
|-------|------|-------------|
| `class_name` | str | Class full name |
| `class_id` | str | Class ID (C000xxxxx) |
| `min_initial_investment` | Optional[Decimal] | Minimum initial investment |
| `net_assets` | Optional[Decimal] | Net assets of class |
| `shares_outstanding` | Optional[Decimal] | Shares outstanding |
| `daily_nav` | List[dict] | Per-class NAV time series: `{date, nav_per_share}` |
| `daily_flows` | List[dict] | Per-class flows: N-MFP3 `{date, gross_subscriptions, gross_redemptions}`; N-MFP2 `{date, gross_subscriptions, gross_redemptions}` (weekly) |
| `seven_day_net_yields` | List[dict] | Per-class net yield series: `{date, net_yield}` |

### `PortfolioSecurity` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `issuer_name` | Optional[str] | Issuer name |
| `title` | Optional[str] | Security title |
| `cusip` | Optional[str] | CUSIP (N-MFP2: `otherUniqueId` fallback) |
| `isin` | Optional[str] | ISIN |
| `lei` | Optional[str] | LEI |
| `cik` | Optional[str] | Issuer CIK |
| `investment_category` | Optional[str] | Investment category code |
| `maturity_date_wam` | Optional[str] | Maturity date for WAM |
| `maturity_date_wal` | Optional[str] | Maturity date for WAL |
| `final_maturity_date` | Optional[str] | Final legal maturity date |
| `yield_rate` | Optional[Decimal] | Yield as of report date |
| `market_value` | Optional[Decimal] | Market value (including sponsor support) |
| `amortized_cost` | Optional[Decimal] | Amortized cost (excluding sponsor support) |
| `pct_of_nav` | Optional[Decimal] | % of fund NAV |
| `daily_liquid` | bool | Daily liquid asset |
| `weekly_liquid` | bool | Weekly liquid asset |
| `illiquid` | bool | Illiquid security |
| `demand_feature` | bool | Has demand feature |
| `guarantee` | bool | Has guarantee |
| `enhancement` | bool | Has enhancement |
| `ratings` | `List[CreditRating]` | NRSRO ratings |
| `repo_agreement` | `Optional[RepurchaseAgreement]` | Repo agreement data |

### `CreditRating` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `agency` | str | NRSRO name |
| `rating` | str | Rating string |

### `RepurchaseAgreement` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `open_flag` | bool | Open repo flag |
| `cleared_flag` | bool | Cleared repo flag |
| `tri_party_flag` | bool | Tri-party repo flag |
| `collateral` | `List[CollateralIssuer]` | Collateral issuers |

### `CollateralIssuer` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `issuer_name` | Optional[str] | Collateral issuer name |
| `lei` | Optional[str] | Issuer LEI |
| `cusip` | Optional[str] | CUSIP |
| `maturity_date` | Optional[str] | Maturity date |
| `coupon` | Optional[Decimal] | Coupon (N-MFP3: `coupon` tag; N-MFP2: `couponOrYield` tag) |
| `principal_amount` | Optional[Decimal] | Principal amount |
| `collateral_value` | Optional[Decimal] | Collateral value |
| `collateral_category` | Optional[str] | Category of collateral |

## N-MFP2 vs N-MFP3 Differences
| Aspect | N-MFP2 (2010–mid 2024) | N-MFP3 (June 2024+) |
|--------|------------------------|----------------------|
| Detection | `b'edgar/nmfp2' in xml_bytes` (checked in `_parse_xml()`) | not N-MFP2 |
| `registrant_name` | `""` (tag absent) | populated |
| `series_name` | `""` (tag absent) | populated |
| Yield series | Single scalar `sevenDayGrossYield` | 20 daily `sevenDayGrossYield` elements with dates |
| NAV series | `netAssetValue/fridayWeek1-5` | `dailyNetAssetValuePerShareSeries` with dates |
| Liquidity | `fridayDay1-4` / `fridayWeek1-5` parallel structures | `liquidAssetsDetails` with dates |
| Class flows tag | `fridayWeek1-5` children with `weeklyGrossSubscriptions/Redemptions` | `dialyShareholderFlowReported` (SEC typo in schema) |
| Class yield | Single `sevenDayNetYield` scalar | `sevenDayNetYield` elements with dates |
| CUSIP fallback | `otherUniqueId` when `CUSIPMember` absent | no fallback needed |
| Collateral coupon | `couponOrYield` tag | `coupon` tag |

## Error Paths
| Condition | Behavior |
|-----------|----------|
| `filing.xml()` returns None | `from_filing()` returns None |
| Malformed XML | `XMLParser(recover=True)` fallback |
| Empty securities list | `portfolio_data()` returns empty DataFrame |
| N-MFP2 missing registrant/series name | Fields are empty strings, not None |
| `dialyShareholderFlowReported` typo | Code intentionally matches the SEC schema misspelling |

## Access Patterns

- `filing.obj()` or `MoneyMarketFund.from_filing(filing)`
- `mmf.portfolio_data()` — all holdings
- `mmf.holdings_by_category()` — holdings grouped by investment category
- `mmf.share_class_data()` — per-class NAV/shares/min investment
- `mmf.yield_history()` — 7-day gross yield over time
- `mmf.nav_history()` — NAV per share over time
- `mmf.liquidity_history()` — daily/weekly liquid asset %
- `mmf.collateral_data()` — repo agreement collateral detail
- `mmf.series_info.seven_day_gross_yields` — raw list of yield dicts
- `mmf.share_classes[0].daily_nav` — raw per-class NAV list
