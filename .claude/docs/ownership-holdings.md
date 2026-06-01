## Ownership & Institutional Holdings

### Overview

This domain covers the "who owns what" SEC filings: Forms 3/4/5 (insider ownership and transactions), Schedule 13D/13G (5%+ beneficial ownership reports), 13F-HR (institutional quarterly holdings), and Form 144 (restricted-stock sale notices). The domain converts raw SEC XML into typed Python objects with pandas DataFrames, rich terminal rendering, and AI-optimized context strings. Every object in this domain is accessed via `filing.obj()`, which dispatches by form code through the `obj()` function in `/Users/elod.szopos/Projects/edgartools/edgar/__init__.py:307`.

---

### Public API surface

| Symbol | file:line | Purpose |
|---|---|---|
| `Form3` | `edgar/ownership/ownershipforms.py:2249` | Initial insider ownership statement (initial filing) |
| `Form4` | `edgar/ownership/ownershipforms.py:2260` | Statement of changes in insider ownership |
| `Form5` | `edgar/ownership/ownershipforms.py:2271` | Annual insider ownership summary |
| `Ownership` | `edgar/ownership/ownershipforms.py:1732` | Base class for Form 3/4/5; parse entry point |
| `Ownership.parse_xml` | `edgar/ownership/ownershipforms.py:2021` | Parse XML string → constructor kwargs dict |
| `Ownership.from_xml` | `edgar/ownership/ownershipforms.py:2016` | Parse XML string → `Ownership` instance |
| `Ownership.get_ownership_summary` | `edgar/ownership/ownershipforms.py:1935` | Returns `InitialOwnershipSummary` (F3) or `TransactionSummary` (F4/F5) |
| `Ownership.to_dataframe` | `edgar/ownership/ownershipforms.py:1982` | Convert to DataFrame; `detailed=True` → one row per tx |
| `Ownership.get_transaction_activities` | `edgar/ownership/ownershipforms.py:1824` | List of `TransactionActivity` objects |
| `Ownership.to_context` | `edgar/ownership/ownershipforms.py:2083` | AI context string; `detail='minimal'/'standard'/'full'` |
| `Ownership.to_html` | `edgar/ownership/ownershipforms.py:2233` | HTML render via Jinja2 template |
| `TransactionActivity` | `edgar/ownership/ownershipforms.py:1094` | Dataclass for a single transaction event |
| `TransactionCode` | `edgar/ownership/ownershipforms.py:144` | Transaction code constants + descriptions |
| `InitialOwnershipSummary` | `edgar/ownership/ownershipforms.py:1239` | Dataclass summary for Form 3 |
| `TransactionSummary` | `edgar/ownership/ownershipforms.py:1401` | Dataclass summary for Form 4/5 |
| `NonDerivativeTable` | `edgar/ownership/ownershipforms.py:604` | Container for common-stock holdings + transactions |
| `DerivativeTable` | `edgar/ownership/ownershipforms.py:766` | Container for derivative holdings + transactions |
| `NonDerivativeHoldings` | `edgar/ownership/ownershipforms.py:447` | DataFrame wrapper for common-stock static holdings |
| `NonDerivativeTransactions` | `edgar/ownership/ownershipforms.py:544` | DataFrame wrapper for common-stock transactions |
| `DerivativeHoldings` | `edgar/ownership/ownershipforms.py:407` | DataFrame wrapper for derivative static holdings |
| `DerivativeTransactions` | `edgar/ownership/ownershipforms.py:479` | DataFrame wrapper for derivative transactions |
| `Footnotes` | `edgar/ownership/ownershipforms.py:285` | Dict wrapper for form footnotes |
| `Owner` | `edgar/ownership/ownershipforms.py:931` | Frozen dataclass for a reporting owner |
| `ReportingOwners` | `edgar/ownership/ownershipforms.py:977` | List wrapper for `Owner` instances |
| `Issuer` | `edgar/ownership/ownershipforms.py:107` | Issuer identity (CIK, name, ticker) |
| `detect_10b5_1_plan` | `edgar/ownership/core.py:202` | Detect 10b5-1 trading plan from footnote text |
| `ownership_to_html` | `edgar/ownership/html_render.py:61` | Render `Ownership` to SEC-style HTML via Jinja2 |
| `Schedule13D` | `edgar/beneficial_ownership/schedule13.py:103` | Active beneficial ownership (activist) |
| `Schedule13G` | `edgar/beneficial_ownership/schedule13.py:521` | Passive institutional beneficial ownership |
| `Schedule13D.from_filing` | `edgar/beneficial_ownership/schedule13.py:341` | Construct from `Filing`; asserts form is SC 13D |
| `Schedule13G.from_filing` | `edgar/beneficial_ownership/schedule13.py:785` | Construct from `Filing`; asserts form is SC 13G |
| `ReportingPerson` | `edgar/beneficial_ownership/models.py:23` | Frozen dataclass for a 13D/G filer |
| `IssuerInfo` | `edgar/beneficial_ownership/models.py:57` | Subject company info (CIK, name, CUSIP) |
| `Schedule13DItems` | `edgar/beneficial_ownership/models.py:82` | Narrative Items 1–7 for 13D |
| `Schedule13GItems` | `edgar/beneficial_ownership/models.py:123` | Structured items 1–10 for 13G |
| `AmendmentInfo` | `edgar/beneficial_ownership/amendments.py:17` | Tracks amendment metadata |
| `OwnershipComparison` | `edgar/beneficial_ownership/amendments.py:62` | Compare two 13D/G filings for share/pct delta |
| `ThirteenF` | `edgar/thirteenf/models.py:190` | 13F-HR quarterly holdings report |
| `ThirteenF.holdings` | `edgar/thirteenf/models.py:372` | `cached_property`; aggregated DataFrame, one row/security |
| `ThirteenF.infotable` | `edgar/thirteenf/models.py:339` | `cached_property`; disaggregated DataFrame by manager |
| `ThirteenF.compare_holdings` | `edgar/thirteenf/models.py:933` | QoQ comparison returning `HoldingsComparison` |
| `ThirteenF.holding_history` | `edgar/thirteenf/models.py:1018` | Multi-quarter history returning `HoldingsHistory` |
| `ThirteenF.previous_holding_report` | `edgar/thirteenf/models.py:773` | Prior quarter `ThirteenF` |
| `ThirteenF.holdings_view` | `edgar/thirteenf/models.py:921` | `HoldingsView` (renderable + iterable) |
| `HoldingsView` | `edgar/thirteenf/models.py:89` | Rich-renderable, iterable holdings wrapper |
| `HoldingsComparison` | `edgar/thirteenf/models.py:121` | QoQ holdings diff with status labels |
| `HoldingsHistory` | `edgar/thirteenf/models.py:156` | Multi-period sparkline history |
| `parse_infotable_xml` | `edgar/thirteenf/parsers/infotable_xml.py:11` | Parse XML infotable → DataFrame |
| `parse_infotable_txt` | `edgar/thirteenf/parsers/infotable_txt/__init__.py:18` | Parse TXT infotable (auto-detects format) → DataFrame |
| `parse_primary_document_xml` | `edgar/thirteenf/parsers/primary_xml.py:16` | Parse primary 13F XML → `PrimaryDocument13F` |
| `lookup_portfolio_managers` | `edgar/thirteenf/manager_lookup.py:14` | Lookup known portfolio managers by name or CIK |
| `Form144` | `edgar/form144.py:438` | Restricted stock sale notice |
| `Form144.from_filing` | `edgar/form144.py:878` | Construct from `Filing`; asserts form is '144' |
| `Form144.to_analyst_summary` | `edgar/form144.py:754` | Full analyst metrics dict |
| `concat_securities_information` | `edgar/form144.py:1225` | Concat `securities_information` from list of Form144 |
| `concat_securities_to_be_sold` | `edgar/form144.py:1229` | Concat `securities_to_be_sold` from list of Form144 |

