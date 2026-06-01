# Form N-CSR — Fund Shareholder Report

**SEC form codes**: N-CSR, N-CSR/A, N-CSRS, N-CSRS/A
**Python class**: `FundShareholderReport`
**Access**: `filing.obj()` -> `FundShareholderReport`
**Source**: `edgar/funds/ncsr.py`

> Unlike all other fund forms, N-CSR uses Inline XBRL (`oef:` taxonomy) via `filing.xbrl()`, NOT raw XML. Share classes are discovered dynamically via `oef:ClassAxis` dimension queries.

## Complete Field Reference

### FundShareholderReport — Top-Level Fields

#### Instance Attributes (set in `__init__`)
| Attribute | Type | Description |
|-----------|------|-------------|
| `_fund_name` | str | Fund name from XBRL `oef:FundName` |
| `_report_type` | str | "Annual" (N-CSR) or "Semi-Annual" (N-CSRS) |
| `_net_assets` | Optional[Decimal] | From `oef:NetAssetsOfSeriesMember` or `oef:NetAssets` |
| `_portfolio_turnover` | Optional[Decimal] | From `oef:PortfolioTurnoverRt` or `us-gaap:InvestmentCompanyPortfolioTurnover` |
| `share_classes` | `List[ShareClassInfo]` | Per-class data extracted from OEF taxonomy |
| `_filing` | `Optional[Filing]` | Source filing (set post-construction) |
| `_cik` | `Optional[str]` | From `str(filing.cik)` (set post-construction) |
| `_series_id` | `Optional[str]` | From `filing.header.series_id` (set post-construction) |

#### Properties
| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `filing` | `Optional[Filing]` | no | Source Filing object |
| `cik` | `Optional[str]` | no | Fund company CIK |
| `series_id` | `Optional[str]` | no | Series ID from filing header |
| `fund_name` | str | no | Fund name |
| `report_type` | str | no | "Annual" or "Semi-Annual" |
| `is_annual` | bool | no | `report_type == "Annual"` |
| `net_assets` | `Optional[Decimal]` | no | Fund net assets |
| `portfolio_turnover` | `Optional[Decimal]` | no | Portfolio turnover rate |
| `num_share_classes` | int | no | `len(self.share_classes)` |

#### Methods
| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing(filing)` | `filing: Filing` | `Optional[FundShareholderReport]` | Classmethod; calls `filing.xbrl()`; determines Annual/Semi-Annual from "CSRS" in form name; sets `_cik`, `_series_id`, `_filing` post-construction |
| `performance_data()` | — | `pd.DataFrame` | Annual returns across all share classes; cached |
| `expense_data()` | — | `pd.DataFrame` | Expense ratios and fees per class; cached |
| `holdings_data()` | — | `pd.DataFrame` | Top holdings per class; cached |
| `to_context(detail)` | `detail: str = 'standard'` | str | AI-optimized string; levels: 'minimal'/'standard'/'full' |

## DataFrame Schemas

### `performance_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `class_name` | str | Share class name |
| `ticker` | Optional[str] | Share class ticker |
| `period` | str | Period label (from ColumnAxis or period_end) |
| `return_pct` | Optional[float] | Average annual return % |
| `inception_date` | Optional[str] | Inception date (when available) |

### `expense_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `class_name` | str | Share class name |
| `ticker` | Optional[str] | Share class ticker |
| `expense_ratio_pct` | Optional[float] | Expense ratio % (from `oef:ExpenseRatioPct` or `oef:ExpensesPctOfAvgNetAssets`) |
| `expenses_paid` | Optional[float] | Actual expenses paid (from `oef:ExpensesPaidAmt`) |
| `advisory_fees_paid` | Optional[float] | Advisory fees paid (from `oef:AdvisoryFeesPaidAmt`) |

### `holdings_data()` columns
| Column | Type | Description |
|--------|------|-------------|
| `class_name` | str | Share class name |
| `holding` | str | Holding name (derived from HoldingAxis member ID) |
| `pct_of_nav` | Optional[float] | % of NAV (from `oef:HoldingPctOfNav`) |
| `pct_of_total_inv` | Optional[float] | % of total investments (if present) |

## Nested Objects

### `ShareClassInfo` (Pydantic, ncsr.py)
| Field | Type | Description |
|-------|------|-------------|
| `class_name` | str | Class name (from `oef:ClassName`, `oef:ClassNameDerived`, `oef:ShareClassNm`, or derived from member ID) |
| `class_ticker` | Optional[str] | Class ticker (from `oef:ClassTicker`) |
| `expense_ratio_pct` | Optional[Decimal] | Expense ratio % |
| `expenses_paid_amt` | Optional[Decimal] | Expenses paid amount |
| `advisory_fees_paid` | Optional[Decimal] | Advisory fees paid |
| `annual_returns` | `List[AnnualReturn]` | Annual return records |
| `holdings` | `List[Holding]` | Top holding records |
| `holdings_count` | Optional[int] | Total holdings count (from `oef:HoldingsCount`) |

### `AnnualReturn` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `period_label` | str | Period label (ColumnAxis or period_end date) |
| `return_pct` | Optional[Decimal] | Return % |
| `inception_date` | Optional[str] | Inception date |

### `Holding` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Holding name (derived from HoldingAxis member ID) |
| `pct_of_nav` | Optional[Decimal] | % of NAV |
| `pct_of_total_inv` | Optional[Decimal] | % of total investments |

## XBRL Concepts Queried
| Concept | Usage |
|---------|-------|
| `oef:FundName` | Fund name (undimensioned) |
| `oef:NetAssetsOfSeriesMember` | Net assets (first fallback: `oef:NetAssets`) |
| `oef:PortfolioTurnoverRt` | Portfolio turnover (first fallback: `us-gaap:InvestmentCompanyPortfolioTurnover`) |
| `oef:ClassAxis` | Dimension for share class discovery |
| `oef:ClassTicker` | Per-class ticker |
| `oef:ClassName` / `oef:ClassNameDerived` / `oef:ShareClassNm` | Class name (tried in order) |
| `oef:ExpenseRatioPct` | Expense ratio (fallback: `oef:ExpensesPctOfAvgNetAssets`) |
| `oef:ExpensesPaidAmt` | Expenses paid |
| `oef:AdvisoryFeesPaidAmt` | Advisory fees |
| `oef:AvgAnnlRtrPct` | Average annual return |
| `oef:HoldingPctOfNav` | Top holding % NAV |
| `oef:HoldingsCount` | Number of holdings |

## Error Paths
| Condition | Behavior |
|-----------|----------|
| `filing.xbrl()` returns None | `from_filing()` returns None |
| No `oef:ClassAxis` dimension facts | Falls back to `_parse_undimensioned_share_class()` |
| Undimensioned fallback with no data | No share class created (empty `share_classes`) |
| Malformed return/holding fact | Warning logged; fact skipped |
| `_cik` and `_series_id` | Set post-construction; None if `filing.header` lacks them |

## Access Patterns

- `filing.obj()` or `FundShareholderReport.from_filing(filing)`
- `report.performance_data()` — annual returns by class
- `report.expense_data()` — expense ratios by class
- `report.holdings_data()` — top holdings by class
- `report.share_classes` — raw `List[ShareClassInfo]`
- `report.share_classes[0].annual_returns` — raw `List[AnnualReturn]`
- `report.is_annual` — True for N-CSR, False for N-CSRS
