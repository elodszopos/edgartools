# Form MA-I — Municipal Advisor Individual

**SEC form codes**: MA-I, MA-I/A
**Python class**: `MunicipalAdvisorForm` (no base class)
**Access**: `filing.obj()` → `MunicipalAdvisorForm`
**Base fields**: See `_base-filing.md`
**Source**: `edgar/muniadvisors.py`

## Complete Field Reference

### From Filing (inherited)
See `_base-filing.md`

### MunicipalAdvisorForm-Specific Fields

#### Properties / Attributes

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing` | `Filing` | no | Underlying Filing object |
| `filer` | `Filer` | no | CIK and CCC from EDGAR header |
| `is_amendment` | `bool` | no | True when form is MA-I/A |
| `is_individual` | `bool` | no | True when form pertains to an individual (vs. organization) |
| `previous_accession_no` | `str` | no | Prior accession number for amendments |
| `contact` | `Contact` | no | Submission contact (name, phone, email) |
| `applicant` | `Applicant` | no | The individual applicant |
| `internet_notification_addresses` | `List[str]` | no | Email addresses for EDGAR notifications |
| `municipal_advisor_offices` | `List[MunicipalAdvisorOffice]` | no | Firms where individual is employed as MA |
| `employment_history` | `EmploymentHistory` | no | Current + prior employers |
| `disclosures` | `Disclosures` | no | All regulatory disclosure responses |
| `signature` | `Signature` | no | Signature block from formData |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing: Filing` | `Optional[MunicipalAdvisorForm]` | Classmethod. Asserts form in `['MA-I','MA-I/A']`. Returns None if no XML. |
| `from_xml` | `xml: str` | `dict` | Classmethod. Returns kwargs dict for constructor; not normally called directly. |
| `to_context` | `detail: str = 'standard'` | `str` | AI context string. `'minimal'`: name + CIK + CRD. `'standard'`: + firms + disclosure flags. `'full'`: + contact info. |

## Nested Objects

### Filer (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `str` | Filer CIK from `<filerId>` |
| `ccc` | `str` | Filer CCC (EDGAR passphrase) from `<filerCcc>` |

### Contact (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Submission contact name |
| `phone` | `str` | Contact phone number |
| `email` | `str` | Contact email (from `<contactEmail>`) |

### Applicant

| Field | Type | Description |
|-------|------|-------------|
| `name` | `Name` | Primary name (first, middle, last, suffix) |
| `other_names` | `List[Name]` | Other names used |
| `crd` | `str` | FINRA CRD number |
| `number_of_advisory_firms` | `int` | Number of MA firms where registered |
| `full_name` | `str` (property) | `name.full_name` convenience accessor |

### Name (`edgar._party.Name`)

| Field | Type | Description |
|-------|------|-------------|
| `first_name` | `str` | First name |
| `middle_name` | `str` | Middle name |
| `last_name` | `str` | Last name |
| `suffix` | `str` | Suffix (Jr., III, etc.) |

### MunicipalAdvisorOffice (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `str` | MA firm CIK |
| `firm_name` | `str` | Full legal name of MA firm |
| `is_independent_relationship` | `bool` | Whether relationship is independent |
| `recent_employment_commenced_date` | `str` | Date employment began |
| `file_number` | `str` | SEC file number for firm |
| `offices` | `List[Office]` | Physical office locations |

### Office (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `start_date` | `str` | Office start date |
| `location_info` | `str` | Location descriptor |
| `address` | `Address` | Physical address |
| `street1` (property) | `str` | `address.street1` or `""` |
| `street2` (property) | `str` | `address.street2` or `""` |
| `city` (property) | `str` | `address.city` or `""` |
| `state_or_country` (property) | `str` | `address.state_or_country` or `""` |
| `zipcode` (property) | `str` | `address.zipcode` or `""` |

### Address (`edgar._party.Address` — Pydantic model)

