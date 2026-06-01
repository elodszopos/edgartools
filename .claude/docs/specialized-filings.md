## Specialized Filings

### Overview

This domain covers the remaining typed form objects in EdgarTools that do not belong to the financial-statement or fund-holdings families. It spans eight distinct subdomain modules: proxy statements (DEF 14A family), municipal advisor individual registrations (MA-I), SEC correspondence threads (CORRESP/UPLOAD), fund proxy-voting records (N-PX), asset-backed securities distribution reports (10-D, ABS-EE), alternative trading system disclosures (ATS-N), business-development-company analytics (BDC datasets/investments/nonaccrual), and the generic XML fallback for ~11 more form types. All objects are returned by `filing.obj()` via the central dispatch in `edgar/__init__.py:195`.

---

### Public API surface

| Symbol | file:line | Purpose |
|---|---|---|
| `ProxyStatement` | `edgar/proxy/core.py:35` | DEF 14A data object; exec comp + PvP via XBRL; HTML extraction for SCT/ownership/audit |
| `ProxySeason` | `edgar/proxy/season.py:45` | All proxy filings for one company annual-meeting cycle |
| `ProxyContest` | `edgar/proxy/contest.py:147` | Contested proxy analysis; management vs dissident timeline |
| `ProxyContests` | `edgar/proxy/contests.py:33` | Market-wide contest collection |
| `proxy_contests()` | `edgar/proxy/contests.py:166` | Top-level function to scan EDGAR for contest-indicator forms |
| `PROXY_FORMS` | `edgar/proxy/models.py:27` | List of 30+ form codes routing to ProxyStatement |
| `classify_proxy_tier()` | `edgar/proxy/models.py:83` | Returns int 1-5 tier for a proxy form code |
| `MunicipalAdvisorForm` | `edgar/muniadvisors.py:287` | MA-I/MA-I/A XML data object; applicant + employment + disclosures |
| `Correspondence` | `edgar/correspondence.py:194` | CORRESP/UPLOAD single-letter data object |
| `CorrespondenceThread` | `edgar/correspondence.py:422` | Reconstructed thread for a file number |
| `CorrespondenceType` | `edgar/correspondence.py:41` | Enum: company_response / sec_comment / review_complete / etc. |
| `CORRESPONDENCE_FORMS` | `edgar/correspondence.py:34` | `['CORRESP', 'UPLOAD']` |
| `NPX` | `edgar/npx/npx.py:372` | N-PX/N-PX/A fund proxy-voting record |
| `ProxyVotes` | `edgar/npx/npx.py:44` | Container of `ProxyTable` entries with filter/analysis methods |
| `TenD` | `edgar/abs/ten_d.py:84` | 10-D ABS distribution report; CMBS loan/property data |
| `ABSType` | `edgar/abs/ten_d.py:50` | Enum: CMBS/AUTO/CREDIT_CARD/RMBS/STUDENT_LOAN/UTILITY/OTHER |
| `CMBSAssetData` | `edgar/abs/cmbs.py:137` | CMBS EX-102 XML parser; `.loans` / `.properties` DataFrames |
| `AutoLeaseAssetData` | `edgar/abs/abs_ee.py:70` | ABS-EE EX-102 auto-lease XML parser; `.assets` DataFrame |
| `DistributionReport` | `edgar/abs/distribution.py:~30` | HTML distribution metric extractor (partial accuracy ~42%) |
| `AlternativeTradingSystem` | `edgar/ats/atsn.py:107` | ATS-N/MA/UA/CA parsed data object |
| `AlternativeTradingSystemWithdrawal` | `edgar/ats/atsn.py` | ATS-N-W withdrawal data object |
| `from_atsn_filing()` | `edgar/ats/atsn.py:36` | Module-level factory |
| `BDCDataset` | `edgar/bdc/datasets.py:447` | Quarterly DERA bulk extract (sub/num/pre/soi TSVs) |
| `ScheduleOfInvestmentsData` | `edgar/bdc/datasets.py:136` | SOI wrapper with CIK-subsetting and cross-BDC search |
| `fetch_bdc_dataset()` | `edgar/bdc/datasets.py:723` | Download and parse a quarterly BDC ZIP from DERA |
| `BDCEntity` | `edgar/bdc/reference.py:41` | A single BDC from the SEC BDC Report |
| `BDCEntities` | `edgar/bdc/reference.py` | Collection of BDCEntity; `.get_by_ticker()` etc. |
| `get_bdc_list()` | `edgar/bdc/reference.py:~120` | Fetch SEC BDC Report → BDCEntities |
| `is_bdc_cik()` | `edgar/bdc/reference.py` | Boolean check for a CIK |
| `find_bdc()` | `edgar/bdc/search.py` | Fuzzy search by name or ticker |
| `extract_nonaccrual()` | `edgar/bdc/nonaccrual.py` | Extract non-accrual investments from a BDC 10-K XBRL |
| `XmlFiling` | `edgar/xmlfiling.py:140` | Generic XML/XSLT fallback for X-17A-5, TA-1/2/W, MA, CFPORTAL, SBSE-*, ATS-N-C |
| `XML_FILING_FORMS` | `edgar/xmlfiling.py:55` | List built from `_XSLT_PREFIXES` + `/A` variants |