---

### Key classes

#### Ownership (Form 3/4/5 base)

`Ownership` — owns all parsed data for one insider filing. Never instantiated directly; `Form3`, `Form4`, `Form5` are thin subclasses that each delegate to `Ownership.parse_xml`.

- `parse_xml(content: str) -> dict` — classmethod; parses `<ownershipDocument>` XML via BeautifulSoup and returns a kwargs dict; `from_xml` calls `cls(**cls.parse_xml(...))` — `edgar/ownership/ownershipforms.py:2021`
- `get_ownership_summary() -> Union[InitialOwnershipSummary, TransactionSummary]` — dispatches on `self.form == "3"` for holdings vs transactions — `edgar/ownership/ownershipforms.py:1935`
- `get_transaction_activities() -> List[TransactionActivity]` — walks market trades, non-market trades, and derivative transactions; resolves footnote IDs to full text — `edgar/ownership/ownershipforms.py:1824`
- `extract_form3_holdings() -> List[SecurityHolding]` — extracts non-derivative and derivative holdings for Form 3 — `edgar/ownership/ownershipforms.py:1768`
- `to_dataframe(detailed=True, include_metadata=True) -> pd.DataFrame` — delegates to `get_ownership_summary().to_dataframe()` — `edgar/ownership/ownershipforms.py:1982`
- `to_context(detail='standard') -> str` — AI-optimized text with `minimal/standard/full` tiers — `edgar/ownership/ownershipforms.py:2083`
- `to_html() -> str` — calls `ownership_to_html(self)` — `edgar/ownership/ownershipforms.py:2233`
- `market_trades` — `cached_property`; filters non-derivative transactions to codes P and S — `edgar/ownership/ownershipforms.py:1910`
- `derivative_trades` — `cached_property`; exposes derivative table's trades — `edgar/ownership/ownershipforms.py:2005`

