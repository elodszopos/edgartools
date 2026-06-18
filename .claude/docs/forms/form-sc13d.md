# Form SC 13D — Activist Beneficial Ownership

**SEC form codes**: `SCHEDULE 13D`, `SCHEDULE 13D/A`, `SC 13D`, `SC 13D/A`
**Python class**: `Schedule13D`
**Access**: `filing.obj()` → `Schedule13D` — or `Schedule13D.from_filing(filing)`
**Base fields**: See `_base-beneficial-ownership.md`
**Source**: `edgar/beneficial_ownership/schedule13.py`, `edgar/beneficial_ownership/models.py`

Filed when an investor acquires ≥5% of a class of equity with activist or control intent. Requires narrative items 1–7. Signals board seats, M&A, spinoffs, capital allocation demands.

---

## Complete Field Reference

### From `_base-beneficial-ownership.md` (inherited)

Shared fields: `issuer_info`, `security_info`, `reporting_persons`, `signatures`, `amendment_number`, `is_amendment`, `filing_date`, `total_shares`, `total_percent`, `to_context()`.

---

### Schedule13D-Specific Fields

#### Constructor parameters (beyond base)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date_of_event` | `str` | required | Date the event triggering this filing occurred |
| `previously_filed` | `bool` | `False` | From `previouslyFiledFlag` XML element |

#### Instance attributes

| Field | Type | Description |
|-------|------|-------------|
| `items` | `Schedule13DItems` | Narrative Items 1–7; see below |
| `date_of_event` | `str` | Event date string (e.g., `'2024-01-15'`) |
| `previously_filed` | `bool` | Whether a prior filing was made |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `event_date` | `str` | Alias for `date_of_event` (API consistency with `Schedule13G`) |

---

### Class Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing(filing)` | `filing: Filing` | `Optional[Schedule13D]` | Asserts form in `['SCHEDULE 13D', 'SCHEDULE 13D/A', 'SC 13D', 'SC 13D/A']`; calls `filing.xml()`; returns `None` if no XML |
| `parse_xml(xml)` | `xml: str` | `dict` | Static; parses `<edgarSubmission>` XML; returns kwargs dict for constructor |

---

## Nested Objects

### Schedule13DItems (frozen dataclass — `models.py`)

All fields are `Optional[str]` unless noted. All default to `None`.

**Item 1 — Security and Issuer**

| Field | Type | Description |
|-------|------|-------------|
| `item1_security_title` | `Optional[str]` | Class of securities (from `<securityTitle>`) |
| `item1_issuer_name` | `Optional[str]` | Issuer name (from `<issuerName>`) |
| `item1_issuer_address` | `Optional[str]` | Issuer principal address — comma-joined street/city/state/zip string (from `<issuerPrincipalAddress>`) |

**Item 2 — Identity and Background**

| Field | Type | Description |
|-------|------|-------------|
| `item2_filing_persons` | `Optional[str]` | Filing person names (from `<filingPersonName>`) |
| `item2_business_address` | `Optional[str]` | Principal business address (from `<principalBusinessAddress>`) |
| `item2_principal_occupation` | `Optional[str]` | Occupation or employment (from `<principalJob>`) |
| `item2_convictions` | `Optional[str]` | Criminal convictions during past 5 years (from `<convictionDescription>`) |
| `item2_citizenship` | `Optional[str]` | Citizenship or incorporation state (from `<citizenship>`) |

**Item 3 — Source and Amount of Funds**

| Field | Type | Description |
|-------|------|-------------|
| `item3_source_of_funds` | `Optional[str]` | Description of fund sources (from `<fundsSource>`); e.g., `'WC'` (working capital), `'BK'` (bank loan) |

**Item 4 — Purpose of Transaction (most analytically important)**

| Field | Type | Description |
|-------|------|-------------|
| `item4_purpose_of_transaction` | `Optional[str]` | Narrative description of investment purpose (from `<transactionPurpose>`); key activist signal |

**Item 5 — Interest in Securities**

| Field | Type | Description |
|-------|------|-------------|
| `item5_percentage_of_class` | `Optional[str]` | Percentage of class owned (from `<percentageOfClassSecurities>`) |
| `item5_number_of_shares` | `Optional[str]` | Number of shares (from `<numberOfShares>`) |
| `item5_transactions` | `Optional[str]` | Recent transactions description (from `<transactionDesc>`) |
| `item5_shareholders` | `Optional[str]` | List of other shareholders in group (from `<listOfShareholders>`) |
| `item5_date_5pct_ownership` | `Optional[str]` | Date ownership reached 5% (from `<date5PercentOwnership>`) |

**Item 6 — Contracts and Arrangements**

| Field | Type | Description |
|-------|------|-------------|
| `item6_contracts` | `Optional[str]` | Description of contracts/arrangements/understandings (from `<contractDescription>`) |

**Item 7 — Material Exhibits**

| Field | Type | Description |
|-------|------|-------------|
| `item7_exhibits` | `Optional[str]` | List of exhibits filed (from `<filedExhibits>`) |

---

## XML Parsing Notes

| Detail | Value |
|--------|-------|
| XML root | `<edgarSubmission>` |
| Items container | `<items1To7>` |
| Reporting persons container | `<reportingPersons> > <reportingPersonInfo>` |
| Signature container | `<signatureInfo> > <signaturePerson> > <signatureDetails>` |
| CUSIP source (legacy) | `issuerCUSIP` (flat) |
| CUSIP source (new schema) | `issuerCusipNumber` (nested) |
| Group membership field | `memberOfGroup` (vs `memberGroup` in 13G) |
| CIK field | `reportingPersonCIK` (present in 13D; absent in 13G) |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form not in ['SCHEDULE 13D', 'SCHEDULE 13D/A', 'SC 13D', 'SC 13D/A']` | `AssertionError` |
| `filing.xml()` returns `None` | `from_filing()` returns `None` |
| Missing `<edgarSubmission>` | `ValueError` |
| Missing `<coverPageHeader>` | `ValueError` |
| Missing `<items1To7>` | `items` set to `Schedule13DItems()` (all `None`) |

---

## Access Patterns

- `filing.obj()` (dispatched via `edgar.__init__.obj()`)
- `Schedule13D.from_filing(filing)` direct construction
- `schedule.items.item4_purpose_of_transaction` — primary activist signal
- `schedule.reporting_persons[0].type_of_reporting_person` — filer type code
- `schedule.total_percent` — max-based aggregate ownership percent
- `OwnershipComparison(current=amendment, previous=original)` — compare two filings
- `get_original_filing(schedule)` — retrieve pre-amendment original