---

### Key classes

#### ProxyStatement (`edgar/proxy/core.py:35`)
Primary interface for DEF 14A data. Dual extraction path: XBRL for structured PvP/exec-comp data, lxml HTML parsing for SCT/ownership/director-comp/audit-fees/voting-proposals.

- `from_filing(filing) -> Optional[ProxyStatement]` — factory — `core.py:69`
- `has_xbrl -> bool` — whether ECD XBRL data present (cached) — `core.py:79`
- `peo_name -> Optional[str]` — reads `ecd:PeoName` concept — `core.py:215`
- `peo_total_comp -> Optional[Decimal]` — latest `ecd:PeoTotalCompAmt` (cached) — `core.py:219`
- `peo_actually_paid_comp -> Optional[Decimal]` — `ecd:PeoActuallyPaidCompAmt` (cached) — `core.py:228`
- `neo_avg_total_comp -> Optional[Decimal]` — `ecd:NonPeoNeoAvgTotalCompAmt` (cached) — `core.py:237`
- `executive_compensation -> pd.DataFrame` — 5-year multi-column PvP DataFrame (cached) — `core.py:610`
- `pay_vs_performance -> pd.DataFrame` — TSR/peer TSR/net income vs CAP (cached) — `core.py:657`
- `named_executives -> List[NamedExecutive]` — only when dimensional XBRL available (~60% of filers) — `core.py:725`
- `has_individual_executive_data -> bool` — checks `dim_ecd_IndividualAxis` in facts — `core.py:716`
- `voting_proposals -> List[VotingProposal]` — HTML regex extraction (cached) — `core.py:467`
- `ceo_pay_ratio -> Optional[CEOPayRatio]` — regex from filing text (cached) — `core.py:486`
- `summary_compensation_table -> pd.DataFrame` — lxml table extraction (cached) — `core.py:505`
- `beneficial_ownership -> pd.DataFrame` — lxml extraction (cached) — `core.py:536`
- `director_compensation_table -> pd.DataFrame` — lxml extraction (cached) — `core.py:564`
- `audit_fees -> Optional[AuditFees]` — lxml extraction (cached) — `core.py:594`
- `awards_close_to_mnpi -> pd.DataFrame` — SEC Rule 402(x) awards near MNPI (cached) — `core.py:338`
- `season -> Optional[ProxySeason]` — lazily fetches current ProxySeason (cached) — `core.py:162`
- `to_context(detail) -> str` — AI context string; detail='minimal'/'standard'/'full' — `core.py:757`

#### ProxySeason (`edgar/proxy/season.py:45`)
Groups proxy filings around one annual meeting. Anchored by management DEF 14A (or DEFC14A in contest years).

- `for_company(company, index=0) -> Optional[ProxySeason]` — classmethod; index=0 is latest — `season.py:80`
- `is_contested -> bool` — checks CONTEST_INDICATOR_FORMS in season filings (cached) — `season.py:283`
- `contest -> Optional[ProxyContest]` — built on demand (cached) — `season.py:290`
- `proxy -> ProxyStatement` — from anchor filing (cached) — `season.py:243`
- `related_filings -> List[Filing]` — all filings in window — `season.py:249`
- `preliminary_filings / supplemental_filings / exempt_solicitations` — tier-filtered views — `season.py:265-277`

#### ProxyContest (`edgar/proxy/contest.py:147`)
Analyze a contested proxy. All party labeling is lazy (network calls on first access).

- `dissidents -> List[str]` — unique dissident party names (cached, lazy header parse) — `contest.py:192`
- `parties -> Dict[str, str]` — all {name: party_type} (cached) — `contest.py:199`
- `timeline -> pd.DataFrame` — chronological table; cols: date/form/party/party_type/tier/accession_no (cached) — `contest.py:233`
- `is_settled -> bool` — management never filed DEFC14A heuristic (cached) — `contest.py:223`
- `management_filings / dissident_filings / third_party_filings` — filtered `List[SeasonFiling]` — `contest.py:208-219`

#### ProxyContests (`edgar/proxy/contests.py:33`)
Market-wide collection. Supports `len()`, `[]`, `.head()`, `.companies`, `.activists`.

- `proxy_contests(year, quarter) -> ProxyContests` — top-level function; scans EDGAR contest forms, groups by filer CIK — `contests.py:166`

#### HTML Extractor functions (`edgar/proxy/html_extractor.py`)
All operate on a shared `_html_tree` (lxml) or `_filing_text` (raw text) from ProxyStatement.

