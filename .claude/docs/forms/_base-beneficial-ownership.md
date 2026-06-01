# Base: Beneficial Ownership (Schedule 13D / 13G)

Shared model for `Schedule13D` (`edgar/beneficial_ownership/schedule13.py`) and `Schedule13G` (`edgar/beneficial_ownership/schedule13.py`). Both classes are structurally parallel; differences are documented in their individual form docs.

**Sources**:
- `edgar/beneficial_ownership/schedule13.py`
- `edgar/beneficial_ownership/models.py`
- `edgar/beneficial_ownership/amendments.py`

---

## Shared Constructor Fields

Both classes store identical field names. XML element names differ between 13D and 13G.

| Field | Type | Description |
|-------|------|-------------|
| `_filing` | `Filing` | Internal reference (not public); accessed via `is_amendment`, `filing_date` |
| `issuer_info` | `IssuerInfo` | Subject company — CIK, name, CUSIP, address |
| `security_info` | `SecurityInfo` | Security class title and CUSIP |
| `reporting_persons` | `List[ReportingPerson]` | All filers; one entry per co-filing entity |
| `items` | `Schedule13DItems` or `Schedule13GItems` | Form-specific narrative items |
| `signatures` | `List[Signature]` | One per reporting person |
| `amendment_number` | `Optional[int]` | From `extract_amendment_number(filing.form)`; `None` for bare `/A` |

13D constructor has `date_of_event: str` and `previously_filed: bool`.
13G constructor has `event_date: str` and `rule_designation: Optional[str]`.

---

## Shared Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_amendment` | `bool` | `'/A' in self._filing.form` |
| `filing_date` | `date` | `self._filing.filing_date` |
| `total_shares` | `int` | `max(p.aggregate_amount for p in included_persons)` — excludes `is_aggregate_exclude_shares=True` persons; `0` if no persons |
| `total_percent` | `float` | `max(p.percent_of_class for p in included_persons)` — same exclusion logic |

**Critical**: `total_shares` uses `max()`, not `sum()` — co-filers in one filing always report overlapping ownership. `OwnershipComparison.shares_change` uses `sum()` (comparing two separate filings).

---

## Shared Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `to_context(detail='standard')` | `detail: str` | `str` | AI context; `'minimal'` ~100 tokens, `'standard'` ~300, `'full'` ~500+ |

---

## Nested Objects

### ReportingPerson (frozen dataclass — `models.py`)

Each individual or entity reporting beneficial ownership. Multiple entries = joint filers (group formation).

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `str` | SEC CIK; always `''` in 13G (not in XML) |
| `name` | `str` | Legal name |
| `citizenship` | `str` | Citizenship or state/country of organization |
| `sole_voting_power` | `int` | Shares with exclusive voting power |
| `shared_voting_power` | `int` | Shares with shared voting power |
| `sole_dispositive_power` | `int` | Shares with exclusive dispositive power |
| `shared_dispositive_power` | `int` | Shares with shared dispositive power |
| `aggregate_amount` | `int` | Total beneficial ownership share count |
| `percent_of_class` | `float` | Ownership as percent of class |
| `type_of_reporting_person` | `str` | SEC type code (e.g., `'IN'` individual, `'HC'` holding company, `'IA'` investment adviser) |
| `fund_type` | `Optional[str]` | Fund classification; 13D only; `None` in 13G |
| `comment` | `Optional[str]` | Free-text comment; 13D only |
| `member_of_group` | `Optional[str]` | `'a'` = group member (joint filer); `'b'` = separate filer; XML element differs: `memberOfGroup` (13D) vs `memberGroup` (13G) |
| `is_aggregate_exclude_shares` | `bool` | `True` = exclude from `total_shares`/`total_percent` aggregation |
| `no_cik` | `bool` | `True` if person has no assigned CIK |

**Computed properties on `ReportingPerson`**:

| Property | Returns | Description |
|----------|---------|-------------|
| `total_voting_power` | `int` | `sole_voting_power + shared_voting_power` |
| `total_dispositive_power` | `int` | `sole_dispositive_power + shared_dispositive_power` |

### IssuerInfo (frozen dataclass — `models.py`)

