# Form C — Crowdfunding Offering (Regulation CF)

**SEC form codes**: `C`, `C/A`, `C-U`, `C-U/A`, `C-AR`, `C-AR/A`, `C-TR`
**Python class**: `FormC`
**Access**: `filing.obj()` → `FormC`
**Base fields**: See `_base-filing.md`
**Source**: `edgar/offerings/formc.py`

---

## Complete Field Reference

### From Filing (inherited)
See `_base-filing.md`

### FormC-Specific Fields

#### Instance Attributes (set in `__init__`)

| Field | Type | Description |
|-------|------|-------------|
| `filer_information` | `FilerInformation` | Pydantic frozen model; filer CIK, flags, period |
| `issuer_information` | `IssuerInformation` | Pydantic model; issuer name, address, portal, legal info |
| `offering_information` | `Optional[OfferingInformation]` | Pydantic model; `None` for C-AR forms and when XML tag is empty |
| `annual_report_disclosure` | `Optional[AnnualReportDisclosure]` | Pydantic model; `None` for C-TR and often for C-U |
| `signature_info` | `SignatureInfo` | Pydantic model; issuer + person signatures |
| `form` | `str` | Raw form code string from filing (e.g. `"C"`, `"C/A"`) |
| `_filing` | `Optional[Filing]` | Set by `from_filing`; `None` when constructed via `from_xml` directly |

#### Properties — Immediate (no network)

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `description` | `str` | no | Human-readable form name (e.g. "Form C/A - Offering Amendment") |
| `portal_file_number` | `Optional[str]` | no | Funding portal's 007-XXXXX file number; `None` for C-AR forms |
| `issuer_name` | `str` | no | `issuer_information.name` shortcut |
| `issuer_cik` | `str` | no | `filer_information.cik` shortcut |
| `portal_name` | `Optional[str]` | no | Funding portal name; `None` if no portal |
| `portal_cik` | `Optional[str]` | no | Funding portal CIK; `None` if no portal |
| `days_to_deadline` | `Optional[int]` | no | Days until `offering_information.deadline_date`; negative if expired; `None` if no deadline or no offering_information |
| `is_expired` | `bool` | no | True if `days_to_deadline < 0` |
| `campaign_status` | `str` | no | "Terminated" / "Annual Report" / "Progress Update" / "Active (Amendment)" / "Active (Initial)" |
| `docs` | `Docs` | no | Interactive API documentation object |