- `extract_voting_proposals(text) -> List[VotingProposal]` — regex "Proposal N" scan, 4-attempt recommendation retry — `html_extractor.py:136`
- `extract_ceo_pay_ratio(text) -> Optional[CEOPayRatio]` — finds pay-ratio section (skips TOC), extracts ratio/ceo/median with footnote-correction heuristic — `html_extractor.py:356`
- `extract_summary_compensation(tree) -> Optional[List[ExecutiveCompEntry]]` — lxml two-pass heading finder, column classifier — `html_extractor.py:830`
- `extract_beneficial_ownership(tree) -> Optional[List[BeneficialOwner]]` — section-header–aware row parser, distinguishes 5pct vs insider — `html_extractor.py:996`
- `extract_director_compensation(tree) -> Optional[List[DirectorCompEntry]]` — rejects 'salary' (would match SCT) — `html_extractor.py:1124`
- `extract_audit_fees(tree) -> Optional[AuditFees]` — year-column detection, multiplier detection (thousands/millions), auditor name regex — `html_extractor.py:1300`

#### MunicipalAdvisorForm (`edgar/muniadvisors.py:287`)
Parses MA-I XML via BeautifulSoup. Constructor takes explicit field objects; `from_filing` does full XML parse.

- `from_filing(filing) -> Optional[MunicipalAdvisorForm]` — asserts form in ['MA-I','MA-I/A'], calls `from_xml(filing.xml())` — `muniadvisors.py:319`
- `from_xml(xml) -> dict` — classmethod returning kwargs dict — `muniadvisors.py:328`
- Key attributes: `.filer (Filer)`, `.applicant (Applicant)`, `.contact (Contact)`, `.municipal_advisor_offices (List[MunicipalAdvisorOffice])`, `.employment_history (EmploymentHistory)`, `.disclosures (Disclosures)`, `.signature (Signature)`

#### Correspondence (`edgar/correspondence.py:194`)
Single CORRESP or UPLOAD letter.

- `from_filing(filing) -> Correspondence` — extracts text, calls `_classify_correspondence()`, extracts metadata from Re: block — `correspondence.py:230`
- `correspondence_type -> CorrespondenceType` — enum classification — `correspondence.py:297`
- `sender -> str` — 'company' or 'sec' — `correspondence.py:303`
- `referenced_file_number -> Optional[str]` — regex from Re: block e.g. '001-36743' — `correspondence.py:309`
- `referenced_form -> Optional[str]` — e.g. '10-K' — `correspondence.py:315`
- `thread -> Optional[CorrespondenceThread]` — lazily reconstructed (cached) — `correspondence.py:334`
- `body -> Optional[str]` — full text content — `correspondence.py:329`

#### CorrespondenceThread (`edgar/correspondence.py:422`)
Reconstructed conversation thread grouped by file number.

- `from_correspondence(corresp) -> Optional[CorrespondenceThread]` — fetches all CORRESP/UPLOAD for same company CIK, filters by file number and referenced_form — `correspondence.py:447`
- `entries -> List[Correspondence]` — chronologically sorted — `correspondence.py:499`
- `is_resolved -> bool` — last entry is REVIEW_COMPLETE — `correspondence.py:505`
- `duration_days -> Optional[int]` — days from first to last entry — `correspondence.py:511`
- `comment_count / response_count -> int` — SEC comment / company response counts — `correspondence.py:529-538`

#### NPX (`edgar/npx/npx.py:372`)
N-PX annual fund proxy voting record.

- `from_filing(filing) -> Optional[NPX]` — parses `primary_doc.xml` via `PrimaryDocExtractor`, finds proxy vote table XML via attachment scan — `npx.py:403`
- `proxy_votes -> Optional[ProxyVotes]` — the voting records container — `npx.py:723`
- `fund_name / cik / period_of_report / submission_type / is_amendment` — primary doc properties — `npx.py:486-513`
- `to_dataframe() -> pd.DataFrame` — single-row metadata DataFrame — `npx.py:737`

#### ProxyVotes (`edgar/npx/npx.py:44`)
Container for all `ProxyTable` entries in one N-PX filing.

- `to_dataframe() -> pd.DataFrame` — one row per VoteRecord; cols: issuer_name/cusip/isin/figi/meeting_date/vote_description/how_voted/shares_voted/management_recommendation/vote_categories/other_managers — `npx.py:58`
- `filter_by_issuer(name) -> ProxyVotes` — case-insensitive partial match — `npx.py:131`
- `filter_by_vote(how_voted) -> ProxyVotes` — e.g. 'AGAINST' — `npx.py:136`
- `filter_by_category(category) -> ProxyVotes` — common values: DIRECTOR ELECTIONS / SECTION 14A SAY-ON-PAY VOTES / AUDIT-RELATED / ENVIRONMENT OR CLIMATE — `npx.py:152`
- `against_management() -> ProxyVotes` — any vote != management_recommendation — `npx.py:179`
- `management_alignment_rate() -> float` — 0.0-1.0 float — `npx.py:210`
- `summary_by_category() -> pd.DataFrame` — for/against/abstain/other/with_mgmt/against_mgmt by category — `npx.py:242`
- `summary() -> pd.DataFrame` — vote counts by how_voted type — `npx.py:313`

