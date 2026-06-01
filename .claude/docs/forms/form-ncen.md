# Form N-CEN — Fund Annual Census

**SEC form codes**: N-CEN, N-CEN/A
**Python class**: `FundCensus`
**Access**: `filing.obj()` -> `FundCensus`
**Source**: `edgar/funds/ncen.py`

## Complete Field Reference

### FundCensus — Top-Level Fields

#### Instance Attributes (set in `__init__`)
| Attribute | Type | Description |
|-----------|------|-------------|
| `report_date` | str | Reporting period end date |
| `is_period_lt_12_months` | bool | Reporting period less than 12 months |
| `registrant` | `RegistrantInfo` | Fund company name, CIK, address, governance |
| `series` | `List[FundSeriesInfo]` | All series reported in this filing |
| `signature_info` | `Optional[SignatureInfo]` | Signer name, title, date |
| `_filing` | `Optional[Filing]` | Source filing |

#### Properties
| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `filing` | `Optional[Filing]` | no | Source Filing object |
| `name` | str | no | From `registrant.name` |
| `cik` | str | no | From `registrant.cik` |
| `lei` | Optional[str] | no | From `registrant.lei` |
| `series_ids` | `List[str]` | no | All `series_id` values from `self.series` |
| `series_id` | Optional[str] | no | First series ID; None if no series |
| `num_series` | int | no | `len(self.series)` |
| `total_series` | Optional[int] | no | From `registrant.total_series` (XML field) |
| `classification_type` | Optional[str] | no | From `registrant.classification_type` |
| `is_etf_company` | bool | no | True if any series has `etf_info is not None` |

#### Methods
| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing(filing)` | `filing: Filing` | `Optional[FundCensus]` | Classmethod; calls `filing.xml()` then `_parse_xml()` |
| `series_data()` | — | `pd.DataFrame` | Series overview; cached |
| `service_providers()` | — | `pd.DataFrame` | All providers across all series; cached |
| `broker_data()` | — | `pd.DataFrame` | Broker/broker-dealer commissions; cached |
| `director_data()` | — | `pd.DataFrame` | Board directors; cached |
| `etf_data()` | — | `pd.DataFrame` | ETF-specific series data; cached |
| `to_context(detail)` | `detail: str = 'standard'` | str | AI-optimized string; levels: 'minimal'/'standard'/'full' |

## DataFrame Schemas

### `series_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Series name |
| `series_id` | str | Series ID (S000xxxxx) |
| `lei` | Optional[str] | Series LEI |
| `fund_type` | Optional[str] | Fund type string |
| `avg_net_assets` | Optional[Decimal] | Monthly average net assets |
| `aggregate_commission` | Optional[Decimal] | Aggregate commissions paid |
| `num_advisers` | int | Number of investment advisers |
| `num_custodians` | int | Number of custodians |
| `has_etf` | bool | Whether this series has ETF data |

### `service_providers()` columns
| Column | Type | Description |
|--------|------|-------------|
| `series_name` | str | Parent series name |
| `series_id` | str | Parent series ID |
| `role` | str | Provider role (adviser/custodian/transfer agent/administrator/pricing service/shareholder servicing) |
| `provider_name` | str | Provider name |
| `lei` | Optional[str] | Provider LEI |
| `affiliated` | bool | Is affiliated with fund |

### `broker_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `series_name` | str | Parent series name |
| `series_id` | str | Parent series ID |
| `type` | str | "broker-dealer" or "broker" |
| `broker_name` | str | Broker/broker-dealer name |
| `lei` | Optional[str] | Broker LEI |
| `commission` | Optional[Decimal] | Commission paid |

### `director_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Director name |
| `crd_number` | Optional[str] | CRD number (None replaces "N/A" sentinel) |
| `interested_person` | bool | Is interested person under ICA |

### `etf_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `series_name` | str | Series name |
| `series_id` | str | Series ID |
| `exchange` | Optional[str] | Exchange name |
| `ticker` | Optional[str] | ETF ticker |
| `creation_unit_size` | Optional[Decimal] | Creation unit share count |
| `avg_pct_purchased_in_kind` | Optional[Decimal] | Avg % purchased in-kind |
| `avg_pct_redeemed_in_kind` | Optional[Decimal] | Avg % redeemed in-kind |
| `is_in_kind` | bool | Is an in-kind ETF |
| `num_authorized_participants` | int | Number of authorized participants |

## Nested Objects

### `RegistrantInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Registrant full name |
| `cik` | str | CIK |
| `lei` | Optional[str] | Registrant LEI |
| `file_number` | Optional[str] | Investment Company Act file number |
| `street1` | Optional[str] | Address street 1 |
| `street2` | Optional[str] | Address street 2 |
| `city` | Optional[str] | City |
| `state` | Optional[str] | State |
| `country` | Optional[str] | Country |
| `zip_code` | Optional[str] | ZIP/postal code |
| `phone` | Optional[str] | Phone |
| `classification_type` | Optional[str] | Fund classification type |
| `total_series` | Optional[int] | Total series registered |
| `directors` | `List[Director]` | Board directors |
| `cco_name` | Optional[str] | Chief Compliance Officer name |
| `cco_crd` | Optional[str] | CCO CRD number |
| `accountant` | `Optional[Accountant]` | Public accountant |
| `underwriter_name` | Optional[str] | Principal underwriter name |