Key attributes set in `__init__`: `form`, `footnotes`, `issuer`, `reporting_owners`, `non_derivative_table`, `derivative_table`, `signatures`, `reporting_period`, `remarks`, `no_securities`.

#### TransactionActivity (dataclass)

Normalized transaction event built by `get_transaction_activities()`. Carries `transaction_type` (string: `"purchase"`, `"sale"`, `"exercise"`, `"award"`, `"tax"`, `"gift"`, `"conversion"`, `"derivative_purchase"`, `"derivative_sale"`, `"other_acquisition"`, `"other_disposition"`), plus `code`, `shares`, `price_per_share`, `value`, `security_type`, `security_title`, `underlying_security`, `footnote_ids` (newline-separated), `footnotes_text` (resolved).

- `is_10b5_1_plan -> Optional[bool]` — delegates to `detect_10b5_1_plan(self.footnotes_text)` — `edgar/ownership/ownershipforms.py:1132`
- `shares_numeric`, `value_numeric`, `price_numeric` — safe numeric conversions that handle footnote-embedded strings — `edgar/ownership/ownershipforms.py:1112`

#### TransactionSummary (dataclass, Form 4/5)

- `net_change -> int` — purchases minus sales share count — `edgar/ownership/ownershipforms.py:1450`
- `has_10b5_1_plan -> Optional[bool]` — aggregates across all transactions — `edgar/ownership/ownershipforms.py:1422`
- `primary_activity -> str` — dominant activity label (e.g. "Purchase", "Sale", "DERIVATIVE TRANSACTIONS") — `edgar/ownership/ownershipforms.py:1468`
- `to_dataframe(include_metadata=True, detailed=True) -> pd.DataFrame` — `detailed=False` returns one summary row; `detailed=True` returns one row per transaction — `edgar/ownership/ownershipforms.py:1502`

#### NonDerivativeTable / DerivativeTable

Both follow the same pattern. Each holds a `holdings` (`*Holdings`) and `transactions` (`*Transactions`) DataHolder. `extract(table: Tag, form: str)` is the classmethod that builds from BeautifulSoup tag. `NonDerivativeTable` additionally exposes `market_trades` (codes P/S), `non_market_trades`, and `exercised_trades` (TransactionType=='Exercise').

#### Schedule13D / Schedule13G

Both classes are structurally parallel. Key differences:

- 13D: has `items: Schedule13DItems` (Items 1–7, with `item4_purpose_of_transaction` the most analytically important); `date_of_event` attribute.
- 13G: has `items: Schedule13GItems` (Items 1–10, mostly N/A flags); `event_date` attribute; `rule_designation` for filer type; `is_passive_investor` always `True`.
- Both: `from_filing(cls, filing)` asserts the filing form, calls `filing.xml()`, then `cls.parse_xml(xml)`, extracts amendment number, and passes all to constructor. Returns `None` if no XML found.
- `total_shares -> int` — `max(p.aggregate_amount for p in included_persons)` — the correct aggregate for group filers is `max`, not `sum`, because co-filers overlap. Excludes persons with `is_aggregate_exclude_shares=True` — `edgar/beneficial_ownership/schedule13.py:381` (13D), `:824` (13G).
- `total_percent -> float` — same max-based logic.
- `is_amendment -> bool` — checks `'/A' in self._filing.form`.
- XML root differs: 13D uses `<edgarSubmission>` with `<items1To7>`; 13G uses `<edgarSubmission>` with `<items>` containing 10 item elements.
- `to_context(detail='standard')` — three-tier AI context — `:424` (13D), `:873` (13G).

#### ReportingPerson (frozen dataclass)

Fields: `cik`, `name`, `citizenship`, `sole_voting_power`, `shared_voting_power`, `sole_dispositive_power`, `shared_dispositive_power`, `aggregate_amount`, `percent_of_class`, `type_of_reporting_person`, `fund_type` (Optional), `comment` (Optional), `member_of_group` (Optional; "a"=group member, "b"=separate filer), `is_aggregate_exclude_shares`, `no_cik`.
- `total_voting_power` / `total_dispositive_power` — sum sole + shared — `edgar/beneficial_ownership/models.py:47`

Note: In 13G XML, `reportingPersonCIK` is not present in `coverPageHeaderReportingPersonDetails`, so `cik` defaults to `''` — `edgar/beneficial_ownership/schedule13.py:654`.

#### OwnershipComparison

Compares two `Schedule13D` or `Schedule13G` instances. `shares_change` uses `sum` (not `max`) of both filings' `aggregate_amount` — `edgar/beneficial_ownership/amendments.py:81`. Properties: `is_accumulating`, `is_liquidating`, `is_unchanged`, `get_summary() -> dict`.