#### TenD (`edgar/abs/ten_d.py:84`)
10-D ABS distribution report.

- Constructor takes `filing`; asserts form in ('10-D', '10-D/A') — `ten_d.py:108`
- `issuing_entity / depositor / sponsors -> Optional[ABSEntity] / List[ABSEntity]` — lazy parsed from HTML (cached via `_ensure_header_parsed()`) — `ten_d.py:344-363`
- `distribution_period -> Optional[DistributionPeriod]` — from HTML header — `ten_d.py:363`
- `security_classes -> List[str]` — from HTML "title of class" table — `ten_d.py:369`
- `abs_type -> ABSType` — CMBS detected by EX-102 attachment; others by company name keywords (cached) — `ten_d.py:374`
- `has_asset_data -> bool` — checks for EX-102 attachment — `ten_d.py:414`
- `asset_data -> Optional[CMBSAssetData]` — CMBS-only; returns None otherwise (cached) — `ten_d.py:431`
- `loans -> pd.DataFrame` — convenience delegator to `asset_data.loans` — `ten_d.py:459`
- `properties -> pd.DataFrame` — convenience delegator to `asset_data.properties` — `ten_d.py:478`
- Note: `distribution_report` property is deferred (only ~42% extraction accuracy across ABS types) — `ten_d.py:498`

#### CMBSAssetData (`edgar/abs/cmbs.py:137`)
Parses CMBS EX-102 XML from stdlib `xml.etree.ElementTree`.

- Constructor: `__init__(xml_content: str)` — `cmbs.py:288`
- `from_filing()` not present; TenD's `asset_data` calls constructor with `_get_exhibit('EX-102')` content
- `loans -> pd.DataFrame` — ~45 fields including loan_id/original_amount/actual_balance/current_rate/payment_status/is_modified/dscr fields (cached) — `cmbs.py`
- `properties -> pd.DataFrame` — ~45 fields including name/city/state/property_type/valuation/occupancy/noi/dscr (cached) — `cmbs.py`
- `summary() -> CMBSSummary` — aggregated statistics — `cmbs.py`
- Namespace: `http://www.sec.gov/edgar/document/absee/cmbs/assetdata` — `cmbs.py:24`

#### AutoLeaseAssetData (`edgar/abs/abs_ee.py:70`)
Parses ABS-EE EX-102 XML for auto-lease securitizations (BMW et al).

- `from_filing(filing) -> Optional[AutoLeaseAssetData]` — finds EX-102 attachment by document_type — `abs_ee.py:154`
- `assets -> pd.DataFrame` — ~35 cols: asset_id/vehicle_manufacturer/vehicle_model/credit_score/acquisition_cost/lessee_state/delinquency_status etc. — `abs_ee.py:267`
- `summary() -> AutoLeaseSummary` — num_assets/total_acquisition_cost/avg_credit_score/vehicle_makes/states etc. — `abs_ee.py:285`
- Namespaces: autolease `http://www.sec.gov/edgar/document/absee/autolease/assetdata`, autoloan equivalent — `abs_ee.py:46`

#### AlternativeTradingSystem (`edgar/ats/atsn.py:107`)
ATS-N/MA/UA/CA three-part disclosure.

- `from_filing(filing) -> Optional[AlternativeTradingSystem]` — parses `primary_doc.xml` via `_parse_xml`, then calls `_apply_oversized_pdfs()` — `atsn.py:218`
- `ats_name -> Optional[str]` — commercial ATS name — `atsn.py:138`
- `operator_name -> Optional[str]` — legal name of the BD operator — `atsn.py:143`
- `mpid -> Optional[str]` — FINRA market participant ID — `atsn.py:135`
- `is_amendment -> bool` — form in (ATS-N/MA, ATS-N/UA, ATS-N/CA) — `atsn.py:147`
- `subscriber_types -> list` — from Part III Item 1 — `atsn.py:151`
- `order_types -> Optional[str]` — Part III Item 7 narrative — `atsn.py:155`
- `fees -> dict` — `{'direct': ..., 'bundled': ..., 'rebates': ...}` from Part III Item 19 — `atsn.py:159`
- `identifying_info -> ATSIdentifyingInfo` — Part I Pydantic model — `atsn.py:124`
- `operator_activities -> ATSOperatorActivities` — Part II Pydantic model — `atsn.py:125`
- `operations -> ATSOperations` — Part III Pydantic model; ~60 fields — `atsn.py:126`
- `_OVERSIZED_PDF_MAP` — surfacing PDF URLs for Items 7A/9A/11C/13A when XML exceeds length — `atsn.py:210`

#### BDCDataset (`edgar/bdc/datasets.py:447`)
Quarterly DERA bulk extract.

