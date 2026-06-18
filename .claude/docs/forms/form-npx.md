# Form N-PX — Fund Proxy Voting Record

**SEC form codes**: `N-PX`, `N-PX/A`
**Python class**: `NPX`
**Access**: `filing.obj()` → `NPX`
**Base fields**: See `_base-filing.md`
**Source**: `edgar/npx/npx.py`, `edgar/npx/models.py`

---

## Complete Field Reference

### From Filing (inherited)
See `_base-filing.md`

### NPX-Specific Fields

#### Instance Attributes (set in `__init__`)

| Field | Type | Description |
|-------|------|-------------|
| `_primary_doc` | `PrimaryDoc` | Parsed primary document XML data |
| `_proxy_votes` | `Optional[ProxyVotes]` | Proxy vote container; `None` if no proxy vote table XML found |
| `_filing` | `Optional[Filing]` | Source filing reference |

#### Properties — Immediate (delegates to `_primary_doc`)

| Property | Type | Lazy | Description |
|----------|------|------|-------------|
| `fund_name` | `Optional[str]` | no | Name of the reporting fund |
| `cik` | `str` | no | CIK of the filer |
| `period_of_report` | `str` | no | Reporting period end date |
| `report_calendar_year` | `Optional[str]` | no | Calendar year of the report |
| `submission_type` | `str` | no | `'N-PX'` or `'N-PX/A'` |
| `is_amendment` | `bool` | no | True if amendment; `False` if `_primary_doc.is_amendment` is `None` |
| `signer_name` | `str` | no | Name of filing signatory |
| `signer_title` | `str` | no | Title of filing signatory |
| `signature_date` | `str` | no | Date filing was signed |
| `address` | `str` | no | Formatted street address of reporting person (multi-line) |
| `agent_for_service_name` | `Optional[str]` | no | Agent for service of process name |
| `agent_for_service_address` | `Optional[str]` | no | Formatted agent address (multi-line); `None` if no street1 |
| `agent_for_service_address_street1` | `Optional[str]` | no | Agent street 1 |
| `agent_for_service_address_street2` | `Optional[str]` | no | Agent street 2 |
| `agent_for_service_address_city` | `Optional[str]` | no | Agent city |
| `agent_for_service_address_state_country` | `Optional[str]` | no | Agent state/country |
| `agent_for_service_address_zip_code` | `Optional[str]` | no | Agent ZIP |
| `phone_number` | `Optional[str]` | no | Phone number of reporting person |
| `crd_number` | `Optional[str]` | no | FINRA CRD number |
| `filer_sec_file_number` | `Optional[str]` | no | SEC file number of the filer |
| `lei_number` | `Optional[str]` | no | Legal Entity Identifier |
| `report_type` | `Optional[str]` | no | e.g. "FUND VOTING REPORT", "MANAGER VOTING REPORT" |
| `confidential_treatment` | `Optional[str]` | no | Confidential treatment flag (Y/N) |
| `notice_explanation` | `Optional[str]` | no | Notice explanation text |
| `npx_file_number` | `Optional[str]` | no | N-PX file number |
| `explanatory_choice` | `Optional[str]` | no | Explanatory choice flag |
| `other_included_managers_count` | `Optional[str]` | no | Count of other included managers |
| `tx_printed_signature` | `Optional[str]` | no | Printed signature text |
| `amendment_no` | `Optional[str]` | no | Amendment number if amendment filing |
| `amendment_type` | `Optional[str]` | no | Type of amendment |
| `de_novo_request_choice` | `Optional[str]` | no | De novo request choice |
| `year_or_quarter` | `Optional[str]` | no | `'YEAR'` or `'QUARTER'` indicator |
| `conf_denied_expired` | `Optional[str]` | no | Confidential treatment denied/expired flag |
| `registrant_type` | `Optional[str]` | no | Registrant type (e.g. "RMIC", "IA") |
| `live_test_flag` | `Optional[str]` | no | `'LIVE'` or `'TEST'` |
| `contact_name` | `Optional[str]` | no | Contact person name |
| `contact_phone_number` | `Optional[str]` | no | Contact phone |
| `contact_email_address` | `Optional[str]` | no | Contact email |
| `investment_company_type` | `Optional[str]` | no | e.g. "N-1A", "N-2" |
| `series_count` | `Optional[str]` | no | Number of series in filing |
| `included_managers` | `List[IncludedManager]` | no | Other investment managers in this filing |
| `report_series_class_infos` | `List[ReportSeriesClassInfo]` | no | Series/class reporting information |
| `series_reports` | `List[SeriesReport]` | no | Series report details |
| `proxy_votes` | `Optional[ProxyVotes]` | no | Proxy voting records; `None` if no proxy vote XML found |
| `primary_doc` | `PrimaryDoc` | no | Raw primary document data |
| `filing` | `Optional[Filing]` | no | Source `Filing` object |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing: Filing` | `Optional[NPX]` | Classmethod factory; parses primary XML and proxy vote table; returns `None` on parse failure |
| `to_dataframe` | — | `pd.DataFrame` | One-row metadata DataFrame (fund-level, not vote-level); see schema below |
| `to_context` | `detail: str = 'standard'` | `str` | AI-optimized text; detail: `'minimal'`/`'standard'`/`'full'` |

---

## Nested Objects

### `ProxyVotes` (dataclass)
Container for all `ProxyTable` objects in one N-PX filing.

| Attribute | Type | Description |
|-----------|------|-------------|
| `proxy_tables` | `List[ProxyTable]` | All proxy vote table entries |

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `to_dataframe` | — | `pd.DataFrame` | One row per VoteRecord; see DataFrame schema below |
| `filter_by_issuer` | `issuer_name: str` | `ProxyVotes` | Case-insensitive partial match on `issuer_name` |
| `filter_by_vote` | `how_voted: str` | `ProxyVotes` | Exact match on `how_voted.upper()` (e.g. `'AGAINST'`, `'FOR'`, `'ABSTAIN'`, `'WITHHOLD'`) |
| `filter_by_category` | `category: str` | `ProxyVotes` | Case-insensitive partial match against `VoteCategory.category_type` |
| `against_management` | — | `ProxyVotes` | Tables where any vote differs from `management_recommendation` |
| `management_alignment_rate` | — | `float` | 0.0–1.0; `1.0` (vacuously true) when no votes have management recommendations |
| `summary_by_category` | — | `pd.DataFrame` | Vote counts per category; see DataFrame schema below |
| `summary` | — | `pd.DataFrame` | Vote counts by `how_voted` type; two columns: `vote_type`, `count` |
| `__len__` | — | `int` | Number of `proxy_tables` |
| `__iter__` | — | `Iterator[ProxyTable]` | Iterate proxy tables |
| `__getitem__` | `int` | `ProxyTable` | Access by index |

### `ProxyTable` (dataclass)
One entry per `<proxyVoteTable>` element in the XML.

| Field | Type | Description |
|-------|------|-------------|
| `issuer_name` | `str` | Company that held the shareholder meeting |
| `meeting_date` | `str` | Date of shareholder meeting (raw string) |
| `vote_description` | `str` | Description of the vote matter |
| `shares_voted` | `float` | Total shares voted on this matter |
| `shares_on_loan` | `float` | Shares on loan at time of vote |
| `cusip` | `Optional[str]` | CUSIP security identifier |
| `isin` | `Optional[str]` | ISIN security identifier |
| `figi` | `Optional[str]` | FIGI security identifier |
| `other_vote_description` | `Optional[str]` | Additional vote description details |
| `vote_source` | `Optional[str]` | Source of the vote |
| `vote_series` | `Optional[str]` | Series information for the vote |
| `vote_other_info` | `Optional[str]` | Additional vote information |
| `vote_categories` | `List[VoteCategory]` | Categories; default empty list |
| `vote_records` | `List[VoteRecord]` | Individual voting records; default empty list |
| `other_managers` | `List[str]` | Other managers involved; default empty list |

### `VoteRecord` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `how_voted` | `str` | How the fund voted (e.g. `'FOR'`, `'AGAINST'`, `'ABSTAIN'`, `'WITHHOLD'`) |
| `shares_voted` | `float` | Shares voted in this record |
| `management_recommendation` | `str` | Management's recommendation; `'NONE'` when no recommendation |

### `VoteCategory` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `category_type` | `str` | Category name; common values: `DIRECTOR ELECTIONS`, `SECTION 14A SAY-ON-PAY VOTES`, `AUDIT-RELATED`, `COMPENSATION`, `ENVIRONMENT OR CLIMATE`, `CORPORATE GOVERNANCE`, `OTHER` |

### `PrimaryDoc` (dataclass)
Raw primary document extracted from `primary_doc.xml`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cik` | `str` | yes | Filer CIK |
| `fund_name` | `Optional[str]` | yes | Fund name |
| `street1` | `str` | yes | Address street 1 |
| `city` | `str` | yes | Address city |
| `state` | `str` | yes | Address state |
| `zip_code` | `str` | yes | Address ZIP |
| `period_of_report` | `str` | yes | Reporting period end date |
| `submission_type` | `str` | yes | Form type |
| `report_calendar_year` | `Optional[str]` | yes | Calendar year |
| `signer_name` | `str` | yes | Signatory name |
| `signer_title` | `str` | yes | Signatory title |
| `signature_date` | `str` | yes | Signature date |
| `phone_number` | `Optional[str]` | no | Phone number |
| `street2` | `Optional[str]` | no | Address street 2 |
| `crd_number` | `Optional[str]` | no | CRD number |
| `filer_sec_file_number` | `Optional[str]` | no | SEC file number |
| `lei_number` | `Optional[str]` | no | LEI |
| `report_type` | `Optional[str]` | no | Report type |
| `notice_explanation` | `Optional[str]` | no | Notice explanation |
| `confidential_treatment` | `Optional[str]` | no | Confidential treatment flag |
| `npx_file_number` | `Optional[str]` | no | N-PX file number |
| `explanatory_choice` | `Optional[str]` | no | Explanatory choice |
| `other_included_managers_count` | `Optional[str]` | no | Other manager count |
| `tx_printed_signature` | `Optional[str]` | no | Printed signature |
| `agent_for_service_name` | `Optional[str]` | no | Agent name |
| `agent_for_service_address_street1` | `Optional[str]` | no | Agent street 1 |
| `agent_for_service_address_street2` | `Optional[str]` | no | Agent street 2 |
| `agent_for_service_address_city` | `Optional[str]` | no | Agent city |
| `agent_for_service_address_state_country` | `Optional[str]` | no | Agent state/country |
| `agent_for_service_address_zip_code` | `Optional[str]` | no | Agent ZIP |
| `is_amendment` | `Optional[bool]` | no | Amendment flag |
| `amendment_no` | `Optional[str]` | no | Amendment number |
| `amendment_type` | `Optional[str]` | no | Amendment type |
| `de_novo_request_choice` | `Optional[str]` | no | De novo choice |
| `year_or_quarter` | `Optional[str]` | no | YEAR or QUARTER |
| `conf_denied_expired` | `Optional[str]` | no | Conf. treatment denied/expired |
| `included_managers` | `List[IncludedManager]` | no | Other managers |
| `registrant_type` | `Optional[str]` | no | Registrant type |
| `live_test_flag` | `Optional[str]` | no | LIVE or TEST |
| `ccc` | `Optional[str]` | no | CIK confirmation code |
| `contact_name` | `Optional[str]` | no | Contact name |
| `contact_phone_number` | `Optional[str]` | no | Contact phone |
| `contact_email_address` | `Optional[str]` | no | Contact email |
| `override_internet_flag` | `Optional[str]` | no | Override internet flag |
| `confirming_copy_flag` | `Optional[str]` | no | Confirming copy flag |
| `investment_company_type` | `Optional[str]` | no | Investment company type |
| `rpt_include_all_series_flag` | `Optional[str]` | no | Include all series flag |
| `series_count` | `Optional[str]` | no | Series count |
| `report_series_class_infos` | `List[ReportSeriesClassInfo]` | no | Series/class info |
| `series_reports` | `List[SeriesReport]` | no | Series reports |

