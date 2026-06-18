# Form SC 13G — Passive Beneficial Ownership

**SEC form codes**: `SCHEDULE 13G`, `SCHEDULE 13G/A`, `SC 13G`, `SC 13G/A`
**Python class**: `Schedule13G`
**Access**: `filing.obj()` → `Schedule13G` — or `Schedule13G.from_filing(filing)`
**Base fields**: See `_base-beneficial-ownership.md`
**Source**: `edgar/beneficial_ownership/schedule13.py`, `edgar/beneficial_ownership/models.py`

Filed by institutional investors (mutual funds, ETFs, pensions, index funds) who acquire ≥5% for passive investment without control intent. Simpler disclosures than 13D; mostly structured Y/N flags. `is_passive_investor` is always `True`.

Key XML differences from 13D: no CIK in reporting persons; `<items>` (not `<items1To7>`); `<signatureInformation>` (not `<signatureInfo>`); `memberGroup` (not `memberOfGroup`).

---

## Complete Field Reference

### From `_base-beneficial-ownership.md` (inherited)

Shared fields: `issuer_info`, `security_info`, `reporting_persons`, `signatures`, `amendment_number`, `is_amendment`, `filing_date`, `total_shares`, `total_percent`, `to_context()`.

---

### Schedule13G-Specific Fields

#### Constructor parameters (beyond base)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `event_date` | `str` | required | Date the event triggering this filing occurred |
| `rule_designation` | `Optional[str]` | `None` | Rule under which filed (e.g., `'13d-1(b)'`, `'13d-1(c)'`, `'13d-1(d)'`) |

#### Instance attributes

| Field | Type | Description |
|-------|------|-------------|
| `items` | `Schedule13GItems` | Structured Items 1–10; see below |
| `event_date` | `str` | Event date string |
| `rule_designation` | `Optional[str]` | SEC rule designation for filing eligibility |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `date_of_event` | `str` | Alias for `event_date` (API consistency with `Schedule13D`) |
| `is_passive_investor` | `bool` | Always `True` for 13G |

---

### Class Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing(filing)` | `filing: Filing` | `Optional[Schedule13G]` | Asserts form in `['SCHEDULE 13G', 'SCHEDULE 13G/A', 'SC 13G', 'SC 13G/A']`; calls `filing.xml()`; returns `None` if no XML |
| `parse_xml(xml)` | `xml: str` | `dict` | Static; parses `<edgarSubmission>` XML; returns kwargs dict |

---

## Nested Objects

### Schedule13GItems (frozen dataclass — `models.py`)

All optional text fields default to `None`; all `bool` flags default to `True` (most items are not-applicable for passive filers).

**Item 1 — Name and Address of Issuer**

| Field | Type | Description |
|-------|------|-------------|
| `item1_issuer_name` | `Optional[str]` | Issuer name (from `<issuerName>`) |
| `item1_issuer_address` | `Optional[str]` | Issuer address (from `<issuerPrincipalExecutiveOfficeAddress>`) |

**Item 2 — Name and Address of Person Filing**

| Field | Type | Description |
|-------|------|-------------|
| `item2_filer_names` | `Optional[str]` | Filing person names (from `<filingPersonName>`) |
| `item2_filer_addresses` | `Optional[str]` | Business/residence addresses (from `<principalBusinessOfficeOrResidenceAddress>`) |
| `item2_citizenship` | `Optional[str]` | Citizenship or state of organization (from `<citizenship>`) |

**Item 3 — If the Amount in Row (11) is Less Than 5%**

| Field | Type | Description |
|-------|------|-------------|
| `item3_not_applicable` | `bool` | `True` (default; most 13G filers report ≥5%) |

**Item 4 — Ownership**

| Field | Type | Description |
|-------|------|-------------|
| `item4_amount_beneficially_owned` | `Optional[str]` | Total shares (from `<amountBeneficiallyOwned>`) |
| `item4_percent_of_class` | `Optional[str]` | Ownership percent string (from `<classPercent>`) |
| `item4_sole_voting` | `Optional[str]` | Sole power to vote (from `<solePowerOrDirectToVote>`) |
| `item4_shared_voting` | `Optional[str]` | Shared power to vote (from `<sharedPowerOrDirectToVote>`) |
| `item4_sole_dispositive` | `Optional[str]` | Sole power to dispose (from `<solePowerOrDirectToDispose>`) |
| `item4_shared_dispositive` | `Optional[str]` | Shared power to dispose (from `<sharedPowerOrDirectToDispose>`) |