#### ThirteenF

- `__init__(filing, use_latest_period_of_report=False)` — asserts form in `THIRTEENF_FORMS`; optionally resolves to the last same-day filing; parses primary XML immediately if available (2013+); stores `primary_form_information: Optional[PrimaryDocument13F]` — `edgar/thirteenf/models.py:222`
- `infotable` — `cached_property`; detects XML vs TXT attachment, dispatches to `parse_infotable_xml` or `parse_infotable_txt`; applies ×1000 multiplier for pre-Q4-2022 filings — `edgar/thirteenf/models.py:339`
- `holdings` — `cached_property`; checks `_cache_provider` first; groups `infotable` by CUSIP, sums numeric cols, sorts by value descending — `edgar/thirteenf/models.py:372`
- `_value_in_thousands` — `True` if `report_period <= 2022-09-30` — `edgar/thirteenf/models.py:537`
- `previous_holding_report()` — searches PyArrow `data['reportDate']` for the prior quarter; prefers company's recent 40 filings (no network call), falls back to `_related_filings` — `edgar/thirteenf/models.py:773`
- `compare_holdings(display_limit=200) -> Optional[HoldingsComparison]` — outer-merges current/previous on CUSIP; adds `ShareChange`, `ValueChange`, `Status` (NEW/CLOSED/INCREASED/DECREASED/UNCHANGED) — `edgar/thirteenf/models.py:933`
- `holding_history(periods=3, display_limit=100) -> Optional[HoldingsHistory]` — walks backward via `previous_holding_report()`; deduplicates by `report_period`; builds wide DataFrame with one column per quarter — `edgar/thirteenf/models.py:1018`
- `management_company_name` — uses `investment_manager.name` if available, else `filing.company` — `edgar/thirteenf/models.py:572`
- `manager_name` — deprecated alias for `management_company_name`; emits `DeprecationWarning` — `edgar/thirteenf/models.py:631`
- `other_managers -> list[OtherManager]` — parsed from `summaryPage.otherManagers2Info` (not `coverPage`) — `edgar/thirteenf/models.py:505`
- `set_cache_provider(cls, provider)` — class-level external cache integration; callable `(accession_no) -> DataFrame | None` — `edgar/thirteenf/models.py:203`
- Static backward-compat aliases at module end delegate to parser sub-modules — `edgar/thirteenf/models.py:1264`

#### ThirteenF parsers

**`parse_infotable_xml`** (`edgar/thirteenf/parsers/infotable_xml.py:11`): Uses `lxml.etree` directly (10–20x faster than BeautifulSoup). Handles namespace detection (checks for `thirteenf` or `informationtable` in namespace URI). Extracts per-holding: `Issuer`, `Class`, `Cusip`, `Value` (int), `PutCall`, `InvestmentDiscretion`, `OtherManager`, `SharesPrnAmount`, `Type` (Shares/Principal), `SoleVoting`, `SharedVoting`, `NonVoting`. Appends `Ticker` via `cusip_ticker_mapping()`.

**`parse_infotable_txt`** (`edgar/thirteenf/parsers/infotable_txt/__init__.py:18`): Auto-detects format by `_is_columnar_format()` (looks for `<S>` tags co-occurring with CUSIPs in data rows). Dispatches to:
- `parse_columnar_format` — `<S>/<C>` tagged single-line format (e.g., JANA Partners style); all data on one line — `edgar/thirteenf/parsers/infotable_txt/format_columnar.py:19`
- `parse_multiline_format` — column-position-based parsing; primary strategy uses `<S>/<C>` marker-line positions; fallback is regex CUSIP scanning; handles multi-line company names (Berkshire Hathaway style) — `edgar/thirteenf/parsers/infotable_txt/format_multiline.py:454`

**`parse_primary_document_xml`** (`edgar/thirteenf/parsers/primary_xml.py:16`): Parses `<edgarSubmission>` XML via BeautifulSoup. Extracts `report_period` (format `%m-%d-%Y`), `CoverPage`, `SummaryPage`, `Signature`. Other managers are parsed from `<otherManagers2Info>` inside `<summaryPage>` (not `<coverPage>`) — `edgar/thirteenf/parsers/primary_xml.py:82`.

#### Form144