- `fetch_bdc_dataset(year, quarter) -> BDCDataset` — downloads ZIP, parses sub.tsv/num.tsv/pre.tsv/soi.tsv — `datasets.py:723`
- `fetch_bdc_dataset_monthly(year, month)` — monthly variant — `datasets.py`
- `.submissions / .numbers / .presentation / .soi` — raw DataFrames — `datasets.py:462-467`
- `schedule_of_investments -> ScheduleOfInvestmentsData` — wrapped SOI with subsetting — `datasets.py:494`
- `summary_by_company() / summary_by_industry()` — aggregate views — `datasets.py:583-648`
- `get_facts_by_tag(tag) -> pd.DataFrame` — cross-BDC XBRL concept query — `datasets.py:571`

#### ScheduleOfInvestmentsData (`edgar/bdc/datasets.py:136`)
SOI wrapper.

- `__getitem__(cik_or_entity)` — filter to one BDC by CIK or BDCEntity — `datasets.py:173`
- `search(query) -> pd.DataFrame` — case-insensitive company name search, returns company/bdc_name/bdc_cik/fair_value — `datasets.py:280`
- `top_companies(n) -> pd.DataFrame` — cross-BDC aggregation by portfolio company — `datasets.py:351`
- `to_dataframe(clean=False) -> pd.DataFrame` — if clean=True, applies `_COLUMN_RENAMES` + `[Member]` stripping — `datasets.py:227`

#### BDCEntity (`edgar/bdc/reference.py:41`)
Represents one BDC from the SEC BDC Report.

- `is_active -> bool` — filed within last 18 months — `reference.py:59`
- `portfolio_investments() -> PortfolioInvestments` — fetches latest 10-K XBRL, extracts SOI — (on BDCEntity, delegated to investments module)

#### extract_nonaccrual / NonAccrualResult (`edgar/bdc/nonaccrual.py`)
Three-layer extraction: XBRL footnotes → custom concepts → standard us-gaap aggregate.

- `extract_nonaccrual(filing) -> NonAccrualResult` — primary entry point — `nonaccrual.py`
- `NonAccrualResult.nonaccrual_rate / .num_nonaccrual / .investments` — key output fields

#### XmlFiling (`edgar/xmlfiling.py:140`)
Generic fallback for XML-native forms without dedicated parsers.

- `from_filing(filing) -> Optional[XmlFiling]` — parses XML with lxml, strips namespaces, converts to nested dict — `xmlfiling.py:172`
- `form_data -> dict` — formData XML tree as nested dict — `xmlfiling.py:228`
- `header_data -> dict` — headerData XML tree — `xmlfiling.py:233`
- `__getitem__(key)` — deep recursive key search in form_data — `xmlfiling.py:241`
- `get(key, default)` — deep key lookup with default — `xmlfiling.py:245`
- `to_html() -> Optional[str]` — network request to SEC XSLT endpoint — `xmlfiling.py:259`
- `description -> str` — human-readable form type string — `xmlfiling.py:237`
- `is_amendment -> bool` — '/A' in form — `xmlfiling.py:223`

---

### Class hierarchy

```
object
├── ProxyStatement                            # edgar/proxy/core.py
│   └── (uses) ProxyStatement._html_tree     # shared lxml parse
├── ProxySeason                               # edgar/proxy/season.py
│   └── (has) ProxyContest
├── ProxyContest                              # edgar/proxy/contest.py
├── ProxyContests                             # edgar/proxy/contests.py
│
├── MunicipalAdvisorForm                      # edgar/muniadvisors.py
│   ├── Filer, Contact, Applicant, Signature
│   ├── EmploymentHistory → List[Employer]
│   ├── List[MunicipalAdvisorOffice] → List[Office]
│   └── Disclosures → CriminalDisclosure, RegulatoryDisclosure, CivilDisclosure,
│                     ComplaintDisclosure, TerminationDisclosure, FinancialDisclosure,
│                     JudgementLienDisclosure, InvestigationDisclosure
│
├── Correspondence                            # edgar/correspondence.py
│   └── (has lazy) CorrespondenceThread → List[Correspondence]
│
├── NPX                                       # edgar/npx/npx.py
│   ├── (owns) PrimaryDoc                    # edgar/npx/models.py
│   └── (owns) ProxyVotes → List[ProxyTable] → List[VoteRecord]
│
├── TenD                                      # edgar/abs/ten_d.py
│   ├── List[ABSEntity]
│   ├── DistributionPeriod
│   └── (lazy) CMBSAssetData                 # edgar/abs/cmbs.py
│       ├── loans DataFrame
│       └── properties DataFrame
│
├── AutoLeaseAssetData                        # edgar/abs/abs_ee.py (direct, not via TenD)
│
├── AlternativeTradingSystem                  # edgar/ats/atsn.py
│   ├── FilerContact                          # edgar/ats/models.py (Pydantic)
│   ├── ATSIdentifyingInfo (Pydantic)
│   ├── ATSOperatorActivities (Pydantic)
│   └── ATSOperations (Pydantic)
│
├── BDCDataset                                # edgar/bdc/datasets.py (dataclass)
│   └── (property) ScheduleOfInvestmentsData
│
├── BDCEntity                                 # edgar/bdc/reference.py (dataclass)
├── BDCEntities                               # edgar/bdc/reference.py
│
├── PortfolioInvestment                       # edgar/bdc/investments.py (dataclass)
├── PortfolioInvestments                      # edgar/bdc/investments.py
│
└── XmlFiling                                 # edgar/xmlfiling.py

# Data/model classes (frozen dataclasses unless noted):
NamedExecutive, ExecutiveCompensation, PayVsPerformance, SeasonFiling  — edgar/proxy/models.py
VotingProposal, CEOPayRatio, ExecutiveCompEntry, BeneficialOwner,
DirectorCompEntry, AuditFees                                           — edgar/proxy/html_extractor.py
PrimaryDoc, ProxyTable, VoteRecord, VoteCategory, IncludedManager,
ReportSeriesClassInfo, SeriesReport                                    — edgar/npx/models.py
ABSEntity, DistributionPeriod                                          — edgar/abs/ten_d.py
CMBSSummary, AutoLeaseSummary                                         — edgar/abs/cmbs.py, abs_ee.py
DistributionMetrics, ReportTable                                       — edgar/abs/distribution.py
NonAccrualInvestment, NonAccrualResult                                 — edgar/bdc/nonaccrual.py
```