| Field | Type | Description |
|-------|------|-------------|
| `street1` | `Optional[str]` | Street address line 1 |
| `street2` | `Optional[str]` | Street address line 2 |
| `city` | `Optional[str]` | City |
| `state_or_country` | `Optional[str]` | State or country code |
| `zipcode` | `Optional[str]` | ZIP / postal code |

### EmploymentHistory

| Field | Type | Description |
|-------|------|-------------|
| `current_employer` | `Employer` | Current employment |
| `previous_employers` | `List[Employer]` | Prior employment records |

### Employer (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Employer name |
| `start_date` | `str` | Start date in `'Mon YYYY'` format |
| `end_date` | `Optional[str]` | End date in `'Mon YYYY'` format; None for current employer |
| `ma_related` | `bool` | Whether position was MA-related |
| `investment_related` | `bool` | Whether position was investment-related |
| `position` | `str` | Position description |
| `address` | `Address` | Employer location |

### Disclosures (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `criminal_disclosure` | `CriminalDisclosure` | Criminal action questions |
| `regulatory_disclosure` | `RegulatoryDisclosure` | SEC/CFTC and other regulator questions |
| `civil_disclosure` | `CivilDisclosure` | Civil court questions |
| `complaint_disclosure` | `ComplaintDisclosure` | MA complaint and fraud proceeding questions |
| `termination_disclosure` | `TerminationDisclosure` | Termination/resignation allegation questions |
| `financial_disclosure` | `FinancialDisclosure` | Bankruptcy/bond/lien questions |
| `judgement_lien_disclosure` | `JudgementLienDisclosure` | Judgment lien questions |
| `investigation_disclosure` | `InvestigationDisclosure` | Current investigation questions |
| `any()` | `bool` (method) | True if any disclosure field is affirmative |

### CriminalDisclosure (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `is_convicted_of_felony` | `bool` | Individual convicted of felony |
| `is_charged_with_felony` | `bool` | Individual charged with felony |
| `is_org_convicted_of_felony` | `bool` | Caused organization felony conviction |
| `is_org_charged_with_felony` | `bool` | Caused organization felony charge |
| `is_convicted_of_misdemeanor` | `bool` | Individual convicted of misdemeanor |
| `is_charged_with_misdemeanor` | `bool` | Individual charged with misdemeanor |
| `is_org_convicted_of_misdemeanor` | `bool` | Caused organization misdemeanor conviction |
| `is_org_charged_with_misdemeanor` | `bool` | Caused organization misdemeanor charge |
| `any()` | `bool` (method) | True if any field is True |

### RegulatoryDisclosure (frozen dataclass — 24 fields)

| Field | Type | Description |
|-------|------|-------------|
| `is_made_false_statement` | `bool` | SEC/CFTC found individual made false statement |
| `is_violated_regulation` | `bool` | Found in violation of SEC or CFTC regulation |
| `is_cause_of_denial` | `bool` | Caused suspension of MA business |
| `is_order_against` | `bool` | Order entered against individual |
| `is_imposed_penalty` | `bool` | Penalty imposed |
| `is_un_ethical` | `bool` | Found dishonest or unethical |
| `is_found_in_violation_of_regulation` | `bool` | Found to have willfully violated Securities or Investment Act |
| `is_found_in_cause_of_denial` | `bool` | Cause of denial of authorization |
| `is_order_against_activity` | `bool` | Order against individual's activities |
| `is_denied_license` | `bool` | License denied, suspended, or revoked |
| `is_found_made_false_statement` | `bool` | Found to have made false statement |
| `is_found_in_violation_of_rules` | `bool` | Found in violation of rules |
| `is_found_in_cause_of_suspension` | `bool` | Cause of suspension |
| `is_discipliend` | `bool` | Expelled or barred from membership (sic — matches XML spelling) |
| `is_authorized_to_act_attorney` | `bool` | Attorney authorization ever suspended |
| `is_regulatory_complaint` | `bool` | Notified of regulatory complaint |
| `is_violated_security_act` | `bool` | Violated Securities Act |
| `is_will_fully_aided` | `bool` | Willfully aided a violation |
| `is_failed_to_supervise` | `bool` | Failed to supervise another individual |
| `is_found_will_fully_aided` | `bool` | Other regulator found willful aiding |
| `is_association_bared` | `bool` | Barred from association with regulated agency |
| `is_final_order` | `bool` | Final order entered |
| `is_will_fully_violated_security_act` | `bool` | Willfully violated Securities Act |
| `is_failed_resonably` | `bool` | Failed to act reasonably (sic — matches XML spelling) |
| `any()` | `bool` (method) | True if any field is True |