- `__init__` — wraps three DataFrames in holder classes: `_securities_information: SecuritiesInformationHolder`, `_securities_to_be_sold: SecuritiesToBeSoldHolder`, `_securities_sold_past_3_months: SecuritiesSoldPast3MonthsHolder` — `edgar/form144.py:438`
- `from_filing(cls, filing)` — asserts form in `['144', '144/A']`; calls `parse_xml` — `edgar/form144.py:878`
- `parse_xml(xml: str) -> dict` — parses `<edgarSubmission>` XML; extracts filer, contact, issuer, relationships, three security DataFrames, remarks, notice signature — `edgar/form144.py:800`
- `securities_information` / `securities_to_be_sold` / `securities_sold_past_3_months` — backward-compatible raw DataFrame properties — `edgar/form144.py:482`
- `securities_info` / `securities_selling` / `recent_sales` — new API returning holder objects with aggregation — `edgar/form144.py:499`
- `is_10b5_1_plan -> bool` — checks `notice_signature.plan_adoption_dates` after filtering 1933 placeholder dates — `edgar/form144.py:625`
- `days_since_plan_adoption -> Optional[int]` — from most recent valid plan date to `approx_sale_date` — `edgar/form144.py:630`
- `cooling_off_compliant -> Optional[bool]` — `days >= 90` (post-2022 SEC rule) — `edgar/form144.py:644`
- `holding_period_days` / `holding_period_years` — avg days from acquisition to sale — `edgar/form144.py:651`
- `anomaly_flags -> List[str]` — list of strings from: `LARGE_LIQUIDATION` (>5% of outstanding), `SHORT_HOLD` (<1 yr), `COOLING_OFF_VIOLATION`, `MULTIPLE_PLANS` — `edgar/form144.py:697`
- `to_analyst_summary() -> Dict[str, Any]` — full metrics dict for investment screening — `edgar/form144.py:754`
- `percent_of_holdings` — via `SecuritiesInformationHolder.percent_of_outstanding` — `edgar/form144.py:610`

---

### Class hierarchy

```
# Ownership / Forms 3, 4, 5
Ownership
├── Form3(Ownership)
├── Form4(Ownership)
└── Form5(Ownership)

Ownership attributes (composition):
├── issuer: Issuer
├── reporting_owners: ReportingOwners → List[Owner]
├── non_derivative_table: NonDerivativeTable
│   ├── holdings: NonDerivativeHoldings(DataHolder)
│   └── transactions: NonDerivativeTransactions(DataHolder)
├── derivative_table: DerivativeTable
│   ├── holdings: DerivativeHoldings(DataHolder)
│   └── transactions: DerivativeTransactions(DataHolder)
├── footnotes: Footnotes
└── signatures: OwnerSignatures → List[OwnerSignature]

Summary objects (returned from get_ownership_summary()):
OwnershipSummary (dataclass)
├── InitialOwnershipSummary(OwnershipSummary)  ← Form 3
│   └── holdings: List[SecurityHolding]
└── TransactionSummary(OwnershipSummary)       ← Form 4, Form 5
    └── transactions: List[TransactionActivity]

# Beneficial Ownership (13D/G)
Schedule13D
└── issuer_info: IssuerInfo
└── security_info: SecurityInfo
└── reporting_persons: List[ReportingPerson]
└── items: Schedule13DItems

Schedule13G
└── (same structure as 13D)
└── items: Schedule13GItems
└── rule_designation: Optional[str]

# 13F
ThirteenF
├── filing: Filing
├── primary_form_information: Optional[PrimaryDocument13F]
│   ├── cover_page: CoverPage → FilingManager
│   ├── summary_page: SummaryPage → List[OtherManager]
│   └── signature: Signature
├── infotable: pd.DataFrame (cached_property)
└── holdings: pd.DataFrame (cached_property, aggregated by CUSIP)

# Form 144
Form144
├── filer: Filer
├── contact: Contact
├── _securities_information: SecuritiesInformationHolder(SecuritiesHolder)
├── _securities_to_be_sold: SecuritiesToBeSoldHolder(SecuritiesHolder)
├── _securities_sold_past_3_months: SecuritiesSoldPast3MonthsHolder(SecuritiesHolder)
└── notice_signature: NoticeSignature
```

---

### Configuration & options