**Item 5 — Ownership of Five Percent or Less**

| Field | Type | Description |
|-------|------|-------------|
| `item5_not_applicable` | `bool` | `True` if filer owns more than 5% |
| `item5_ownership_5pct_or_less` | `Optional[str]` | Description if applicable (from `<classOwnership5PercentOrLess>`) |

**Item 6 — Ownership of More Than Five Percent on Behalf of Another**

| Field | Type | Description |
|-------|------|-------------|
| `item6_not_applicable` | `bool` | `True` for most passive filers |

**Item 7 — Identification and Classification of Subsidiary**

| Field | Type | Description |
|-------|------|-------------|
| `item7_not_applicable` | `bool` | `True` for most passive filers |

**Item 8 — Identification and Classification of Members of Group**

| Field | Type | Description |
|-------|------|-------------|
| `item8_not_applicable` | `bool` | `True` unless filing as a group |

**Item 9 — Notice Pursuant to Rule 13d-1(k)**

| Field | Type | Description |
|-------|------|-------------|
| `item9_not_applicable` | `bool` | `True` unless Rule 13d-1(k) applies |

**Item 10 — Certification**

| Field | Type | Description |
|-------|------|-------------|
| `item10_certification` | `Optional[str]` | Certification text (from `<certifications>`) |

---

## Reporting Persons — 13G Differences

`ReportingPerson` instances from 13G have these structural differences vs 13D:

| Field | 13D | 13G |
|-------|-----|-----|
| `cik` | Populated from `reportingPersonCIK` | Always `''` (not in XML) |
| `fund_type` | Present | Always `None` |
| `comment` | Present | Always `None` |
| `member_of_group` | From `<memberOfGroup>` | From `<memberGroup>` |
| XML container | `<reportingPersons> > <reportingPersonInfo>` | `<coverPageHeaderReportingPersonDetails>` |

---

## XML Parsing Notes

| Detail | Value |
|--------|-------|
| XML root | `<edgarSubmission>` |
| Items container | `<items>` (vs `<items1To7>` in 13D) |
| Reporting persons container | `<coverPageHeaderReportingPersonDetails>` (repeating) |
| Signature container | `<signatureInformation>` (vs `<signatureInfo>` in 13D) |
| CUSIP source (legacy) | `issuerCusip` (lowercase 'c'; vs `issuerCUSIP` in 13D) |
| CUSIP source (new schema) | `issuerCusipNumber` (same as 13D) |
| Rule designation | `<designateRulesPursuantThisScheduleFiled> > <designateRulePursuantThisScheduleFiled>` |
| Address element | `<issuerPrincipalExecutiveOfficeAddress>` (vs `<address>` in 13D) |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form not in ['SCHEDULE 13G', 'SCHEDULE 13G/A', 'SC 13G', 'SC 13G/A']` | `AssertionError` |
| `filing.xml()` returns `None` | `from_filing()` returns `None` |
| Missing `<edgarSubmission>` | `ValueError` |
| Missing `<coverPageHeader>` | `ValueError` |
| Missing `<items>` | `items` set to `Schedule13GItems()` (all defaults) |

---

## Access Patterns

- `filing.obj()` (dispatched via `edgar.__init__.obj()`)
- `Schedule13G.from_filing(filing)` direct construction
- `schedule.rule_designation` — passive filing rule basis
- `schedule.items.item4_amount_beneficially_owned` — total shares string
- `schedule.items.item4_percent_of_class` — ownership percent string
- `schedule.is_passive_investor` — always `True`
- `schedule.reporting_persons[0].type_of_reporting_person` — filer type (e.g., `'IA'` investment adviser)
- `OwnershipComparison(current=amendment, previous=original)` — compare two filings
- `get_original_filing(schedule)` — retrieve pre-amendment original