### `FundSeriesInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Series name |
| `series_id` | str | Series ID (S000xxxxx) |
| `lei` | Optional[str] | Series LEI |
| `fund_type` | Optional[str] | Fund type |
| `is_diversified` | Optional[bool] | Diversified status (derived from `isNonDiversifiedCompany` flag inversion) |
| `avg_net_assets` | Optional[Decimal] | Monthly average net assets |
| `aggregate_commission` | Optional[Decimal] | Aggregate commissions |
| `is_securities_lending` | bool | Engages in securities lending |
| `advisers` | `List[ServiceProvider]` | Investment advisers |
| `custodians` | `List[ServiceProvider]` | Custodians |
| `transfer_agents` | `List[ServiceProvider]` | Transfer agents |
| `admins` | `List[ServiceProvider]` | Administrators |
| `pricing_services` | `List[ServiceProvider]` | Pricing services |
| `shareholder_servicing_agents` | `List[ServiceProvider]` | Shareholder servicing agents |
| `broker_dealers` | `List[BrokerDealer]` | Broker-dealers |
| `brokers` | `List[BrokerDealer]` | Brokers (separate list from broker-dealers in N-CEN) |
| `principal_transactions` | `List[PrincipalTransaction]` | Principal transactions |
| `securities_lending` | `List[SecuritiesLending]` | Securities lending agents |
| `line_of_credit` | `Optional[LineOfCredit]` | Line of credit info |
| `liquidity_providers` | `List[LiquidityProvider]` | Liquidity classification service providers |
| `etf_info` | `Optional[ETFInfo]` | ETF-specific data (merged from exchangeSeriesInfo section) |

### `ServiceProvider` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Provider name |
| `role` | str | Role label |
| `lei` | Optional[str] | LEI |
| `file_number` | Optional[str] | File number |
| `crd_number` | Optional[str] | CRD number (None replaces "N/A" sentinels) |
| `is_affiliated` | bool | Affiliated with fund |

### `BrokerDealer` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Broker/broker-dealer name |
| `file_number` | Optional[str] | File number |
| `crd_number` | Optional[str] | CRD number |
| `lei` | Optional[str] | LEI |
| `commission` | Optional[Decimal] | Commission amount |

### `PrincipalTransaction` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Principal name |
| `file_number` | Optional[str] | File number |
| `crd_number` | Optional[str] | CRD number |
| `total_purchase_sale` | Optional[Decimal] | Total purchase/sale amount |

### `SecuritiesLending` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `agent_name` | Optional[str] | Lending agent name |
| `agent_lei` | Optional[str] | Agent LEI |
| `is_affiliated` | bool | Agent is affiliated |
| `is_indemnified` | bool | Fund is indemnified by agent |

### `LineOfCredit` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `has_line_of_credit` | bool | Has an existing line of credit |
| `is_committed` | Optional[str] | Committed or uncommitted |
| `size` | Optional[Decimal] | Line of credit size |
| `institution_names` | `List[str]` | Institution names providing credit |

### `LiquidityProvider` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Liquidity classification service name |
| `lei` | Optional[str] | LEI |
| `is_affiliated` | bool | Is affiliated |
| `asset_classes` | `List[str]` | Asset class types covered |

### `ETFInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `series_id` | str | Series ID (matches management series) |
| `fund_name` | str | Fund name |
| `exchange` | Optional[str] | Exchange name |
| `ticker` | Optional[str] | ETF ticker symbol |
| `creation_unit_size` | Optional[Decimal] | Shares per creation unit |
| `avg_pct_purchased_in_kind` | Optional[Decimal] | Avg % of creation units purchased in-kind |
| `avg_pct_redeemed_in_kind` | Optional[Decimal] | Avg % of redemptions in-kind |
| `std_dev_purchased_in_kind` | Optional[Decimal] | Std dev of in-kind purchases |
| `std_dev_redeemed_in_kind` | Optional[Decimal] | Std dev of in-kind redemptions |
| `is_in_kind` | bool | Is an in-kind ETF |
| `authorized_participants` | `List[AuthorizedParticipant]` | APs for this ETF |

### `AuthorizedParticipant` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | AP name |
| `lei` | Optional[str] | AP LEI |
| `file_number` | Optional[str] | File number |
| `crd_number` | Optional[str] | CRD number |
| `purchase_value` | Optional[Decimal] | Value of creation units purchased |
| `redeem_value` | Optional[Decimal] | Value of creation units redeemed |

### `Director` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Director name |
| `crd_number` | Optional[str] | CRD number |
| `is_interested_person` | bool | Interested person status |

### `Accountant` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Public accountant name |
| `pcaob_number` | Optional[str] | PCAOB registration number |
| `lei` | Optional[str] | Accountant LEI |

### `SignatureInfo` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `registrant_name` | Optional[str] | Registrant signed name |
| `signed_date` | Optional[str] | Date signed |
| `signer` | Optional[str] | Signer name |
| `title` | Optional[str] | Signer title |

## Error Paths
| Condition | Behavior |
|-----------|----------|
| `filing.xml()` returns None | `from_filing()` returns None |
| No `managementInvestmentQuestionSeriesInfo` | `self.series` is empty list |
| ETF series not in management series | `etf_info` remains None (no merge target) |
| CRD number "N/A" in XML | `_clean_na()` converts to None |
| No directors | `director_data()` returns empty DataFrame |

## Access Patterns

- `filing.obj()` or `FundCensus.from_filing(filing)`
- `census.series_data()` — series overview
- `census.service_providers()` — all advisers/custodians/etc.
- `census.broker_data()` — broker commissions
- `census.director_data()` — board of directors
- `census.etf_data()` — ETF series details
- `census.registrant.directors` — raw `List[Director]`
- `census.series[0].advisers` — raw `List[ServiceProvider]` for first series
- `census.series[0].etf_info.authorized_participants` — APs for ETF series