| Option | Type | Default | Effect |
|---|---|---|---|
| `Ownership.parse_xml` content | `str` | required | Raw XML of `<ownershipDocument>` element |
| `Ownership.to_dataframe` `detailed` | `bool` | `True` | `True` = one row per transaction/holding; `False` = one summary row |
| `Ownership.to_context` `detail` | `str` | `'standard'` | `'minimal'` ~100 tokens; `'standard'` ~300; `'full'` ~500+ |
| `ThirteenF.__init__` `use_latest_period_of_report` | `bool` | `False` | If True, resolves to the last same-day/same-form filing rather than the exact one passed |
| `ThirteenF.set_cache_provider(provider)` | callable | `None` | Class-level external cache for `holdings`; callable `(accession_no) -> DataFrame|None` |
| `ThirteenF.compare_holdings` `display_limit` | `int` | `200` | Max rows in Rich display; underlying DataFrame has all rows |
| `ThirteenF.holding_history` `periods` | `int` | `3` | Number of quarters to collect |
| `ThirteenF.holdings_view` `display_limit` | `int` | `200` | Max rows in Rich display |
| `_13F_VALUE_IN_THOUSANDS_CUTOFF` | `datetime` | `datetime(2022, 9, 30)` | Filings with `report_period` on or before this date have `Value` in thousands; auto-multiplied ×1000 — `edgar/thirteenf/models.py:30` |
| `Schedule13D.from_filing` forms | asserted | `['SCHEDULE 13D','SCHEDULE 13D/A','SC 13D','SC 13D/A']` | Raises `AssertionError` for wrong form type |
| `Schedule13G.from_filing` forms | asserted | `['SCHEDULE 13G','SCHEDULE 13G/A','SC 13G','SC 13G/A']` | Same |
| `Form144.from_filing` forms | asserted | `['144','144/A']` | Same |
| `TransactionSummary.to_dataframe` `include_metadata` | `bool` | `True` | Include issuer/insider/date columns |
| `lookup_portfolio_managers` `include_approximate` | `bool` | `False` | If True, includes non-active historical managers |

---

### Data flow / lifecycle

**Forms 3/4/5:**
1. `filing.obj()` → `edgar.__init__.obj()` dispatches on form code `'3'/'4'/'5'`
2. Calls `filing.xml()` to fetch raw XML string from EDGAR
3. `Ownership.parse_xml(xml)` uses BeautifulSoup (`"xml"` parser) to parse `<ownershipDocument>` root
4. Extracts: `form` (documentType), `footnotes` (all `<footnote>` tags keyed by `id`), `issuer`, `signatures`, `reporting_owners` (calls `Entity(int(cik))` to detect individual vs company for name reversal), `non_derivative_table`, `derivative_table`, `reporting_period`, `remarks`, `no_securities`
5. Returns kwargs dict; `from_xml` or subclass constructor wraps in typed object
6. User accesses `.non_derivative_table.transactions.data` (DataFrame), `.derivative_table.holdings.data`, `.market_trades` (cached), `.get_transaction_activities()` (builds `TransactionActivity` list, resolves footnotes), or `.get_ownership_summary()` (builds `InitialOwnershipSummary` or `TransactionSummary`)
7. `cached_property` on `market_trades` and `derivative_trades` prevents repeated filtering

**Schedule 13D/G:**
1. `filing.obj()` → `Schedule13D.from_filing(filing)` or `Schedule13G.from_filing(filing)`
2. Calls `filing.xml()`, parses `<edgarSubmission>` root via BeautifulSoup
3. For 13D: extracts `coverPageHeader` → issuer, security, date_of_event, `reportingPersons` → list of `ReportingPerson`, `items1To7` → `Schedule13DItems`, `signatureInfo` → signatures
4. For 13G: same structure but `coverPageHeaderReportingPersonDetails` (no CIK in 13G), `items` (not `items1To7`), `signatureInformation` elements
5. `extract_amendment_number(filing.form)` parses `Amendment No. X` from form name
6. CUSIP is read from `issuerCUSIP` (legacy) or `issuerCusipNumber` (new nested schema)
7. `total_shares` / `total_percent` use `max()` semantics for group filers (co-filers always overlap within one filing)

**ThirteenF:**
1. `filing.obj()` → `ThirteenF(sec_filing)`
2. `__init__` asserts form in `THIRTEENF_FORMS`; parses primary XML immediately if `filing.xml()` returns non-None (2013+ filings)
3. `infotable` (cached_property): calls `_get_infotable_from_attachment()` — tries `document_type=='INFORMATION TABLE' and .xml` first, then `.txt`, then sequence 1 `.txt`; dispatches to `parse_infotable_xml` or `parse_infotable_txt`; applies ×1000 normalization for pre-Q4-2022 filings
4. `holdings` (cached_property): checks `_cache_provider` (optional Redis/external); groups `infotable` by CUSIP; `Type` and `PutCall` become pandas `Categorical` to save memory; sorted by `Value` descending
5. `previous_holding_report()`: uses `Company(cik).get_filings(form=...).latest(40)` then PyArrow sort by `reportDate` descending; falls back to `_related_filings`; result manually cached via `_previous_holding_report_cache`
6. For TXT-only (pre-2013) filings, `primary_form_information` is `None`; `total_value`/`total_holdings` are computed from `infotable` instead

**Form 144:**
1. `filing.obj()` → `Form144.from_filing(filing)`
2. Parses `<edgarSubmission>` XML; builds three DataFrames via list comprehensions of `SecuritiesInformation.from_tag()`, `SecuritiesToBeSold.from_tag()`, `SecuritiesSoldPast3Months.from_tag()`
3. Each DataFrame is wrapped in a `SecuritiesHolder` subclass for aggregation
4. Computed properties (`is_10b5_1_plan`, `cooling_off_compliant`, `holding_period_days`, `anomaly_flags`) execute lazily on property access, no caching