### `IncludedManager` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `serial_no` | `str` | Manager serial number |
| `form13f_file_number` | `Optional[str]` | 13F file number |
| `name` | `str` | Manager name |
| `sec_file_number` | `Optional[str]` | SEC file number |

### `ReportSeriesClassInfo` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `series_id` | `str` | Series identifier |
| `class_infos` | `List[ClassInfo]` | Class information for this series |

### `ClassInfo` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `class_id` | `str` | Class identifier |

### `SeriesReport` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `id_of_series` | `str` | Series ID |
| `name_of_series` | `Optional[str]` | Series name |
| `lei_of_series` | `Optional[str]` | Series LEI |

---

## DataFrame Schemas

### `proxy_votes.to_dataframe()` columns
One row per `VoteRecord` (one proxy table may have multiple vote records).

| Column | Type | Description |
|--------|------|-------------|
| `issuer_name` | `str` | Company that held meeting |
| `meeting_date` | `str` | Meeting date |
| `vote_description` | `str` | Matter description |
| `total_shares_voted` | `float` | `ProxyTable.shares_voted` |
| `shares_on_loan` | `float` | `ProxyTable.shares_on_loan` |
| `cusip` | `Optional[str]` | CUSIP identifier |
| `isin` | `Optional[str]` | ISIN identifier |
| `figi` | `Optional[str]` | FIGI identifier |
| `other_vote_description` | `Optional[str]` | Additional description |
| `vote_source` | `Optional[str]` | Vote source |
| `vote_series` | `Optional[str]` | Series information |
| `vote_other_info` | `Optional[str]` | Other info |
| `vote_categories` | `Optional[str]` | Comma-separated category types |
| `other_managers` | `Optional[str]` | Comma-separated manager names |
| `how_voted` | `Optional[str]` | `VoteRecord.how_voted`; `None` if no vote records |
| `shares_voted` | `Optional[float]` | `VoteRecord.shares_voted`; `None` if no vote records |
| `management_recommendation` | `Optional[str]` | `VoteRecord.management_recommendation`; `None` if no vote records |

