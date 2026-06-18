# Form 3 — Initial Statement of Beneficial Ownership

**SEC form codes**: `3`, `3/A`
**Python class**: `Form3` (extends `Ownership`)
**Access**: `filing.obj()` → `Form3`
**Base fields**: See `_base-ownership.md` for all shared fields, nested objects, and DataFrame schemas
**Source**: `edgar/ownership/ownershipforms.py:2249`

---

## Form 3 Overview

| Aspect | Detail |
|--------|--------|
| Purpose | Filed when an insider first becomes subject to reporting (new director, officer, or 10% owner) |
| Focus | **Holdings** — what the insider owns, not transactions |
| Filing trigger | New association with the company (not a transaction) |
| Key distinction from Form 4 | Contains `holdings` (not transactions) in both non-derivative and derivative tables |
| `no_securities` | Can be `True` — valid Form 3 with no holdings reported |

---

## Form 3-Specific Behavior

All fields and methods are inherited from `Ownership`. Behavior diverges from Form 4/5 in these ways:

### Properties and Methods — Form 3 Behavior

| Field / Method | Form 3 Behavior |
|----------------|----------------|
| `form` | Always `"3"` |
| `non_derivative_table.holdings` | Populated — this is where the holdings live |
| `non_derivative_table.transactions` | Empty `NonDerivativeTransactions` DataFrame |
| `derivative_table.holdings` | Populated if insider holds derivatives |
| `derivative_table.transactions` | Empty `DerivativeTransactions` |
| `market_trades` | Always `None` (no transactions) |
| `derivative_trades` | Always `None` (no transactions) |
| `get_ownership_summary()` | Returns `InitialOwnershipSummary` (not `TransactionSummary`) |
| `extract_form3_holdings()` | Primary Form 3 accessor — merges non-derivative + derivative holdings into `List[SecurityHolding]` |
| `to_dataframe()` | Delegates to `InitialOwnershipSummary.to_dataframe()` — one row per holding |
| `to_dataframe(detailed=False)` | Single summary row with `Total Shares`, `Has Derivatives`, `Holdings` count |
| `__rich__` / HTML render | Shows holdings tables (Table I and Table II); no transaction columns |

### `InitialOwnershipSummary` — Form 3 Summary Object

Returned by `form3.get_ownership_summary()`. See `_base-ownership.md` for full field reference.

Key Form 3 fields:

| Field | Type | Description |
|-------|------|-------------|
| `holdings` | `List[SecurityHolding]` | All holdings (non-derivative + derivative combined) |
| `no_securities` | `bool` | `True` when filed with no holdings |
| `total_shares` | `int` | Sum of non-derivative shares |
| `has_derivatives` | `bool` | Any derivative holdings present |

### DataFrame Schema — `to_dataframe()` (Form 3, detailed=True)

One row per holding. See `_base-ownership.md` → "DataFrame Schemas" section for full column list.

Additional column present only in derivative holding rows:

| Column | Description |
|--------|-------------|
| `Underlying Security` | Underlying title |
| `Underlying Shares` | Underlying share count |
| `Exercise Price` | Conversion/exercise price |
| `Exercise Date` | Exercisable date |
| `Expiration Date` | Expiration date |

### HTML Rendering — Table I (Non-Derivative, Form 3)

Template renders 4 columns (not 11 as in Form 4/5):

| Column | Description |
|--------|-------------|
| Security Title | `Security` |
| Amount | `Shares` |
| Direct/Indirect | `DirectIndirect` code |
| Nature of Ownership | `NatureOfOwnership` |

### HTML Rendering — Table II (Derivative, Form 3)

Template fills transaction-only columns (`N/A`) for Form 3. Populated columns:

| Column | Description |
|--------|-------------|
| Security Title | `Security` |
| Conversion/Exercise Price | `ExercisePrice` |
| Exercisable/Expiration Date | `ExerciseDate - ExpirationDate` |
| Title and Amount of Underlying | `Underlying - UnderlyingShares` |
| Direct/Indirect | `DirectIndirect` |
| Nature of Ownership | `Nature Of Ownership` |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `no_securities = True` | `InitialOwnershipSummary.to_dataframe()` returns metadata row with `Total Shares = 0`, `Holdings = 0` |
| No holdings and `no_securities = False` | Same as above — `to_dataframe()` returns empty-looking row |
| `extract_form3_holdings()` on empty tables | Returns `[]` |

---

## Access Patterns

- `filing.obj()` → `Form3`
- `form3.no_securities` — check before accessing holdings
- `form3.extract_form3_holdings()` → `List[SecurityHolding]` — primary Form 3 accessor
- `form3.non_derivative_table.holdings.data` — raw common stock holdings DataFrame
- `form3.derivative_table.holdings.data` — raw derivative holdings DataFrame
- `form3.get_ownership_summary()` → `InitialOwnershipSummary`
- `form3.to_dataframe()` — one row per holding with metadata
- `form3.reporting_owners[0].position` — insider role at time of initial filing
