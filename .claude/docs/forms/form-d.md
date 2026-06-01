# Form D — Private Placement

**SEC form codes**: `D`, `D/A`
**Python class**: `FormD`
**Access**: `filing.obj()` → `FormD`
**Base fields**: See `_base-filing.md`
**Source**: `edgar/offerings/formd.py`

---

## Complete Field Reference

### From Filing (inherited)
See `_base-filing.md`

### FormD-Specific Fields

#### Instance Attributes (set in `__init__`)

| Field | Type | Description |
|-------|------|-------------|
| `submission_type` | `str` | `'D'` or `'D/A'` from `<submissionType>` element |
| `is_live` | `bool` | True if `testOrLive == 'LIVE'` |
| `primary_issuer` | `Issuer` | Main issuer from `<primaryIssuer>` (from `edgar._party`) |
| `related_persons` | `List[Person]` | Executives and directors from `<relatedPersonsList>` |
| `offering_data` | `OfferingData` | Complete offering details |
| `signature_block` | `SignatureBlock` | Signature block with `authorized_representative` flag |

#### Properties — Immediate

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `is_new` | `bool` | no | Delegates to `offering_data.is_new` |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_xml` | `offering_xml: str` | `FormD` | Only entry point; no `from_filing`; dispatch in `edgar/__init__.py` calls `filing.xml()` then `FormD.from_xml(xml)` |
| `to_context` | `detail: str = 'standard'` | `str` | AI-optimized text; detail: `'minimal'`/`'standard'`/`'full'` |

---

## Nested Objects

### `Issuer` (from `edgar._party`) — `primary_issuer`

| Field | Type | Description |
|-------|------|-------------|
| `entity_name` | `str` | Legal entity name |
| `cik` | `str` | CIK number |
| `entity_type` | `str` | Legal entity type (e.g. "Limited Partnership") |
| `jurisdiction` | `str` | State/country of organization |
| `year_of_incorporation` | `str` | Year incorporated |

### `Person` (from `edgar._party`) — items in `related_persons`

| Field | Type | Description |
|-------|------|-------------|
| `first_name` | `str` | First name |
| `last_name` | `str` | Last name |
| `address` | `Address` | Business address |

### `OfferingData` (plain class)

| Field | Type | Description |
|-------|------|-------------|
| `industry_group` | `IndustryGroup` | Industry classification |
| `revenue_range` | `str` | `revenueRange` (e.g. "1000000-5000000") |
| `federal_exemptions` | `List[str]` | Exemption items (e.g. `["Rule 506(b)"]`) |
| `is_new` | `bool` | True if `<isAmendment>` is `'true'`; confusingly named — see Error Paths |
| `date_of_first_sale` | `str` | `dateOfFirstSale` raw string |
| `more_than_one_year` | `bool` | `moreThanOneYear == 'true'` |
| `is_equity` | `bool` | `isEquityType == 'true'` |
| `is_pooled_investment` | `bool` | `isPooledInvestmentFundType == 'true'` |
| `business_combination_transaction` | `BusinessCombinationTransaction` | Business combination flag |
| `minimum_investment` | `str` | `minimumInvestmentAccepted` raw string |
| `sales_compensation_recipients` | `List[SalesCompensationRecipient]` | Broker-dealer recipients; empty list if none |
| `offering_sales_amounts` | `Optional[OfferingSalesAmounts]` | Dollar amounts; `None` if element absent |
| `investors` | `Optional[Investors]` | Investor count details; `None` if element absent |
| `sales_commission_finders_fees` | `Optional[SalesCommissionFindersFees]` | Commission details; `None` if element absent |
| `use_of_proceeds` | `Optional[UseOfProceeds]` | Proceeds usage; always extracted (raises if `useOfProceeds` tag missing) |

**`OfferingData.from_xml(el: Tag)` classmethod** — factory method consuming BeautifulSoup tag.

### `IndustryGroup` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `industry_group_type` | `str` | e.g. "Technology", "Pooled Investment Fund" |
| `investment_fund_info` | `Optional[InvestmentFundInfo]` | Present only for pooled investment fund types |

### `InvestmentFundInfo` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `investment_fund_type` | `str` | Fund type (e.g. "Hedge Fund", "Private Equity Fund") |
| `is_40_act` | `bool` | Whether fund is registered under Investment Company Act of 1940 |

### `OfferingSalesAmounts` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `total_offering_amount` | `object` | Raw string from XML (not typed as float) |
| `total_amount_sold` | `object` | Raw string from XML |
| `total_remaining` | `object` | Raw string from XML |
| `clarification_of_response` | `Optional[str]` | Free-text clarification |

**Note**: All amount fields are typed `object` — they remain as raw strings from XML. Use `float()` to convert.

### `Investors` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `has_non_accredited_investors` | `bool` | `hasNonAccreditedInvestors == 'true'` |
| `total_already_invested` | `object` | Raw string count of investors |

### `SalesCommissionFindersFees` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `sales_commission` | `object` | Raw string dollar amount |
| `finders_fees` | `object` | Raw string dollar amount |
| `clarification_of_response` | `Optional[str]` | Free-text clarification |

### `UseOfProceeds` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `gross_proceeds_used` | `object` | Raw string dollar amount from `grossProceedsUsed/dollarAmount` |
| `clarification_of_response` | `Optional[str]` | Free-text clarification |

### `BusinessCombinationTransaction` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `is_business_combination` | `bool` | `isBusinessCombinationTransaction == 'true'` |
| `clarification_of_response` | `Optional[str]` | Free-text clarification |

### `SalesCompensationRecipient` (plain class)
Items in `offering_data.sales_compensation_recipients`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Recipient name; literal "None" strings stripped |
| `crd` | `str` | FINRA CRD number; literal "None" strings stripped |
| `associated_bd_name` | `str` | Associated broker-dealer name (note: field has a typo in `__init__` — stored as annotation, not assignment) |
| `associated_bd_crd` | `str` | Associated BD CRD number |
| `address` | `Address` | Recipient address; `None` if no `<recipientAddress>` element |
| `states_of_solicitation` | `List[str]` | State codes + any `<value>` entries (e.g. "All States") |

**`SalesCompensationRecipient.from_xml(recipient_tag: Tag)` classmethod** — cleans literal "None" strings via `re.sub`.

### `SignatureBlock` (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `authorized_representative` | `bool` | `authorizedRepresentative == 'true'` |
| `signatures` | `List[Signature]` | All signatures |

### `Signature` (Pydantic) — items in `signature_block.signatures`

| Field | Type | Description |
|-------|------|-------------|
| `issuer_name` | `str` | Issuer entity name; defaults to `""` if absent |
| `signature_name` | `str` | Signature text; defaults to `""` |
| `name_of_signer` | `str` | Printed name of signer; defaults to `""` |
| `title` | `Optional[str]` | Signer's title |
| `date` | `Optional[str]` | Signature date raw string |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `from_xml` called with no `primaryIssuer` element | `Issuer.from_xml(None)` — behavior depends on `edgar._party.Issuer` |
| `useOfProceeds` tag absent from XML | `use_of_proceeds = UseOfProceeds(...)` raises `AttributeError` (tag required) |
| `offering_sales_amount_tag` absent | `offering_sales_amounts = None` |
| `investors_tag` absent | `investors = None` |
| `sales_commission_finders_tag` absent | `sales_commission_finders_fees = None` |
| `bus_combination_el` absent | `business_combination_transaction = None` |
| `SalesCompensationRecipient.address` when no `<recipientAddress>` | `address = None` |
| All amount fields | Remain as raw `object` strings; explicit `float()` conversion may raise `ValueError` |
| `is_new` field | Confusing: set to `True` when `<isAmendment>` is `'true'` — use `submission_type` for amendment detection |

---

## Access Patterns

- `filing.obj()` → `FormD` (dispatch calls `filing.xml()` then `FormD.from_xml(xml)`)
- `formd.primary_issuer.entity_name` — company name
- `formd.offering_data.offering_sales_amounts.total_offering_amount` — check for `None` first
- `formd.offering_data.investors.has_non_accredited_investors` — accredited-only check
- `formd.offering_data.federal_exemptions` — list of applicable exemptions
- `formd.related_persons` — list of directors/officers
- `formd.offering_data.sales_compensation_recipients` — broker-dealer list
- `float(formd.offering_data.offering_sales_amounts.total_offering_amount)` — convert amount string