---

### Design patterns

- **Template Method** — `Ownership.parse_xml` is a classmethod returning a dict; `Form3/4/5` each call `super().parse_xml(content)` and pass result to their constructor (`edgar/ownership/ownershipforms.py:2255`). The base class owns all parsing, subclasses add no logic — they exist to give a distinct type for dispatch.
- **DataHolder wrapper** — `DataHolder` base class (and `SecuritiesHolder` in form144) wraps a `pd.DataFrame`, exposing `empty`, `__len__`, `__getitem__` (returns typed dataclass row). Prevents `NoneType` errors and enables Rich rendering via `__rich__`. Used by `NonDerivativeHoldings`, `NonDerivativeTransactions`, `DerivativeHoldings`, `DerivativeTransactions` — `edgar/ownership/ownershipforms.py:258`.
- **Cached property** — `Ownership.market_trades`, `Ownership.derivative_trades`, `ThirteenF.infotable`, `ThirteenF.holdings`, `ThirteenF.infotable_xml`, `ThirteenF.infotable_txt` all use `functools.cached_property` to avoid re-parsing on repeated access.
- **Strategy (format detection)** — `parse_infotable_txt` uses `_is_columnar_format()` to pick between two concrete parsers (`format_columnar.py` vs `format_multiline.py`) without the caller knowing which was used — `edgar/thirteenf/parsers/infotable_txt/__init__.py:32`.
- **Pluggable cache** — `ThirteenF._cache_provider` is a class-level slot for an external cache (Redis, etc). When set, `holdings` checks it first and skips the expensive `infotable` load — `edgar/thirteenf/models.py:198`.
- **Frozen dataclasses** — `DerivativeHolding`, `NonDerivativeHolding`, `DerivativeTransaction`, `NonDerivativeTransaction`, `Owner`, `ReportingPerson`, `IssuerInfo`, `SecurityInfo`, `Signature`, `SecuritiesInformation`, `SecuritiesToBeSold`, `SecuritiesSoldPast3Months`, `NoticeSignature`, `FilingManager`, `OtherManager`, `CoverPage`, `SummaryPage` are all frozen; prevent accidental mutation.
- **Facade (obj() dispatch)** — `filing.obj()` → `edgar.obj(filing)` provides a single entry point for all form types via a flat if/elif chain keyed on `filing.form`, hiding all import paths from users — `edgar/__init__.py:307`.

---

### Cross-domain interactions

**Imports from other `edgar.*` modules:**
- `edgar._party.Address`, `Contact`, `Filer` — used by Form144, Schedule13D/G, ThirteenF for address modelling
- `edgar.entity.Entity` — called in `ReportingOwners.from_reporting_owner_tags` to detect company vs individual for name reversal (`edgar/ownership/ownershipforms.py:1018`)
- `edgar.entity.Company` — used in `ThirteenF._find_previous_holding_report()` and `Form144.company` property
- `edgar.core.IntString`, `get_bool` — utility types used throughout ownership/13D parsing
- `edgar.datatools.convert_to_numeric` — used in `NonDerivativeTable` for Shares/Remaining/Price column conversion
- `edgar.richtools.df_to_rich_table`, `repr_rich` — used in `DataHolder.__rich__` and all `__repr__` methods
- `edgar.xmltools.child_text`, `child_value`, `child_texts`, `find_element` — XML helper functions used in all parsers
- `edgar.display.formatting.reverse_name`, `yes_no`, `format_currency_short` — display formatting utilities
- `edgar.reference.cusip_ticker_mapping` — used by both infotable XML and TXT parsers to add `Ticker` column

**Consumed by other modules:**
- `edgar/__init__.py:obj()` imports and dispatches to all five form types
- `edgar/__init__.py:get_obj_info()` maps form codes to class name strings (used by `filing.obj_type` property)
- Tests and examples reference `filing.obj()` to get typed ownership objects
- `ThirteenF._related_filings` and `_same_day_filings` consume `edgar._filings.Filings` filter/query API

---

### Gotchas & notable behaviors