---

### Configuration & options

| Option | Type | Default | Effect |
|---|---|---|---|
| `ProxySeason.for_company(index=)` | int | 0 | 0=latest season, 1=previous, etc. |
| `proxy_contests(year=, quarter=)` | Optional[int] | current year / all quarters | Scans specific year+quarter |
| `ProxyStatement.to_context(detail=)` | str | 'standard' | 'minimal'/'standard'/'full' token budgets |
| `ProxyVotes.filter_by_vote(how_voted)` | str | — | 'FOR'/'AGAINST'/'ABSTAIN'/'WITHHOLD' |
| `ProxyVoteTableExtractor` | bytes | — | Uses `iterparse` for memory efficiency on large XML |
| `PrimaryDocExtractor` namespaces | dict | `npx: .../npx` + `com: .../common` | SEC-defined XML namespaces |
| `fetch_bdc_dataset(year, quarter)` | int, int | — | quarter must be 1-4; raises ValueError otherwise |
| `get_available_quarters(max_years_back=)` | int | 5 | Years back to probe; results cached via `@lru_cache(maxsize=1)` |
| `ScheduleOfInvestmentsData.to_dataframe(clean=)` | bool | False | If True, applies `_COLUMN_RENAMES` and strips `[Member]`/` Axis` suffixes |
| `BDCEntity.is_active` cutoff | — | 18 months | `dateutil.relativedelta(months=18)` from today |
| `XmlFiling.to_html()` timeout | — | 15s | httpx.get timeout for XSLT endpoint |
| `CMBSAssetData` date format | — | MM-DD-YYYY | `_parse_xml_date()` in cmbs.py |
| `AutoLeaseAssetData` date format | — | MM-DD-YYYY (`_parse_date`) / MM/YYYY (`_parse_month_year`) | Two distinct date helpers |
| `extract_ceo_pay_ratio` footnote heuristic | — | value > $200M → strip last digit | Removes embedded footnote superscripts |

---

### Data flow / lifecycle

**ProxyStatement:**
- `filing.obj()` → dispatch in `edgar/__init__.py:415` → `ProxyStatement(filing)` (stores filing reference only)
- XBRL path: `._xbrl_data` (cached property) calls `filing.xbrl()` → `._facts_dataframe` (cached) converts to DataFrame → `_get_concept_value()` / `_get_concept_series()` query by concept name
- HTML path: `._filing_html` (cached) → `._html_tree` (cached, lxml parse ~100-200ms) → shared across all lxml-based extractors
- Text path: `._filing_text` (cached) prefers `filing.text()` over `filing.markdown()` to avoid pipe-character pollution in regex
- All compensation properties and DataFrame properties are `@cached_property` — computed once on first access

**ProxySeason:**
- `ProxySeason.for_company(company)` → `_find_anchors()` (fetches DEF 14A + DEFC14A filings, deduplicates by year, max 20 DEF 14A + 10 DEFC14A) → `_gather_season_filings()` (date-range query for all PROXY_FORMS) → `__init__`
- `contest` property builds `ProxyContest` lazily; `ProxyContest._labeled_filings` triggers header parsing (network) on first access

**Correspondence:**
- `from_filing()` calls `filing.text()` → regex extraction of Re: block → `_classify_correspondence()` based on form + content patterns
- `thread` property calls `CorrespondenceThread.from_correspondence()` which iterates all CORRESP/UPLOAD for the company CIK (can be many network calls)
- Filing.correspondence() in `_filings.py:2223` works on ANY filing type by building a synthetic anchor with the file_number from EDGAR metadata

**NPX:**
- `from_filing()` calls `filing.xml()` → `PrimaryDocExtractor(bytes).extract()` → scans attachments for XML containing `proxyVoteTable` → `ProxyVoteTableExtractor` uses `iterparse` for memory efficiency → `ProxyVotes(proxy_tables=...)`
- `ProxyVoteTableExtractor` yields `ProxyTable` objects; clears each element after processing to avoid memory accumulation

