# Form 13F-HR — Institutional Holdings Report

**SEC form codes**: `13F-HR`, `13F-HR/A`, `13F-NT`, `13F-NT/A`, `13F-CTR`, `13F-CTR/A`
**Python class**: `ThirteenF`
**Access**: `filing.obj()` → `ThirteenF` — or `ThirteenF(filing)`
**Source**: `edgar/thirteenf/models.py`

Only `13F-HR` and `13F-HR/A` have an infotable (`has_infotable()` returns `True` for these only). `13F-NT` is a notice-only form; `primary_form_information` may be populated but `infotable`/`holdings` are `None`.

---

## Complete Field Reference

### Filing fields (inherited)

See `core-filing-access.md`. Key passthrough: `filing.cik`, `filing.company`, `filing.form`, `filing.filing_date`, `filing.accession_no`.

---

### ThirteenF-Specific Fields

#### Constructor

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filing` | `Filing` | required | Filing with form in `THIRTEENF_FORMS`; asserted |
| `use_latest_period_of_report` | `bool` | `False` | Resolve to last same-day same-form filing |

#### Immediate attributes (set in `__init__`)

| Field | Type | Description |
|-------|------|-------------|
| `filing` | `Filing` | The resolved filing (may differ from input if `use_latest_period_of_report=True`) |
| `primary_form_information` | `Optional[PrimaryDocument13F]` | Parsed primary XML; `None` for pre-2013 TXT-only filings |

#### Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `form` | `str` | no | `filing.form` passthrough |
| `accession_number` | `str` | no | `filing.accession_no` passthrough |
| `report_period` | `Optional[str]` | no | YYYY-MM-DD; from primary XML or `filing.period_of_report` |
| `filing_date` | `str` | no | YYYY-MM-DD formatted |
| `investment_manager` | `Optional[FilingManager]` | no | Legal management entity (name + address); `None` for TXT-only |
| `management_company_name` | `str` | no | Manager legal name; falls back to `filing.company` for TXT-only |
| `filing_signer_name` | `Optional[str]` | no | Individual who signed (typically administrative, not portfolio manager) |
| `filing_signer_title` | `Optional[str]` | no | Signer's business title |
| `manager_name` | `str` | no | **DEPRECATED** — emits `DeprecationWarning`; alias for `management_company_name` |
| `signer` | `Optional[str]` | no | Raw signer name from `primary_form_information.signature.name` |
| `total_value` | `Optional[Decimal]` | no | Total portfolio value in dollars; auto-converts from thousands when `_value_in_thousands` is True |
| `total_holdings` | `Optional[int]` | no | Count of holdings; from primary XML or `len(infotable)` |
| `other_managers` | `list[OtherManager]` | no | Co-reporting managers from `summaryPage.other_managers`; `[]` if none |
| `_value_in_thousands` | `bool` | no | Per-filing detection (see below); `True` when values are in thousands and must be ×1000 scaled |
| `_report_period_dt` | `Optional[datetime]` | no | Internal `datetime` for comparisons |

#### cached_property fields

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `infotable_xml` | `Optional[str]` | cached | Raw XML of info table attachment; `None` if TXT or no infotable |
| `infotable_txt` | `Optional[str]` | cached | Raw TXT of info table attachment; `None` if XML format |
| `infotable_html` | `Optional[str]` | cached | HTML info table attachment content (rare) |
| `infotable` | `Optional[pd.DataFrame]` | cached/network | Disaggregated holdings by manager — ALL columns below; unit detection + ×1000 normalization runs here |
| `holdings` | `Optional[pd.DataFrame]` | cached/network | Aggregated by CUSIP+PutCall — ALL columns below; checks `_cache_provider` first |
| `_schema_version` | `Optional[str]` | cached | Primary-document `<schemaVersion>` (e.g. `'X0202'`); `None` for pre-2013 or missing element |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `has_infotable()` | — | `bool` | `True` only for `13F-HR` and `13F-HR/A` |
| `previous_holding_report()` | — | `Optional[ThirteenF]` | Prior quarter; searches `Company.get_filings(latest=40)`, prefers 30–200 day gap; result manually cached |
| `holdings_view(display_limit=200)` | `display_limit: int` | `Optional[HoldingsView]` | Renderable/iterable wrapper around `infotable_summary()`; `None` if no holdings |
| `compare_holdings(display_limit=200)` | `display_limit: int` | `Optional[HoldingsComparison]` | QoQ outer-merge on CUSIP with share/value deltas and Status labels; `None` if no previous |
| `holding_history(periods=3, display_limit=100)` | `periods: int`, `display_limit: int` | `Optional[HoldingsHistory]` | Multi-quarter wide DataFrame; deduplicated by `report_period` |
| `get_portfolio_managers(include_approximate=False)` | `include_approximate: bool` | `list[dict]` | Curated lookup from `edgar/reference/data/portfolio_managers.json`; empty list if unknown fund |
| `get_manager_info_summary()` | — | `dict` | Keys: `from_13f_filing`, `external_sources`, `limitations` |
| `is_filing_signer_likely_portfolio_manager()` | — | `bool` | Heuristic: title-based check; `True` for CEO/CIO/PM titles |
| `to_context(detail='standard')` | `detail: str` | `str` | AI context; `'minimal'` ~100 tokens, `'standard'` ~300, `'full'` ~500+ |
| `set_cache_provider(provider)` | `provider: callable` | `None` | Class method; `provider(accession_no) -> DataFrame|None`; avoids expensive `infotable` load |

---

## DataFrame Schemas

### `infotable` columns (disaggregated — one row per manager-security pair)

| Column | Type | Description |
|--------|------|-------------|
| `Issuer` | `str` | Issuer name (`nameOfIssuer`) |
| `Class` | `str` | Security class (`titleOfClass`) |
| `Cusip` | `str` | 9-character CUSIP |
| `Value` | `int` | Market value in dollars (normalized via per-filing unit detection; raw XML may be in thousands or whole dollars) |
| `PutCall` | `str` | `''` (non-option), `'PUT'`, or `'CALL'` |
| `InvestmentDiscretion` | `str` | `'SOLE'`, `'DEFINED'`, or `'OTHER'` |
| `OtherManager` | `str` | Manager sequence number(s); for multi-manager filings |
| `SharesPrnAmount` | `int` | Share count or principal amount |
| `Type` | `str` | `'Shares'` or `'Principal'` |
| `SoleVoting` | `int` | Shares with sole voting authority |
| `SharedVoting` | `int` | Shares with shared voting authority |
| `NonVoting` | `int` | Shares with no voting authority |
| `Ticker` | `str` | Ticker mapped via `cusip_ticker_mapping()`; `NaN` if CUSIP not in reference |

### `holdings` columns (aggregated — one row per CUSIP+PutCall)

Same columns as `infotable` **except**: `OtherManager` and `InvestmentDiscretion` are dropped (manager-specific). `Type` and `PutCall` become `pd.Categorical` to save memory. Put/Call positions are kept as distinct rows (grouped by `Cusip`+`PutCall`) so option positions do not collapse into the underlying equity row (#828).

| Column | Type | Notes |
|--------|------|-------|
| `Cusip` | `str` | Part of group key |
| `Issuer` | `str` | First value across managers |
| `Class` | `str` | First value |
| `Ticker` | `str` | First value |
| `PutCall` | `Categorical` | Part of group key; categories: `['', 'Put', 'Call']` (title-case from SEC XML) |
| `SharesPrnAmount` | `int` | **Summed** across managers within same Cusip+PutCall |
| `Value` | `int` | **Summed** across managers; sorted descending |
| `SoleVoting` | `int` | **Summed** |
| `SharedVoting` | `int` | **Summed** |
| `NonVoting` | `int` | **Summed** |
| `Type` | `Categorical` | Categories: `['Shares', 'Principal', '-']`; first value |

### `compare_holdings()` DataFrame columns (`HoldingsComparison.data`)

| Column | Type | Description |
|--------|------|-------------|
| `Cusip` | `str` | Merge key |
| `Ticker` | `str` | Coalesced current/previous |
| `Issuer` | `str` | Coalesced current/previous |
| `Shares` | `float` | Current `SharesPrnAmount`; `NaN` for CLOSED positions |
| `Value` | `float` | Current market value; `NaN` for CLOSED |
| `PrevShares` | `float` | Previous quarter shares; `NaN` for NEW positions |
| `PrevValue` | `float` | Previous quarter value; `NaN` for NEW |
| `ShareChange` | `float` | `Shares - PrevShares`; `NaN` for NEW/CLOSED |
| `ShareChangePct` | `float` | Percent change; `NaN` when no previous shares |
| `ValueChange` | `float` | `Value - PrevValue`; `NaN` for NEW/CLOSED |
| `ValueChangePct` | `float` | Percent change; `NaN` when no previous value |
| `Status` | `str` | `'NEW'`, `'CLOSED'`, `'INCREASED'`, `'DECREASED'`, `'UNCHANGED'` |

### `holding_history()` DataFrame columns (`HoldingsHistory.data`)

| Column | Type | Description |
|--------|------|-------------|
| `Cusip` | `str` | Security identifier |
| `Ticker` | `str` | From most recent period |
| `Issuer` | `str` | From most recent period |
| `<YYYY-MM-DD>` | `float` | One column per period (e.g., `2024-09-30`); share count; `NaN` = not held |

---

## Nested Objects

### PrimaryDocument13F

`ThirteenF.primary_form_information` — `None` for pre-2013 TXT-only filings.

| Field | Type | Description |
|-------|------|-------------|
| `report_period` | `datetime` | Period end date (parsed from `%m-%d-%Y` format in XML) |
| `cover_page` | `CoverPage` | Cover page data |
| `summary_page` | `SummaryPage` | Summary totals and other managers |
| `signature` | `Signature` | Filing signer information |
| `additional_information` | `str` | Free-text `additionalInformation` element |

### CoverPage (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `report_calendar_or_quarter` | `str` | Reporting calendar or quarter string |
| `report_type` | `str` | Report type (e.g., `'13F-HR'`) |
| `filing_manager` | `FilingManager` | Legal entity name and address |
| `other_managers` | `List[OtherManager]` | Co-reporting managers from the cover page; use `SummaryPage.other_managers` for consolidated filings |

### SummaryPage (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `other_included_managers_count` | `int` | Count of co-reporting managers |
| `total_value` | `Decimal` | Raw total from XML (may be in thousands for pre-Q4-2022; `ThirteenF.total_value` normalizes) |
| `total_holdings` | `int` | Total number of holdings entries |
| `other_managers` | `Optional[List[OtherManager]]` | Parsed from `<summaryPage><otherManagers2Info>`; `None` if absent |

### FilingManager (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Legal entity name of the investment manager |
| `address` | `Address` | Registered address (street1, street2, city, state_or_country, zipcode) |

### OtherManager (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `str` | CIK of the co-reporting manager |
| `name` | `str` | Legal name |
| `file_number` | `str` | SEC file number (form 13F file number) |
| `sequence_number` | `Optional[int]` | Sequence number from `<otherManager2>` |

### Signature (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Full name of signer |
| `title` | `str` | Business title |
| `phone` | `str` | Contact phone number |
| `signature` | `str` | Electronic signature value |
| `city` | `str` | City of signing |
| `state_or_country` | `str` | State or country code |
| `date` | `str` | Signature date string |

### HoldingsView

Renderable/iterable wrapper for holdings display.

| Attribute | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | The summary DataFrame from `infotable_summary()` |
| `display_limit` | `int` | Max rows in Rich display |
| `__len__()` | `int` | Row count |
| `__iter__()` | yields `dict` | Each row as column-keyed dict |
| `__getitem__(int)` | `dict` | Row dict by index |
| `__getitem__(slice)` | `pd.DataFrame` | Slice of underlying DataFrame |

### HoldingsComparison

| Attribute | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Full comparison DataFrame; see schema above |
| `current_period` | `str` | Current quarter period string |
| `previous_period` | `str` | Previous quarter period string |
| `manager_name` | `str` | `management_company_name` |
| `display_limit` | `int` | Max rows in Rich display |
| `__len__()` | `int` | Total row count (NEW + CLOSED + changed + unchanged) |
| `__iter__()` | yields `dict` | Each row as dict |
| `__getitem__(int)` | `dict` | Row dict |
| `__getitem__(slice)` | `pd.DataFrame` | Slice |

### HoldingsHistory

| Attribute | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Wide DataFrame; fixed cols: Cusip, Ticker, Issuer; then one col per period |
| `periods` | `list[str]` | Period strings ordered oldest→newest |
| `manager_name` | `str` | `management_company_name` |
| `display_limit` | `int` | Max rows in Rich display |
| `__len__()` | `int` | Row count |
| `__iter__()` | yields `dict` | Each row as dict |
| `__getitem__(int)` | `dict` | Row dict |
| `__getitem__(slice)` | `pd.DataFrame` | Slice |

---

## Value Unit Detection

`_detect_value_in_thousands()` runs once per filing when `infotable` is first built. Result cached in `_value_in_thousands_flag`. Logic in `edgar/thirteenf/models.py`:

| Step | Condition | Decision |
|------|-----------|----------|
| 1 — Price heuristic (decisive high) | ≥50% of `Type=='Shares'` non-option rows imply price < $1.00 | **Thousands** — majority sub-$1 is unambiguous |
| 2 — Price heuristic (low = ambiguous) | <50% sub-$1 rows | Defer to step 3 |
| 3 — Schema version prior | `_schema_version >= 'X0202'` → whole-dollar era schema | **Dollars** |
| 3 — Schema version prior | `_schema_version < 'X0202'` → pre-transition schema | **Thousands** |
| 3 — Schema version absent | `_schema_version` is `None` | Defer to step 4 |
| 4 — Date fallback | `report_period <= 2022-09-30` | **Thousands** |
| 4 — Date fallback | `report_period > 2022-09-30` | **Dollars** |

No priceable equity rows (bond/PRN-only filings) skip step 1 and go directly to step 3.

`_value_in_thousands` property: returns `_value_in_thousands_flag` if set by `infotable` build; for 13F-NT (no infotable) falls back to `_resolve_unit_fallback(schema_version, report_period_dt)`.

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form not in THIRTEENF_FORMS` | `AssertionError` in `__init__` |
| Pre-2013 TXT-only filing | `primary_form_information` is `None`; `total_value`/`total_holdings` computed from `infotable` |
| No infotable attachment found | `infotable` returns `None`; `holdings` returns `None` |
| No INFORMATION TABLE attachment found (HTML type) | `infotable_html` raises `IndexError` — no bounds check on `attachments[0]` |
| `_cache_provider` raises | Silently falls through to normal `infotable` computation |
| No previous filing found | `previous_holding_report()` returns `None`; `compare_holdings()` returns `None` |
| Empty `infotable` | `holdings` returns `None`; `holdings_view()` returns `None` |
| `13F-NT` form | `has_infotable()` is `False`; `infotable`/`holdings` are `None`; unit detection uses schema+date fallback |
| Bond/PRN-only filing (no priceable equity rows) | Price heuristic skipped; unit falls back to schema version then date cutoff |

---

## Access Patterns

- `filing.obj()` or `ThirteenF(filing)` for standard access
- `ThirteenF(filing, use_latest_period_of_report=True)` when a manager files multiple 13Fs same day
- `t.holdings` — aggregated DataFrame (recommended for most analysis)
- `t.infotable` — disaggregated (needed for multi-manager inspection)
- `t.holdings_view()` — for terminal display
- `t.compare_holdings()` — QoQ delta; `result.data` for the full DataFrame
- `t.holding_history(periods=4)` — multi-quarter wide DataFrame
- `t.primary_form_information.cover_page.filing_manager.name` — manager legal name
- `t.primary_form_information.signature.title` — signer title
- `ThirteenF.set_cache_provider(fn)` — wire Redis/external cache at class level