### `npx.to_dataframe()` columns
One row — fund-level metadata only (not vote-level).

| Column | Type |
|--------|------|
| `cik` | `str` |
| `fund_name` | `Optional[str]` |
| `period_of_report` | `str` |
| `report_calendar_year` | `Optional[str]` |
| `submission_type` | `str` |
| `is_amendment` | `bool` |
| `report_type` | `Optional[str]` |
| `npx_file_number` | `Optional[str]` |
| `lei_number` | `Optional[str]` |
| `crd_number` | `Optional[str]` |
| `investment_company_type` | `Optional[str]` |
| `year_or_quarter` | `Optional[str]` |
| `signer_name` | `str` |
| `signer_title` | `str` |
| `signature_date` | `str` |
| `address` | `str` |
| `phone_number` | `Optional[str]` |
| `agent_for_service_name` | `Optional[str]` |
| `agent_for_service_address` | `Optional[str]` |
| `contact_name` | `Optional[str]` |
| `contact_phone_number` | `Optional[str]` |
| `contact_email_address` | `Optional[str]` |
| `confidential_treatment` | `Optional[str]` |
| `other_included_managers_count` | `Optional[str]` |
| `series_count` | `Optional[str]` |
| `proxy_vote_count` | `int` |

### `proxy_votes.summary_by_category()` columns