Subject company whose securities are reported.

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `str` | Issuer CIK; from `issuerCIK` (13D) or `issuerCik` (13G) |
| `name` | `str` | Issuer legal name |
| `cusip` | `str` | 9-character CUSIP; from `issuerCUSIP` or `issuerCusipNumber` (13D); `issuerCusip` or `issuerCusipNumber` (13G) |
| `address` | `Optional[Address]` | Registered office address; `None` if absent from XML |

### SecurityInfo (frozen dataclass — `models.py`)

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | Security class title (e.g., `'Common Stock'`) |
| `cusip` | `str` | 9-character CUSIP (populated from `IssuerInfo` during parse) |

### Signature (frozen dataclass — `models.py`)

One per reporting person. Structure differs between 13D (`signatureInfo > signaturePerson`) and 13G (`signatureInformation`).

| Field | Type | Description |
|-------|------|-------------|
| `reporting_person` | `str` | Name of the reporting person (link to `ReportingPerson`) |
| `signature` | `str` | Electronic signature value |
| `title` | `str` | Signer's title |
| `date` | `str` | Signature date string |

---

## Amendment & Comparison Objects (`amendments.py`)

### AmendmentInfo (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `is_amendment` | `bool` | `True` if `/A` in `filing.form` |
| `amendment_number` | `Optional[int]` | Parsed from `filing.form`; defaults to `1` for bare `/A` |
| `original_accession` | `Optional[str]` | Populated separately; `None` by default from `from_filing()` |

**Factory**: `AmendmentInfo.from_filing(filing)` — extracts from `filing.form`.

### OwnershipComparison (dataclass)

Compare two `Schedule13D` or `Schedule13G` instances (typically original vs amendment).

| Field | Type | Description |
|-------|------|-------------|
| `current` | `Schedule13D | Schedule13G` | Newer filing |
| `previous` | `Schedule13D | Schedule13G` | Older filing |

| Property | Type | Description |
|----------|------|-------------|
| `shares_change` | `int` | `sum(current persons) - sum(previous persons)` — uses `sum()` (cross-filing comparison) |
| `percent_change` | `float` | `sum(current pcts) - sum(previous pcts)` |
| `is_accumulating` | `bool` | `shares_change > 0` |
| `is_liquidating` | `bool` | `shares_change < 0` |
| `is_unchanged` | `bool` | `shares_change == 0` |
| `get_summary()` | `dict` | Keys: `previous_filing_date`, `current_filing_date`, `previous_shares`, `current_shares`, `shares_change`, `previous_percent`, `current_percent`, `percent_change`, `is_accumulating`, `is_liquidating`, `is_unchanged` |

---

## Module-Level Helpers (`amendments.py`)

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `get_amendment_info(schedule)` | `schedule` | `AmendmentInfo` | Calls `AmendmentInfo.from_filing(schedule._filing)` |
| `get_original_filing(schedule)` | `schedule` | `Optional[Schedule13D|13G]` | Finds pre-amendment original via `filing.related_filings(filing_date=..., amendments=False)[-1]`; `None` if not amendment or not found |
| `compare_to_previous(schedule, previous=None)` | `schedule`, `previous` | `Optional[OwnershipComparison]` | Auto-fetches original if `previous=None`; `None` if not found |

---

## Gotchas

- **Bare `/A` amendment number discrepancy**: Two code paths produce different values for the same filing. `extract_amendment_number(filing.form)` (used by the schedule constructor) returns `None` for a bare `/A` form (e.g. `SC 13D/A` with no number). `AmendmentInfo.from_filing(filing)` (used by amendment helpers) defaults to `1` for bare `/A`. Code that mixes both paths will see `amendment_number = None` on the schedule object and `amendment_number = 1` from `AmendmentInfo`.

## Error Paths

| Condition | Behavior |
|-----------|----------|
| Wrong form type | `AssertionError` in `from_filing()` |
| No XML in filing | `from_filing()` returns `None` |
| Missing `<edgarSubmission>` | `ValueError("Invalid XML: missing <edgarSubmission> root element")` |
| Missing `<coverPageHeader>` | `ValueError("Invalid XML: missing <coverPageHeader>")` |
| Empty `reporting_persons` | `total_shares` and `total_percent` return `0` / `0.0` |
| All persons have `is_aggregate_exclude_shares=True` | `total_shares` and `total_percent` return `0` / `0.0` |
| `get_original_filing` network fails | Returns `None` (exception caught silently) |