### CivilDisclosure (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `is_enjoined` | `bool` | Enjoined in connection with MA business |
| `is_found_violation_of_regulation` | `bool` | Court found violation of law or regulation |
| `is_dismissed` | `bool` | Civil action dismissed with settlement |
| `is_named_in_civil_proceeding` | `bool` | Named in current civil proceeding |
| `any()` | `bool` (method) | True if any field is True |

### ComplaintDisclosure (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `is_complaint_pending` | `bool` | MA-related complaint still pending |
| `is_complaint_settled` | `bool` | MA-related complaint settled |
| `is_fraud_case_pending` | `bool` | MA-related fraud proceeding pending |
| `is_fraud_case_resulting_award` | `bool` | Fraud proceeding resulted in award |
| `is_fraud_case_settled` | `bool` | Fraud proceeding settled |
| `any()` | `bool` (method) | True if any field is True |

### TerminationDisclosure (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `is_violated_industry_standards` | `bool` | Terminated after violation allegations |
| `is_involved_in_fraud` | `bool` | Terminated after fraud allegations |
| `is_failed_to_supervise` | `bool` | Terminated after failure to supervise |
| `any()` | `bool` (method) | True if any field is True |

### FinancialDisclosure (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `is_compromised` | `bool` | Made compromise with creditors |
| `is_bankruptcy_petition` | `bool` | Controlled organization filed for bankruptcy |
| `is_trustee_appointed` | `bool` | Trustee appointed for controlled organization |
| `is_bond_revoked` | `bool` | Bonding company denied/paid/revoked bond |
| `any()` | `bool` (method) | True if any field is True |

### JudgementLienDisclosure (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `is_lien_against` | `bool` | Judgment lien currently against individual |
| `any()` | `bool` (method) | Returns `self.is_lien_against` |

### InvestigationDisclosure (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `is_investigated` | `bool` | Individual currently under investigation |

Note: `InvestigationDisclosure` does NOT have an `.any()` method — only `is_investigated: bool`. Other disclosure classes have `.any()` but not this one.

### Signature (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `date_signed` | `str` | Date signature was applied |
| `signature` | `str` | Signature text |
| `title` | `str` | Signer's title |

## Gotchas

- **`to_context` standard detail disclosure flags are broken in source** — the loop uses short attribute names (`'criminal'`, `'regulatory'`, etc.) via `getattr(self.disclosures, disc_type, None)`, but actual attribute names are `criminal_disclosure`, `regulatory_disclosure`, etc. All `getattr` calls silently return `None`, so disclosure flags never appear in `to_context` standard output even when disclosures are affirmative.

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.form` not in `['MA-I','MA-I/A']` | `from_filing` raises `AssertionError` |
| `filing.xml()` returns None | `from_filing` returns None |
| Missing XML elements | `child_text`/`child_value` return empty string or None; fields default to empty |

## Access Patterns

- `filing.obj()` → `MunicipalAdvisorForm`
- `MunicipalAdvisorForm.from_filing(filing)` — returns None if no XML
- `form.disclosures.any()` — quick flag for any regulatory issue
- `form.disclosures.criminal_disclosure.any()` — category-specific check
- `form.applicant.full_name` — formatted name string
- `form.municipal_advisor_offices[0].offices[0].city` — first office location