**TenD:**
- Constructor just stores filing reference; header is lazy via `_ensure_header_parsed()` (BeautifulSoup parse on first access to issuing_entity/depositor/sponsors/distribution_period/security_classes)
- `abs_type` (cached) checks for EX-102 attachment first (CMBS), then falls back to company name keywords
- `asset_data` (cached) reads EX-102 content and constructs `CMBSAssetData`

**ATS-N:**
- `from_filing()` calls `filing.xml()` → `_parse_xml()` strips namespaces → parses 3 parts (cover/partOne/partTwo/partThree) into Pydantic models → `_apply_oversized_pdfs()` scans attachments for PDF URLs for oversized narrative fields

**BDC datasets:**
- `fetch_bdc_dataset()` downloads ZIP via `get_with_retry` → extracts sub.tsv/num.tsv/pre.tsv/soi.tsv → returns `BDCDataset` dataclass (all DataFrames in memory)
- `schedule_of_investments` wraps `soi` DataFrame in `ScheduleOfInvestmentsData`; `__getitem__` by CIK filters on `cik` column
- `get_available_quarters()` probes SEC URLs with 5s timeout; `@lru_cache(maxsize=1)` — returns stale if called repeatedly in a session

**XmlFiling:**
- `from_filing()` calls `filing.xml()` → lxml parse → `_strip_namespaces()` → `_element_to_dict()` recursively converts to nested dict (repeated tags become lists)
- `to_html()` makes a live network request to `https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{xslt_prefix}/primary_doc.xml`

---

### Design patterns

- **Lazy/cached properties**: All heavy computations in ProxyStatement (XBRL load, HTML parse, all DataFrame extractions) use `@cached_property`. TenD header parsing uses an `_ensure_header_parsed()` guard. NPX `_extract_proxy_votes` called once in `from_filing`.
- **Dual extraction paths in ProxyStatement**: XBRL for structured/numeric fields (peo_total_comp, etc.), lxml DOM for HTML tables (SCT, ownership, director comp). Filing text (not markdown) used for regex to avoid table-formatting noise.
- **Two-pass heading finder in HTML extractor**: First scan excludes elements inside `<table>` tags; second pass includes them. Avoids false matches on TOC entries — `html_extractor.py:716`.
- **Gate-flag dual-pattern resolution for ATS-N**: SEC XML uses Y/N gate flags both as element text (when "N") and as attribute on container (when "Y"). `_gate()` helper resolves both — `atsn.py:47`.
- **iterparse for NPX**: `ProxyVoteTableExtractor` uses `ET.iterparse` and clears elements after processing — `parsing.py:597`. Prevents OOM on large fund filings with thousands of votes.
- **Factory classmethod pattern**: All major objects expose `from_filing(filing)` as the canonical entry point, returning `Optional[Self]` on failure rather than raising.
- **`_element_to_dict` with list coalescing for XmlFiling**: Repeated sibling tags are coerced to list; first occurrence is a scalar — `xmlfiling.py:93`.
- **Tiered form classification**: `classify_proxy_tier()` assigns 1-5 tier; `SeasonFiling.tier` carries it through — avoids re-parsing form strings in downstream consumers.
- **Generous-inclusion on DEFC14A**: When CIK resolution fails in `_find_anchors`, the filing is included conservatively rather than excluded — `season.py:143`.

---

### Cross-domain interactions

**Imports FROM other edgar.* modules:**

| Module | Imports from |
|---|---|
| `edgar/proxy/core.py` | `edgar.richtools`, `edgar.xbrl` (via `filing.xbrl()`), `edgar.documents.utils.html_utils` |
| `edgar/proxy/season.py` | `edgar.entity.core.Entity`, `edgar.proxy.contest`, `edgar.proxy.models` |
| `edgar/proxy/contests.py` | `edgar._filings.get_filings`, `edgar.reference.tickers.find_ticker` |
| `edgar/muniadvisors.py` | `edgar._party.Address/Name`, `edgar.xmltools.child_text/child_texts/child_value` |
| `edgar/correspondence.py` | `edgar.Company` (inside `from_correspondence()` for thread reconstruction) |
| `edgar/npx/npx.py` | `edgar._filings.Filing` (TYPE_CHECKING only) |
| `edgar/abs/ten_d.py` | `edgar.abs.cmbs.CMBSAssetData` (deferred import to avoid circular) |
| `edgar/ats/atsn.py` | `edgar.funds.reports._strip_namespaces/_text`, `edgar.ats.models` |
| `edgar/bdc/datasets.py` | `edgar.httprequests.get_with_retry` |
| `edgar/bdc/reference.py` | `edgar.display.formatting.cik_text`, `edgar.httprequests.get_with_retry` |
| `edgar/bdc/nonaccrual.py` | `edgar.bdc.investments._parse_investment_identifier` |
| `edgar/xmlfiling.py` | `edgar._filings.Filing` (TYPE_CHECKING) |

**Consumed by:**

