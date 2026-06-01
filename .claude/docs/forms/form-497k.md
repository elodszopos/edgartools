# Form 497K — Fund Summary Prospectus

**SEC form codes**: 497K
**Python class**: `Prospectus497K`
**Access**: `filing.obj()` -> `Prospectus497K`
**Source**: `edgar/funds/prospectus497k.py`

> No XBRL in 497K filings. Series/class/ticker IDs come from SGML header `<SERIES-AND-CLASSES-CONTRACTS-DATA>` block. All financial data extracted from HTML table parsing (Form N-1A mandated structure).

## Complete Field Reference

### Prospectus497K — Top-Level Fields

#### Instance Attributes (set in `__init__`)
| Attribute | Type | Description |
|-----------|------|-------------|
| `_filing` | `Optional[Filing]` | Source filing |
| `_share_classes` | `List[ShareClassFees]` | Per-class fee/expense data |
| `_performance_returns` | `List[PerformanceReturn]` | Average annual return rows |
| `_best_quarter` | `Optional[Tuple[Decimal, str]]` | (return_pct, date_str) |
| `_worst_quarter` | `Optional[Tuple[Decimal, str]]` | (return_pct, date_str) |
| `_fund_name` | str | Fund name (from HTML metadata or SGML series name) |
| `_prospectus_date` | `Optional[str]` | Prospectus date |
| `_investment_objective` | `Optional[str]` | Investment objective text |
| `_portfolio_turnover` | `Optional[Decimal]` | Portfolio turnover rate |
| `_portfolio_managers` | `List[str]` | Portfolio manager names |
| `_min_investments` | Dict | Minimum investment requirements |
| `_series_id` | `Optional[str]` | Series ID from SGML header |
| `_series_name` | `Optional[str]` | Series name from SGML header |
| `_class_info` | `List[Dict]` | Raw class info from SGML: `[{class_id, name, ticker}]` |
| `_cik` | `Optional[str]` | CIK from SGML header |

#### Properties
| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `filing` | `Optional[Filing]` | no | Source Filing object |
| `fund_name` | str | no | `_fund_name or _series_name or ""` |
| `prospectus_date` | `Optional[str]` | no | Prospectus date |
| `investment_objective` | `Optional[str]` | no | Investment objective text |
| `portfolio_turnover` | `Optional[Decimal]` | no | Portfolio turnover |
| `portfolio_managers` | `List[str]` | no | Portfolio manager names |
| `tickers` | `List[str]` | no | All share class tickers from `_share_classes` |
| `series_id` | `Optional[str]` | no | Series ID (S000xxxxx) from SGML header |
| `class_ids` | `List[str]` | no | Class IDs (C000xxxxx) from `_share_classes` |
| `cik` | `Optional[str]` | no | Fund CIK |
| `share_classes` | `List[ShareClassFees]` | no | All share class fee objects |
| `num_share_classes` | int | no | `len(_share_classes)` |
| `best_quarter` | `Optional[Tuple[Decimal, str]]` | no | (return_pct, date_str) or None |
| `worst_quarter` | `Optional[Tuple[Decimal, str]]` | no | (return_pct, date_str) or None |

#### DataFrame Properties (cached)
| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `fees` | `pd.DataFrame` | cached | Fee data per share class |
| `expense_example` | `pd.DataFrame` | cached | Expense example ($10K hypothetical) |
| `performance` | `pd.DataFrame` | cached | Average annual returns |

