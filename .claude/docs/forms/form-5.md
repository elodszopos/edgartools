# Form 5 — Annual Statement of Beneficial Ownership

**SEC form codes**: `5`, `5/A`
**Python class**: `Form5` (extends `Ownership`)
**Access**: `filing.obj()` → `Form5`
**Base fields**: See `_base-ownership.md` for all shared fields, nested objects, and DataFrame schemas
**Source**: `edgar/ownership/ownershipforms.py:2271`

---

## Form 5 Overview

| Aspect | Detail |
|--------|--------|
| Purpose | Annual catch-all for transactions that were exempt from Form 4 reporting during the year |
| Focus | **Transactions** — same structure as Form 4 |
| Filing deadline | 45 days after fiscal year end |
| Key distinction from Form 4 | Covers exempt transactions (small acquisitions, gifts, inheritances) not previously reported |
| Key distinction from Form 3 | Contains transactions (not just initial holdings) |

---

## Form 5-Specific Behavior

`Form5` is structurally identical to `Form4` — both extend `Ownership` and follow the transaction-focused path. The only runtime distinction is `self.form == "5"`.

### Properties and Methods — Form 5 Behavior

| Field / Method | Form 5 Behavior |
|----------------|----------------|
| `form` | Always `"5"` |
| `non_derivative_table.transactions` | Populated — primary data |
| `derivative_table.transactions` | Populated if exempt derivative transactions occurred |
| `market_trades` | Open market trades (codes P/S); typically rare in Form 5 |
| `get_ownership_summary()` | Returns `TransactionSummary` (same as Form 4) |
| `to_dataframe()` | One row per `TransactionActivity` |
| `__rich__` / HTML render | Same 11-column Table I and 14-column Table II as Form 4 |

### Typical Transaction Codes in Form 5

Form 5 typically contains exempt transaction codes not seen on Form 4:

| Code | Description | Normalized type |
|------|-------------|----------------|
| `G` | Gift | `"gift"` |
| `W` | Inherited (willed) | `"other_acquisition"` or `"other_disposition"` |
| `J` | Other (miscellaneous exempt) | `"other_acquisition"` or `"other_disposition"` |
| `A` | Small acquisition exempt from Form 4 | `"award"` |
| `P` | Late-reported open market purchase | `"purchase"` |
| `S` | Late-reported open market sale | `"sale"` |

All codes map through `TransactionCode.TRANSACTION_TYPES` — see `_base-ownership.md`.

### `TransactionSummary` — Form 5 Summary Object

Identical to Form 4. Returned by `form5.get_ownership_summary()`. See `_base-ownership.md` for full field reference.

Key runtime note for Form 5: `primary_activity` may return unusual values like `"Gift"`, `"Willed"`, or `"Other"` because exempt transactions dominate Form 5 filings.

### HTML Rendering

Identical to Form 4 — uses the same template and same 11-column Table I and 14-column Table II layout. The `form_title_display` context variable is set to `"ANNUAL STATEMENT OF CHANGES IN BENEFICIAL OWNERSHIP"` by `ownership_to_html`.

---

## DataFrame Schema — `to_dataframe()` (Form 5)

Identical to Form 4. See `_base-ownership.md` → "DataFrame Schemas" → "Ownership.to_dataframe() — detailed mode (Form 4/5)".

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| Form 5 with no transactions | `TransactionSummary.transactions = []`; `primary_activity = "No Transactions"` |
| All transactions are exempt/unusual codes | `market_trades` is `None`; `net_change = 0` |
| `has_10b5_1_plan` | Typically `None` — exempt transactions rarely have 10b5-1 footnotes |

---

## Access Patterns

- `filing.obj()` → `Form5`
- `form5.get_transaction_activities()` → `List[TransactionActivity]` — exempt transactions with footnotes resolved
- `form5.get_ownership_summary()` → `TransactionSummary`
- `form5.non_derivative_table.transactions.data` — raw transactions DataFrame
- `form5.to_dataframe()` — one row per transaction with metadata
- `form5.to_context()` — AI context; structure identical to Form 4 context output
- `form5.reporting_period` — fiscal year end date covered by this annual statement