- `edgar/__init__.py:195` — `get_obj_info()` + dispatch function routes all `filing.obj()` calls
- `edgar/_filings.py:2223` — Filing.correspondence() builds thread from any filing
- `edgar.ai.mcp.tools.proxy` — MCP tool surface for proxy data

---

### Gotchas & notable behaviors

**ProxyStatement:**
- `has_xbrl` returns False for SRCs, EGCs, SPACs, and registered investment companies — they are exempt from ECD XBRL tagging. All XBRL-dependent properties return None in that case.
- `named_executives` only populated when company uses dimensional XBRL tagging (~60% of filers). Check `has_individual_executive_data` first.
- `voting_proposals` caps at proposal number 30 to filter out page numbers that match the regex — `html_extractor.py:167`.
- CEO pay ratio extractor has footnote-superscript correction: if value > $200M, strips last digit; cross-checks against stated ratio — `html_extractor.py:427-437`.
- `_filing_text` prefers `filing.text()` over `filing.markdown()` specifically because markdown table formatting (pipes) pollutes regex — `core.py:426`.
- `lxml` parse takes ~100-200ms for 1MB proxy statement; `_html_tree` is shared via `cached_property` so all HTML extractors pay this cost only once.

**ProxySeason:**
- `for_company(index=0)` always returns the latest season. If you pass an older ProxyStatement filing, its `.season` property may return a more recent season than the filing itself.
- Season window uses `filing_date` range queries, not fiscal year. Cross-year annual meetings may span calendar years.
- Deduplicated by year: if both DEF 14A and DEFC14A exist for the same year (settlement case), DEF 14A takes precedence — `season.py:159`.

**Correspondence:**
- Thread reconstruction fetches ALL CORRESP/UPLOAD for the company and re-parses each one — can be slow for prolific filers.
- `CorrespondenceThread.from_correspondence()` returns None (not raises) if `referenced_file_number` is absent.
- `Filing.correspondence()` in `_filings.py:2223` works on non-correspondence filings by building a synthetic anchor with the EDGAR-metadata file number.

**NPX:**
- `proxy_votes` is None (not empty ProxyVotes) if no proxy vote table XML found in attachments.
- Vote table XML is looked for first in `attachments.data_files`, then in `attachments.documents`; skips files named 'primary'. Checks for `proxyVoteTable` in content.
- `management_alignment_rate()` returns 1.0 (not 0.0) when there are no vote records with management recommendations — vacuous-truth behavior.

**TenD / ABS:**
- `abs_type` detection for CMBS relies on EX-102 attachment presence, not content. If an EX-102 is absent, even a CMBS filing will not get `ABSType.CMBS`.
- `distribution_report` extraction was commented out because validation showed only ~42% accuracy across ABS types. Raw HTML is accessible via `filing.html()`.
- `AutoLeaseAssetData.from_filing()` scans all attachments for document_type containing 'EX-102'; returns None if not found.
- CMBS XML namespace is `http://www.sec.gov/edgar/document/absee/cmbs/assetdata`; ABS-EE uses separate autolease/autoloan namespaces.

**ATS-N:**
- Gate flags in SEC XML appear in two mutually exclusive patterns: as element text when "N", as attribute on container when "Y". `_gate()` searches both — `atsn.py:47`.
- Oversized narrative fields (Items 7A, 9A, 11C, 13A) may have their authoritative text in PDF attachments. `_apply_oversized_pdfs()` always sets the URL; the XML field may also be non-empty. PDF is an extended version, not replacement.
- `AlternativeTradingSystemWithdrawal` handles ATS-N-W; identity lives in the header (not Part I, which does not exist).

**BDC:**
- `get_available_quarters()` probes live SEC URLs with 5s timeout. `@lru_cache(maxsize=1)` means result is stale for the lifetime of the Python process.
- `ScheduleOfInvestmentsData.__getitem__` accepts both `int` (CIK) and any object with a `.cik` attribute (BDCEntity).
- SOI `.to_dataframe(clean=True)` removes `[Member]` suffixes and simplifies axis column names via `_COLUMN_RENAMES`; default is False (raw columns).
- `extract_nonaccrual` uses three-layer fallback: XBRL footnotes (richest, but rare) → custom concepts (6/11 BDCs) → standard us-gaap aggregate (1/11 BDCs). Negation patterns are checked BEFORE affirmative patterns to prevent false positives from policy disclosures.
- BDC file numbers start with "814-"; `is_bdc_cik()` uses this as the identifier.

**XmlFiling:**
- `_element_to_dict()` coalesces repeated sibling tags into a list; single-child tags remain scalars. The type of a field value depends on how many times the tag appears, which varies by filing.
- `to_html()` makes a live HTTPS call to the SEC XSLT endpoint. Returns None on any network or HTTP error, not raising.
- XSLT URL pattern: `https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_dashes}/{xslt_prefix}/primary_doc.xml`
- `XML_FILING_FORMS` is built programmatically from `_XSLT_PREFIXES` keys plus `/A` variants — dynamically includes amendments.