#### Methods
| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing(filing)` | `filing: Filing` | `Optional[Prospectus497K]` | Classmethod; calls `filing.html()`, SGML header extraction, HTML table parsing via `_497k_tables.py`; returns None if no HTML |
| `to_context(detail)` | `detail: str = 'standard'` | str | AI-optimized string; levels: 'minimal'/'standard'/'full' |

## DataFrame Schemas

### `fees` DataFrame columns
| Column | Type | Description |
|--------|------|-------------|
| `class_name` | str | Share class name |
| `ticker` | Optional[str] | Class ticker |
| `management_fee` | Optional[Decimal] | Management fee % |
| `twelve_b1_fee` | Optional[Decimal] | 12b-1 distribution fee % |
| `other_expenses` | Optional[Decimal] | Other expenses % |
| `total_annual_expenses` | Optional[Decimal] | Total annual operating expenses % |
| `fee_waiver` | Optional[Decimal] | Fee waiver % |
| `net_expenses` | Optional[Decimal] | Net annual expenses after waiver % |

### `expense_example` DataFrame columns
| Column | Type | Description |
|--------|------|-------------|
| `class_name` | str | Share class name |
| `ticker` | Optional[str] | Class ticker |
| `1yr` | Optional[int] | Cost after 1 year on $10K investment |
| `3yr` | Optional[int] | Cost after 3 years |
| `5yr` | Optional[int] | Cost after 5 years |
| `10yr` | Optional[int] | Cost after 10 years |

### `performance` DataFrame columns
| Column | Type | Description |
|--------|------|-------------|
| `label` | str | Return row label (e.g., class name, benchmark) |
| `section` | str | Section header (share class section) |
| `1yr` | Optional[Decimal] | 1-year average annual return |
| `5yr` | Optional[Decimal] | 5-year average annual return |
| `10yr` | Optional[Decimal] | 10-year average annual return |
| `since_inception` | Optional[Decimal] | Since-inception return |

## Nested Objects

### `ShareClassFees` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `class_name` | str | Share class name |
| `ticker` | Optional[str] | Class ticker symbol |
| `class_id` | Optional[str] | Class/Contract ID (C000xxxxx) from SGML |
| `max_sales_load` | Optional[Decimal] | Maximum sales load (shareholder fee) |
| `max_deferred_sales_load` | Optional[Decimal] | Maximum deferred sales load |
| `redemption_fee` | Optional[Decimal] | Redemption fee |
| `management_fee` | Optional[Decimal] | Management fee % |
| `twelve_b1_fee` | Optional[Decimal] | 12b-1 fee % |
| `other_expenses` | Optional[Decimal] | Other expenses % |
| `acquired_fund_fees` | Optional[Decimal] | Acquired fund fees and expenses % |
| `total_annual_expenses` | Optional[Decimal] | Total annual operating expenses % |
| `fee_waiver` | Optional[Decimal] | Fee waiver/expense reimbursement % |
| `net_expenses` | Optional[Decimal] | Net expenses after waiver % |
| `expense_1yr` | Optional[int] | Expense example: 1 year |
| `expense_3yr` | Optional[int] | Expense example: 3 years |
| `expense_5yr` | Optional[int] | Expense example: 5 years |
| `expense_10yr` | Optional[int] | Expense example: 10 years |

### `PerformanceReturn` (Pydantic)
| Field | Type | Description |
|-------|------|-------------|
| `label` | str | Row label (share class name, benchmark name, etc.) |
| `section` | str | Share class section header context |
| `return_1yr` | Optional[Decimal] | 1-year return |
| `return_5yr` | Optional[Decimal] | 5-year return |
| `return_10yr` | Optional[Decimal] | 10-year return |
| `return_since_inception` | Optional[Decimal] | Since-inception return |
| `inception_date` | Optional[str] | Inception date |

## SGML Header Data (`_class_info` list)
Each entry is a dict with:
| Key | Description |
|-----|-------------|
| `class_id` | C000xxxxx identifier |
| `name` | Class contract name |
| `ticker` | Ticker symbol |

## Error Paths
| Condition | Behavior |
|-----------|----------|
| `filing.html()` returns None | `from_filing()` returns None |
| No `<SERIES-AND-CLASSES-CONTRACTS-DATA>` in SGML | `series_id`, `class_info` are None/empty |
| HTML fee table not found | `_share_classes` is empty; `fees` is empty DataFrame |
| No performance table found | `_performance_returns` is empty |
| `fund_name` not in HTML | Falls back to `_series_name` from SGML header |

## Access Patterns

- `filing.obj()` or `Prospectus497K.from_filing(filing)`
- `p.fees` — fee table as DataFrame (property, not method)
- `p.expense_example` — expense example as DataFrame (property, not method)
- `p.performance` — returns as DataFrame (property, not method)
- `p.best_quarter` — `(Decimal('8.80'), 'December 31, 2023')` tuple
- `p.tickers` — `["VFINX", "VFIAX"]`
- `p.share_classes[0].total_annual_expenses` — raw Decimal
- `p.class_ids` — `["C000002990", "C000002991"]`