**Forms 3/4/5:**
- `Ownership.parse_xml` uses BeautifulSoup with the `"xml"` parser (not `"lxml"`) for consistency with namespace handling in these SEC documents.
- `ReportingOwners.from_reporting_owner_tags` makes a live `Entity(int(cik))` call per owner to check `entity.data.is_company` — this involves a network lookup and can fail or slow down parsing for unusual CIKs.
- When `officer_title` contains `'see remarks'` (case-insensitive), the title is replaced with the filing's `remarks` field — `edgar/ownership/ownershipforms.py:1037`.
- `no_securities = True` when `<noSecuritiesOwned>1</noSecuritiesOwned>` is present — Form 3 can be filed with no holdings.
- `footnote_id` values can be `AttributeValueList` (BeautifulSoup quirk) — all footnote extraction code defensively handles this by taking `[0]` of lists — `edgar/ownership/ownershipforms.py:331`.
- `TransactionSummary.has_10b5_1_plan` returns `None` (not `False`) when no footnotes are present at all, `False` when footnotes exist but don't mention the plan — `edgar/ownership/ownershipforms.py:1422`.
- `detect_10b5_1_plan` checks for `"10b5-1"`, `"10b-5-1"`, `"rule 10b5"`, `"rule 10b-5"`, `"10b5 plan"`, `"10b-5 plan"` — `edgar/ownership/core.py:224`.
- Placeholder footnote values like `[F1]` embedded in share/price strings are stripped by `safe_numeric` before conversion — `edgar/ownership/core.py:69`.
- Form 3 `__rich__` and HTML rendering show `holdings` (not transactions); Forms 4/5 show `transactions` — `edgar/ownership/ownershipforms.py:754`.
- `html_render.py` uses Jinja2 with templates from `edgar/ownership/templates/ownership_form.html`; form-type-specific columns differ (Form 3 has 4 columns for Table I; Forms 4/5 have 11 columns).

**Schedule 13D/G:**
- `total_shares` / `total_percent` use `max()` not `sum()` because group filers within a single filing always report overlapping (not additive) beneficial ownership — `edgar/beneficial_ownership/schedule13.py:389`.
- The 13D and 13G XML schemas have different element names for the same conceptual fields: `issuerCUSIP` (13D legacy) vs `issuerCusip` (13G legacy); both also have a newer `issuerCusipNumber` — `schedule13.py:192` (13D), `:616` (13G).
- 13G `coverPageHeaderReportingPersonDetails` does not contain CIK — `cik` is always `''` for 13G reporting persons.
- The `member_of_group` element is named `memberOfGroup` in 13D vs `memberGroup` in 13G — `schedule13.py:229` vs `:667`.
- `extract_amendment_number` handles "Amendment No. 9", "/A #9" but returns `None` (not `1`) for bare `/A` suffix.
- `get_original_filing` uses `filing.related_filings(filing_date=f':{schedule.filing_date}', amendments=False)` to find the non-amendment original — `edgar/beneficial_ownership/amendments.py:173`.
- `OwnershipComparison.shares_change` uses `sum` (correct for comparing two separate filings) while `Schedule13D.total_shares` uses `max` (correct within one filing) — this asymmetry is intentional.

**ThirteenF:**
- The schema changed in Q4 2022: before `datetime(2022, 9, 30)`, `<value>` was in thousands; after, it is in dollars. The library auto-multiplies by 1000 for old filings — `edgar/thirteenf/models.py:30`.
- Multi-manager filings (State Street, Bank of America, etc.) have multiple rows per CUSIP in `infotable` (one per manager-CUSIP pair). `.holdings` aggregates these to one row per CUSIP; `.infotable` is the disaggregated view.
- `other_managers` is now parsed from `<summaryPage><otherManagers2Info>` not `<coverPage>` — the `CoverPage.other_managers` field is explicitly deprecated to `[]` in the parser — `edgar/thirteenf/parsers/primary_xml.py:127`.
- `primary_form_information` is `None` for pre-2013 TXT-only filings; all properties that depend on it fall back to `infotable`-based computation.
- The infotable attachment discovery cascade: (1) XML with `.xml` extension and `document_type='INFORMATION TABLE'`; (2) TXT with `.txt` extension matching descriptions `FORM 13F` or `INFORMATION TABLE`; (3) sequence-number-1 `.txt` attachment.
- `use_latest_period_of_report=True` is intended for cases where a manager files multiple 13F filings on the same day for different periods — the constructor will pick the last one by same-day filter.
- `PutCall` categorical values are `''`, `'PUT'`, `'CALL'` — the empty string (not `None`) is the default for non-option positions.

**Form 144:**
- Placeholder `01/01/1933` dates appear throughout the SEC form schema as defaults — `_valid_plan_dates()` filters these out before any plan-related calculations — `edgar/form144.py:619`.
- `is_10b5_1_plan` is `True` only when valid (non-1933) `planAdoptionDates` exist in `<noticeSignature>` — this is different from the footnote-based detection in Form 4.
- `percent_of_holdings` uses `units_outstanding` from the first security row only — not aggregated — `edgar/form144.py:357`.
- Both legacy (raw DataFrame properties `securities_information`, `securities_to_be_sold`, `securities_sold_past_3_months`) and new API (holder objects `securities_info`, `securities_selling`, `recent_sales`) coexist for backward compatibility — `edgar/form144.py:479`.
- `concat_securities_information` and `concat_securities_to_be_sold` are module-level helpers for aggregating across a list of Form 144 filings — `edgar/form144.py:1225`.