| Column | Type | Description |
|--------|------|-------------|
| `category` | `str` | Category type name |
| `total_votes` | `int` | Total vote records in category |
| `for_votes` | `int` | Count of FOR votes |
| `against_votes` | `int` | Count of AGAINST votes |
| `abstain_votes` | `int` | Count of ABSTAIN votes |
| `other_votes` | `int` | Count of WITHHOLD and other types |
| `with_management` | `int` | Votes matching management recommendation |
| `against_management` | `int` | Votes differing from management recommendation |

### `proxy_votes.summary()` columns

| Column | Type | Description |
|--------|------|-------------|
| `vote_type` | `str` | `how_voted.upper()` value |
| `count` | `int` | Number of vote records with this vote type |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `filing.xml()` returns `None` | `from_filing` returns `None` with log warning |
| Primary XML parse fails | `from_filing` returns `None` with log error |
| No proxy vote XML in attachments | `proxy_votes` is `None` (not empty `ProxyVotes`) |
| Attachment named `'primary'` in documents | Skipped during proxy vote search |
| `proxyVoteTable` not in XML content | Attachment skipped |
| `management_alignment_rate()` with no votes having recommendations | Returns `1.0` (vacuous truth) |
| `ProxyTable` with empty `vote_records` | `to_dataframe()` includes one row with `None` for vote fields |
| `proxy_votes.filter_by_category` case mismatch | Case-insensitive partial match — partial strings work (e.g. `"CLIMATE"` matches `"ENVIRONMENT OR CLIMATE"`) |

---

## Access Patterns

- `filing.obj()` → `NPX`
- `NPX.from_filing(filing)` — explicit construction
- `npx.proxy_votes.to_dataframe()` — full vote record DataFrame
- `npx.proxy_votes.filter_by_issuer("Apple")` — filter to one company
- `npx.proxy_votes.against_management()` — votes that differed from management
- `npx.proxy_votes.filter_by_category("ENVIRONMENT")` — ESG/climate votes
- `npx.proxy_votes.filter_by_vote("AGAINST")` — all against votes
- `npx.proxy_votes.management_alignment_rate()` — overall alignment score
- `npx.proxy_votes.summary_by_category()` — category breakdown DataFrame
- `npx.proxy_votes.summary()` — vote type counts
- `npx.to_dataframe()` — fund metadata (not votes); use `proxy_votes.to_dataframe()` for votes
