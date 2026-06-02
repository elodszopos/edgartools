# Form 4 — Statement of Changes in Beneficial Ownership

**SEC form codes**: `4`, `4/A`
**Python class**: `Form4` (extends `Ownership`)
**Access**: `filing.obj()` → `Form4`
**Base fields**: See `_base-ownership.md` for all shared fields, nested objects, and DataFrame schemas
**Source**: `edgar/ownership/ownershipforms.py:2260`

---

## Form 4 Overview

| Aspect | Detail |
|--------|--------|
| Purpose | Reports every change in insider ownership (purchases, sales, awards, exercises, etc.) |
| Focus | **Transactions** — the changes that occurred |
| Filing deadline | 2 business days after the transaction |
| Most common form | The most frequently filed ownership form |
| Key distinction | Contains `transactions` (not just holdings) in both tables |

---

## Form 4-Specific Behavior

All fields and methods are inherited from `Ownership`. Behavior diverges from Form 3 in these ways:

### Properties and Methods — Form 4 Behavior

| Field / Method | Form 4 Behavior |
|----------------|----------------|
| `form` | Always `"4"` |
| `non_derivative_table.transactions` | Populated — primary data |
| `non_derivative_table.holdings` | May also be populated (holdings reported on Form 4 when not previously filed) |
| `derivative_table.transactions` | Populated for option exercises, grants of derivative securities, etc. |
| `derivative_table.holdings` | May be populated |
| `market_trades` | Filtered subset of `non_derivative_table.transactions` with `Code in ('P', 'S')` |
| `derivative_trades` | `DataHolder` wrapping `derivative_table.transactions.data`; `None` if empty |
| `get_ownership_summary()` | Returns `TransactionSummary` (not `InitialOwnershipSummary`) |
| `to_dataframe()` | One row per `TransactionActivity` |
| `to_dataframe(detailed=False)` | Single summary row with aggregated counts and values |
| `__rich__` | Renders via `TransactionSummary.__rich__()`: 7 columns for non-derivative (Type, Code, Description, Shares, Price, Value, Ownership) and 5 columns for derivative (Type, Code, Shares, Underlying, Expiration) |
| HTML render (`_repr_html_`) | Table I: 11 columns (non-derivative); Table II: 14 columns (derivative). See HTML Rendering sections below |

### Key Transaction Identification

Form 4 is commonly used to identify:

| Transaction | Code | Normalized `transaction_type` |
|-------------|------|-------------------------------|
| Open market purchase | `P` | `"purchase"` |
| Open market sale | `S` | `"sale"` |
| Grant / award | `A` | `"award"` |
| Option exercise | `M` | `"exercise"` |
| In-the-money/at-the-money derivative exercise | `X` | `"other_acquisition"` / `"other_disposition"` (non-deriv, based on AcquiredDisposed) or `"derivative_purchase"` / `"derivative_sale"` (deriv) |
| Tax withholding | `F` | `"tax"` |
| Gift | `G` | `"gift"` |
| Derivative acquisition | `A`, `C`, etc. on derivative table | `"derivative_purchase"` |
| Derivative disposition | `D`, etc. on derivative table | `"derivative_sale"` |

### 10b5-1 Plan Detection

Form 4 is the primary source for 10b5-1 plan detection. The detection chain:

1. `get_transaction_activities()` resolves footnote IDs → `footnotes_text` per `TransactionActivity`
2. `TransactionActivity.is_10b5_1_plan` calls `detect_10b5_1_plan(footnotes_text)` from `edgar/ownership/core.py:202`
3. `TransactionSummary.has_10b5_1_plan` aggregates across all activities
4. `to_context(detail='full')` emits `"10b5-1 Plan: Yes/No"` line

Patterns detected: `"10b5-1"`, `"10b-5-1"`, `"rule 10b5"`, `"rule 10b-5"`, `"10b5 plan"`, `"10b-5 plan"`

### `TransactionSummary` — Form 4 Summary Object

Returned by `form4.get_ownership_summary()`. See `_base-ownership.md` for full field reference.

Key Form 4 fields:

| Field | Type | Description |
|-------|------|-------------|
| `transactions` | `List[TransactionActivity]` | All normalized transaction events |
| `remaining_shares` | `Optional[int]` | Last `Remaining` value from market trades or all transactions |
| `has_derivative_transactions` | `bool` | `True` if derivative table has transactions |
| `net_change` | `int` | `purchase_shares - sale_shares` |
| `net_value` | `float` | `purchase_value - sale_value` |
| `primary_activity` | `str` | Dominant activity label |
| `has_10b5_1_plan` | `Optional[bool]` | Aggregated plan detection |

### HTML Rendering — Table I (Non-Derivative, Form 4/5)

Template renders 11 columns:

| Column | Source Field | Description |
|--------|-------------|-------------|
| Security Title | `Security` | |
| Transaction Date | `Date` | |
| Deemed Execution Date | `DeemedDate` | Not a real DataFrame column; `html_render.py` uses `.get('DeemedDate', '')` which always returns empty string. Do not access as a DataFrame column. |
| Transaction Code | `Code` | |
| V | `V` | Not a real DataFrame column; `html_render.py` uses `.get('V', '')` which always returns empty string. Do not access as a DataFrame column. |
| Amount | `Shares` | |
| A or D | `AcquiredDisposed` | |
| Price | `Price` | |
| Amount Owned After | `Remaining` | |
| Direct/Indirect | `DirectIndirect` | |
| Nature of Ownership | `NatureOfOwnership` | |

Holdings rows (when present in Form 4) fill transaction-specific columns with empty strings and use `Remaining` for the "Amount Owned After" column.

### HTML Rendering — Table II (Derivative, Form 4/5)

14 columns rendered:

| Column | Source Field | Description |
|--------|-------------|-------------|
| Security Title | `Security` | |
| Conversion/Exercise Price | `ExercisePrice` | |
| Transaction Date | `Date` | |
| Deemed Execution Date | `DeemedDate` | Not a real DataFrame column; `html_render.py` uses `.get('DeemedDate', '')` which always returns empty string. Do not access as a DataFrame column. |
| Transaction Code | `Code` | |
| V | `V` | Not a real DataFrame column; `html_render.py` uses `.get('V', '')` which always returns empty string. Do not access as a DataFrame column. |
| Amount | `Shares` | |
| A or D | `AcquiredDisposed` | |
| Exercisable/Expiration Date | `ExerciseDate - ExpirationDate` | Combined |
| Title and Amount of Underlying | `Underlying - UnderlyingShares` | Combined |
| Price | `Price` | |
| Amount Owned After | `Remaining` | |
| Direct/Indirect | `DirectIndirect` | |
| Nature of Ownership | `NatureOfOwnership` | |

---

## DataFrame Schema — `to_dataframe()` (Form 4, detailed=True)

See `_base-ownership.md` → "DataFrame Schemas" → "Ownership.to_dataframe() — detailed mode (Form 4/5)".

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| Filing has only derivative transactions | `market_trades` is `None`; `common_stock_purchases/sales` return empty DataFrame |
| All `Price` values are `NaN` | `value` field in all `TransactionActivity` is `0`; `net_value = 0` |
| `remaining_shares` not in market trades | Falls back to last `Remaining` in `non_derivative_table.transactions.data` |
| No transactions at all | `TransactionSummary.transactions = []`; `primary_activity = "No Transactions"` |
| Footnote ID embedded in shares string | `shares_numeric` strips via `safe_numeric()` → may return `None` |

---

## Access Patterns

- `filing.obj()` → `Form4`
- `form4.market_trades` — DataFrame of open market buys and sells (codes P and S)
- `form4.market_trades[form4.market_trades.AcquiredDisposed == 'A']` — purchases only
- `form4.get_transaction_activities()` → `List[TransactionActivity]` — fully resolved with footnotes
- `form4.get_ownership_summary()` → `TransactionSummary`
- `ts = form4.get_ownership_summary()` then `ts.has_10b5_1_plan`, `ts.net_change`, `ts.primary_activity`
- `form4.derivative_table.transactions.data` — raw derivative transactions DataFrame
- `form4.to_dataframe()` — one row per transaction with issuer/insider metadata
- `form4.to_dataframe(detailed=False)` — aggregated summary row
- `form4.to_context(detail='full')` — full AI context including 10b5-1 flag and derivative detail