#### Cached Properties

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `issuer` | `IssuerCompany` | cached | `IssuerCompany(cik, name)`; wraps filer CIK + issuer name |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing: Filing` | `Optional[FormC]` | Primary entry point; calls `filing.xml()`, delegates to `from_xml`; sets `_filing` |
| `from_xml` | `offering_xml: str, form: str` | `FormC` | BeautifulSoup XML parser; `form` populates `description` and `campaign_status` |
| `get_offering` | — | `Offering` | Returns complete lifecycle `Offering` object; requires `_filing` to be set |
| `get_issuer_company` | — | `IssuerCompany` | Deprecated alias for `issuer` property |
| `to_context` | `detail='standard', filing_date=None` | `str` | AI-optimized text; detail: `'minimal'`/`'standard'`/`'full'` |
| `parse_date` | `date_str: str` | `date` | Static; parses MM-DD-YYYY format; raises `ValueError` on mismatch |
| `format_date` | `date_value: date` | `str` | Static; formats as "April 1, 2021" |

#### Module-level Helpers

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `group_offerings_by_file_number` | `filings: EntityFilings` | `Dict[str, EntityFilings]` | Groups Form C filings by 020-XXXXX issuer file number using PyArrow |

---

## Nested Objects

### `FilerInformation` (Pydantic, frozen)

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `str` | Filer CIK |
| `ccc` | `str` | CIK Confirmation Code (populated from `filerCik` element) |
| `confirming_copy_flag` | `bool` | From `confirmingCopyFlag` XML element |
| `return_copy_flag` | `bool` | From `returnCopyFlag` XML element |
| `override_internet_flag` | `bool` | From `overrideInternetFlag` XML element |
| `live_or_test` | `bool` | True if `testOrLive == 'LIVE'` |
| `period` | `Optional[date]` | Period of report; parsed via `FormC.parse_date` |

**Note**: `FilerInformation.company` is a `@property` decorated with `@lru_cache(maxsize=1)` — returns `Company(self.cik)`.

### `IssuerInformation` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Issuer company name |
| `address` | `Address` | Business address |
| `website` | `str` | `issuerWebsite` XML element |
| `co_issuer` | `bool` | `isCoIssuer` flag |
| `funding_portal` | `Optional[FundingPortal]` | Intermediary portal; `None` when `commissionCik` absent |
| `legal_status` | `str` | `legalStatusForm` (e.g. "Limited Liability Company") |
| `jurisdiction` | `str` | `jurisdictionOrganization` state code |
| `date_of_incorporation` | `date` | Parsed from `dateIncorporation` via `FormC.parse_date` |

**Computed property**: `incorporated -> str` — `"{date_of_incorporation} {jurisdiction}"`.

### `FundingPortal` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Portal company name |
| `cik` | `str` | Portal CIK (from `commissionCik`) |
| `crd` | `Optional[str]` | FINRA CRD number |
| `file_number` | `str` | 007-XXXXX SEC file number |

### `OfferingInformation` (Pydantic) — `None` for C-AR forms

| Field | Type | Description |
|-------|------|-------------|
| `compensation_amount` | `str` | Portal compensation description |
| `financial_interest` | `Optional[str]` | Portal financial interest |
| `security_offered_type` | `Optional[str]` | Security type (e.g. "Equity", "Debt", "Other") |
| `security_offered_other_desc` | `Optional[str]` | Description when type is "Other" |
| `no_of_security_offered` | `Optional[str]` | Raw string; use `number_of_securities` property for int |
| `price` | `Optional[str]` | Raw price string; use `price_per_security` property for float |
| `price_determination_method` | `Optional[str]` | How price was determined |
| `offering_amount` | `Optional[float]` | Target (minimum) offering amount in dollars |
| `over_subscription_accepted` | `Optional[str]` | `'Y'` or `'N'` |
| `over_subscription_allocation_type` | `Optional[str]` | How over-subscriptions are allocated |
| `desc_over_subscription` | `Optional[str]` | Description of over-subscription plan |
| `maximum_offering_amount` | `Optional[float]` | Maximum offering amount in dollars |
| `deadline_date` | `Optional[date]` | Offering close date; parsed via `maybe_date` |

**Computed properties on OfferingInformation**:

| Property | Type | Description |
|----------|------|-------------|
| `security_description` | `str` | Combined type + other_desc |
| `target_amount` | `Optional[float]` | Alias for `offering_amount` |
| `price_per_security` | `Optional[float]` | `float(price)` or `None` |
| `number_of_securities` | `Optional[int]` | `int(float(no_of_security_offered))` or `None` |
| `percent_to_maximum` | `Optional[float]` | `(offering_amount / maximum_offering_amount) * 100`; `None` if either is zero |
| `target_offering_amount` | `Optional[float]` | Alias for `offering_amount` |
| `offering_deadline` | `Optional[date]` | Alias for `deadline_date` |

### `AnnualReportDisclosure` (Pydantic) — `None` for C-TR, often for C-U

**Two-year financial data** (most_recent and prior fiscal year fields):

| Field | Type | Description |
|-------|------|-------------|
| `current_employees` | `int` | `currentEmployees` |
| `total_asset_most_recent_fiscal_year` | `float` | Total assets, current year |
| `total_asset_prior_fiscal_year` | `float` | Total assets, prior year |
| `cash_equi_most_recent_fiscal_year` | `float` | Cash & equivalents, current |
| `cash_equi_prior_fiscal_year` | `float` | Cash & equivalents, prior |
| `act_received_most_recent_fiscal_year` | `float` | Accounts receivable, current |
| `act_received_prior_fiscal_year` | `float` | Accounts receivable, prior |
| `short_term_debt_most_recent_fiscal_year` | `float` | Short-term debt, current |
| `short_term_debt_prior_fiscal_year` | `float` | Short-term debt, prior |
| `long_term_debt_most_recent_fiscal_year` | `float` | Long-term debt, current |
| `long_term_debt_prior_fiscal_year` | `float` | Long-term debt, prior |
| `revenue_most_recent_fiscal_year` | `float` | Revenue, current |
| `revenue_prior_fiscal_year` | `float` | Revenue, prior |
| `cost_goods_sold_most_recent_fiscal_year` | `float` | COGS, current |
| `cost_goods_sold_prior_fiscal_year` | `float` | COGS, prior |
| `tax_paid_most_recent_fiscal_year` | `float` | Taxes paid, current |
| `tax_paid_prior_fiscal_year` | `float` | Taxes paid, prior |
| `net_income_most_recent_fiscal_year` | `float` | Net income, current |
| `net_income_prior_fiscal_year` | `float` | Net income, prior |
| `offering_jurisdictions` | `List[str]` | State codes from `<issueJurisdictionSecuritiesOffering>` elements |

**Computed properties on AnnualReportDisclosure**:

| Property | Type | Description |
|----------|------|-------------|
| `is_offered_in_all_states` | `bool` | `offering_jurisdictions` is superset of all state codes |
| `total_debt_most_recent` | `float` | short-term + long-term current year |
| `total_debt_prior` | `float` | short-term + long-term prior year |
| `debt_to_asset_ratio` | `Optional[float]` | `(total_debt_most_recent / total_asset_most_recent) * 100`; `None` if zero assets |
| `revenue_growth_yoy` | `Optional[float]` | `((curr - prior) / prior) * 100`; `None` if prior is zero |
| `is_pre_revenue` | `bool` | `revenue_most_recent_fiscal_year == 0` |
| `burn_rate_change` | `Optional[float]` | `net_income_current - net_income_prior` |
| `asset_growth_yoy` | `Optional[float]` | YoY asset growth %; `None` if prior is zero |

**Convenience aliases** (most_recent fiscal year):
`total_assets`, `cash_and_cash_equivalents`, `accounts_receivable`, `short_term_debt`, `long_term_debt`, `revenues`, `cost_of_goods_sold`, `taxes_paid`, `net_income`, `number_of_employees`

### `SignatureInfo` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `issuer_signature` | `IssuerSignature` | Entity-level signature |
| `signatures` | `List[PersonSignature]` | Individual officer signatures |

**Computed property**: `signers -> List[Signer]` — deduplicates by signature name, collects unique titles.

### `IssuerSignature` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `issuer` | `str` | Issuer entity name |
| `title` | `str` | Officer title |
| `signature` | `str` | `/s/ Name` text |

### `PersonSignature` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `signature` | `str` | `/s/ Name` text |
| `title` | `str` | Officer title |
| `date` | `date` | Signature date; parsed via `FormC.parse_date` |

### `Signer` (Pydantic) — returned by `SignatureInfo.signers`

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Signer name (from signature field) |
| `titles` | `List[str]` | All unique titles for this signer |

### `IssuerCompany` (plain class)

| Attribute | Type | Description |
|-----------|------|-------------|
| `cik` | `str` | Issuer CIK |
| `name` | `str` | Issuer name from Form C |

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `as_company` | — | `Company` | Converts to full `Company` object; instance-cached via `_company` attribute |
| `get_offerings` | — | `List[Offering]` | All Form C filings grouped by file number; returns list of `Offering` objects |
| `latest_offering` | — | `Optional[Offering]` | First entry from `get_offerings()` |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `offering_info_tag` is None or empty | `offering_information = None` |
| `annual_report_disclosure_tag` is None or has no contents | `annual_report_disclosure = None` |
| `funding_portal_cik` absent from XML | `issuer_information.funding_portal = None` |
| `period` element absent from XML | `filer_information.period = None` |
| `parse_date` called with non-MM-DD-YYYY string | Raises `ValueError` |
| `maybe_date` on bad date string | Returns `None` (catches `ValueError`) |
| `get_offering` called when `_filing` is `None` | `Offering(None)` — may raise in `Offering.__init__` |
| No XML from `filing.xml()` | `from_filing` returns `None` |
| `days_to_deadline` when no `deadline_date` | Returns `None` |
| `revenue_growth_yoy` when prior revenue is 0 | Returns `None` |

---

## Access Patterns

- `filing.obj()` → `FormC`
- `FormC.from_filing(filing)` — explicit construction
- `formc.offering_information.price_per_security` — parsed price as float
- `formc.annual_report_disclosure.debt_to_asset_ratio` — check for None first (C-U, C-TR)
- `formc.issuer.get_offerings()` — all offering lifecycle objects for this company
- `formc.get_offering()` — single `Offering` tracking this filing's full lifecycle
- `formc.signature_info.signers` — deduplicated list of signers with titles
- `group_offerings_by_file_number(company.get_filings(form=['C','C/A']))` — group by 020-XXXXX
