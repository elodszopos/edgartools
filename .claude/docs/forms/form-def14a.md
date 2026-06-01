# Form DEF 14A — Proxy Statement

**SEC form codes**: DEF 14A, DEF 14A/A, DEFA14A, DEFA14A/A, DEFM14A, DEFM14A/A, DEFR14A, DEFR14A/A, DEFC14A, DEFC14A/A, DEFN14A, DEFN14A/A, DFAN14A, DFAN14A/A, DFRN14A, DFRN14A/A, PRE 14A, PRE 14A/A, PREC14A, PREC14A/A, PREM14A, PREM14A/A, PREN14A, PREN14A/A, PRER14A, PRER14A/A, PRRN14A, PRRN14A/A, PX14A6G, PX14A6N (30 total)
**Python class**: `ProxyStatement` (no base class — standalone)
**Access**: `filing.obj()` → `ProxyStatement`; or `ProxyStatement.from_filing(filing)`
**Base fields**: See `core-filing-access.md` — all `Filing` fields available via `.filing`
**Source**: `edgar/proxy/core.py`, `edgar/proxy/models.py`, `edgar/proxy/html_extractor.py`, `edgar/proxy/season.py`, `edgar/proxy/contest.py`

---

## Complete Field Reference

### ProxyStatement-Specific Fields

#### Metadata Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `filing` | `Filing` | no | Source Filing object |
| `form` | `str` | no | Form type (DEF 14A, DEFA14A, etc.) |
| `filing_date` | `str` | no | Date filed with SEC (YYYY-MM-DD) |
| `cik` | `str` | no | Central Index Key as string |
| `accession_number` | `str` | no | SEC accession number |
| `company_name` | `Optional[str]` | no | Legal name from XBRL `dei:EntityRegistrantName`; None if no XBRL |
| `fiscal_year_end` | `Optional[str]` | no | From `dei:DocumentPeriodEndDate`; None if no XBRL |
| `has_xbrl` | `bool` | cached | True if ECD XBRL data present; SRCs, EGCs, SPACs, funds return False |

#### XBRL-Backed Scalar Properties

All return None when `has_xbrl` is False.

| Field | Type | Lazy | XBRL Concept | Description |
|-------|------|------|--------------|-------------|
| `peo_name` | `Optional[str]` | no | `ecd:PeoName` | Principal Executive Officer name (most recent) |
| `peo_total_comp` | `Optional[Decimal]` | cached | `ecd:PeoTotalCompAmt` | PEO SCT total compensation, most recent year |
| `peo_actually_paid_comp` | `Optional[Decimal]` | cached | `ecd:PeoActuallyPaidCompAmt` | PEO Compensation Actually Paid, most recent year |
| `neo_avg_total_comp` | `Optional[Decimal]` | cached | `ecd:NonPeoNeoAvgTotalCompAmt` | Non-PEO NEO average total comp, most recent year |
| `neo_avg_actually_paid_comp` | `Optional[Decimal]` | cached | `ecd:NonPeoNeoAvgCompActuallyPaidAmt` | Non-PEO NEO average CAP, most recent year |
| `total_shareholder_return` | `Optional[Decimal]` | cached | `ecd:TotalShareholderRtnAmt` | Company TSR, most recent year |
| `peer_group_tsr` | `Optional[Decimal]` | cached | `ecd:PeerGroupTotalShareholderRtnAmt` | Peer group TSR, most recent year |
| `net_income` | `Optional[Decimal]` | cached | `us-gaap:NetIncomeLoss` | Net income, most recent year |
| `company_selected_measure` | `Optional[str]` | no | `ecd:CoSelectedMeasureName` | Company KPI name |
| `company_selected_measure_value` | `Optional[Decimal]` | cached | `ecd:CoSelectedMeasureAmt` | Company KPI value, most recent year |
| `performance_measures` | `List[str]` | cached | `ecd:MeasureName` | All performance measure names used |

#### Governance / Award Timing Properties (XBRL-backed)

All return None when `has_xbrl` is False.

| Field | Type | Lazy | XBRL Concept | Description |
|-------|------|------|--------------|-------------|
| `insider_trading_policy_adopted` | `Optional[bool]` | cached | `ecd:InsiderTrdPoliciesProcAdoptedFlag` | Whether insider trading policy adopted |
| `award_timing_mnpi_considered` | `Optional[bool]` | cached | `ecd:AwardTmgMnpiCnsdrdFlag` | Award timing decisions considered MNPI |
| `award_dates_predetermined` | `Optional[bool]` | cached | `ecd:AwardTmgPredtrmndFlag` | Whether award grant dates were predetermined |
| `mnpi_disclosure_timed_for_comp_value` | `Optional[bool]` | cached | `ecd:MnpiDiscTimedForCompValFlag` | MNPI disclosure timed to affect comp value |

#### Multi-Year DataFrame Properties (XBRL-backed)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `executive_compensation` | `pd.DataFrame` | cached | 5-year PEO/NEO comp time series; empty if no XBRL |
| `pay_vs_performance` | `pd.DataFrame` | cached | 5-year TSR/CAP metrics; empty if no XBRL |
| `awards_close_to_mnpi` | `pd.DataFrame` | cached | Awards granted within 4 business days of MNPI disclosure (SEC Rule 402(x), since 2023) |

#### Dimensional XBRL Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `has_individual_executive_data` | `bool` | cached | True if `dim_ecd_IndividualAxis` exists in facts |
| `named_executives` | `List[NamedExecutive]` | cached | Per-executive data; only when dimensionally tagged (~60% of filers) |

#### HTML-Extracted Properties

All use `lxml` DOM on `_html_tree` (shared cached parse, ~100-200ms first access).

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `voting_proposals` | `List[VotingProposal]` | cached | Voting proposals via regex on filing text; empty list on failure |
| `ceo_pay_ratio` | `Optional[CEOPayRatio]` | cached | CEO pay ratio via regex on filing text; None if section not found |
| `summary_compensation_table` | `pd.DataFrame` | cached | Per-NEO SCT via lxml table extraction; empty DataFrame on failure |
| `beneficial_ownership` | `pd.DataFrame` | cached | 5%+ holders and insiders via lxml; empty DataFrame on failure |
| `director_compensation_table` | `pd.DataFrame` | cached | Non-employee director comp via lxml; empty DataFrame on failure |
| `audit_fees` | `Optional[AuditFees]` | cached | Audit fee breakdown via lxml; None if section not found |

#### Season / Navigation

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `season` | `Optional[ProxySeason]` | cached | Latest ProxySeason for this company; triggers network; None if entity unresolvable |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing(filing)` | `Filing` | `Optional[ProxyStatement]` | Classmethod factory; calls `cls(filing)` — form assertion is in `__init__`, not here |
| `to_context(detail)` | `detail: str = 'standard'` | `str` | AI-optimized string; detail='minimal'/'standard'/'full' |

---

## DataFrame Schemas

### `executive_compensation` columns

| Column | Type | Description |
|--------|------|-------------|
| `fiscal_year_end` | date/str | End of fiscal year |
| `peo_total_comp` | Decimal/None | PEO total from SCT |
| `peo_actually_paid_comp` | Decimal/None | PEO compensation actually paid |
| `neo_avg_total_comp` | Decimal/None | Non-PEO NEO average total |
| `neo_avg_actually_paid_comp` | Decimal/None | Non-PEO NEO average CAP |

### `pay_vs_performance` columns

| Column | Type | Description |
|--------|------|-------------|
| `fiscal_year_end` | date/str | End of fiscal year |
| `peo_actually_paid_comp` | Decimal/None | CEO compensation actually paid |
| `neo_avg_actually_paid_comp` | Decimal/None | NEO average CAP |
| `total_shareholder_return` | Decimal/None | Company TSR |
| `peer_group_tsr` | Decimal/None | Peer group TSR |
| `net_income` | Decimal/None | Net income |
| `company_selected_measure_value` | Decimal/None | Company-selected KPI value |

### `awards_close_to_mnpi` columns

| Column | Type | Description |
|--------|------|-------------|
| `grant_date` | str | Date the award was granted |
| `executive` | str/None | Executive identifier (cleaned, Member suffix stripped) |
| `award_type` | str/None | Award type (cleaned) |
| `exercise_price` | Decimal/None | Exercise price |
| `grant_date_fair_value` | Decimal/None | Fair value on grant date |
| `underlying_securities` | Decimal/None | Number of underlying securities |
| `market_price_change_pct` | Decimal/None | % change in underlying security price |

### `summary_compensation_table` columns

| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Executive name |
| `title` | str | Executive title (abbreviated) |
| `year` | int | Fiscal year |
| `salary` | int/None | Base salary |
| `bonus` | int/None | Discretionary bonus |
| `stock_awards` | int/None | Stock award fair value |
| `option_awards` | int/None | Option award fair value |
| `non_equity_incentive` | int/None | Non-equity incentive plan compensation |
| `pension_change` | int/None | Change in pension value and NQDC earnings |
| `other_compensation` | int/None | All other compensation |
| `total` | int/None | Total compensation |

### `beneficial_ownership` columns

| Column | Type | Description |
|--------|------|-------------|
| `holder_name` | str | Name of holder |
| `holder_type` | str | '5pct_holder', 'director_officer', or 'group' |
| `shares` | int/None | Shares beneficially owned |
| `percent_of_class` | float/None | Percent of class; 0.5 sentinel = "less than 1%" |

### `director_compensation_table` columns

| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Director name |
| `fees_earned` | int/None | Fees earned or paid in cash |
| `stock_awards` | int/None | Stock award fair value |
| `option_awards` | int/None | Option award fair value |
| `non_equity_incentive` | int/None | Non-equity incentive plan compensation |
| `pension_change` | int/None | Change in pension value and NQDC earnings |
| `other_compensation` | int/None | All other compensation |
| `total` | int/None | Total compensation |

---

## Nested Objects

### `NamedExecutive` (frozen dataclass — `models.py`)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Executive name |
| `member_id` | `Optional[str]` | XBRL dimensional member ID (e.g., `ecd_IndividualAxis` value) |
| `role` | `Optional[str]` | Role string from XBRL (PEO, NEO, etc.) |
| `total_comp` | `Optional[Decimal]` | Always `None` — not populated by `named_executives` property code path |
| `actually_paid_comp` | `Optional[Decimal]` | Always `None` — not populated by `named_executives` property code path |
| `fiscal_year_end` | `Optional[str]` | Fiscal year end date string |

### `VotingProposal` (frozen dataclass — `html_extractor.py`)

| Field | Type | Description |
|-------|------|-------------|
| `number` | `int` | Proposal number (1-30) |
| `description` | `str` | Cleaned proposal description (max ~120 chars) |
| `board_recommendation` | `Optional[str]` | 'FOR', 'AGAINST', 'ABSTAIN', or None |
| `proposal_type` | `ProposalType` | Classified type (see below) |

`ProposalType` values: `director_election`, `say_on_pay`, `say_on_pay_frequency`, `auditor_ratification`, `equity_plan`, `shareholder_proposal`, `company_proposal`

### `CEOPayRatio` (frozen dataclass — `html_extractor.py`)

| Field | Type | Description |
|-------|------|-------------|
| `ceo_compensation` | `Optional[int]` | CEO annual total compensation (dollars) |
| `median_employee_compensation` | `Optional[int]` | Median employee annual total comp (dollars) |
| `ratio` | `Optional[int]` | Pay ratio as integer (e.g., 533 means 533:1) |

### `AuditFees` (frozen dataclass — `html_extractor.py`)

| Field | Type | Description |
|-------|------|-------------|
| `auditor_name` | `str` | Auditor firm name (may be empty string) |
| `current_year` | `int` | Current year (0 if not detected) |
| `prior_year` | `int` | Prior year (0 if not detected) |
| `audit_fees_current` | `Optional[int]` | Audit fees, current year |
| `audit_fees_prior` | `Optional[int]` | Audit fees, prior year |
| `audit_related_current` | `Optional[int]` | Audit-related fees, current year |
| `audit_related_prior` | `Optional[int]` | Audit-related fees, prior year |
| `tax_fees_current` | `Optional[int]` | Tax fees, current year |
| `tax_fees_prior` | `Optional[int]` | Tax fees, prior year |
| `other_fees_current` | `Optional[int]` | Other fees, current year |
| `other_fees_prior` | `Optional[int]` | Other fees, prior year |
| `total_current` | `Optional[int]` | Total fees, current year |
| `total_prior` | `Optional[int]` | Total fees, prior year |

### `SeasonFiling` (frozen dataclass — `models.py`)

Carries labeled metadata for each filing in a season or contest.

| Field | Type | Description |
|-------|------|-------------|
| `filing` | `Filing` | The underlying Filing object |
| `form` | `str` | Form type string |
| `filing_date` | `str` | Filing date (YYYY-MM-DD) |
| `accession_no` | `str` | SEC accession number |
| `file_number` | `Optional[str]` | SEC file number |
| `party_type` | `str` | 'management', 'dissident', 'third_party', or 'unknown' |
| `party_name` | `Optional[str]` | Best-effort filer name from SGML header |
| `filer_cik` | `Optional[str]` | Filer CIK from SGML header |
| `tier` | `int` | 1=full proxy, 2=contested definitive, 3=preliminary, 4=supplemental, 5=exempt |

---

## Nested Class: ProxySeason

**Source**: `edgar/proxy/season.py`
**Access**: `proxy_statement.season` or `ProxySeason.for_company(company, index=0)`

Groups all proxy filings around one annual meeting, anchored by management's definitive proxy.

### ProxySeason Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `anchor` | `Filing` | no | Management definitive proxy (DEF 14A or DEFC14A) |
| `anchor_form` | `str` | no | Form type of anchor |
| `filing_date` | `str` | no | Filing date of anchor (YYYY-MM-DD) |
| `company_name` | `str` | no | Company name |
| `cik` | `str` | no | Company CIK as string |
| `num_filings` | `int` | no | Total filings in this season |
| `proxy` | `ProxyStatement` | cached | ProxyStatement from anchor filing |
| `related_filings` | `List[Filing]` | no | All proxy filings in season window |
| `preliminary_filings` | `List[SeasonFiling]` | cached | Tier 3: PRE 14A, PREC14A, etc. |
| `supplemental_filings` | `List[SeasonFiling]` | cached | Tier 4: DEFA14A, DFAN14A, DFRN14A |
| `exempt_solicitations` | `List[SeasonFiling]` | cached | Tier 5: PX14A6G, PX14A6N |
| `is_contested` | `bool` | cached | True if any CONTEST_INDICATOR_FORMS in season |
| `contest` | `Optional[ProxyContest]` | cached | ProxyContest if contested, else None |

### ProxySeason Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `for_company(company, index)` | `company: Entity, index: int = 0` | `Optional[ProxySeason]` | Classmethod; 0=latest, 1=previous, etc.; triggers network |
| `to_context(detail)` | `detail: str = 'standard'` | `str` | AI-optimized string; detail='minimal'/'standard'/'full' |

---

## Nested Class: ProxyContest

**Source**: `edgar/proxy/contest.py`
**Access**: `proxy_season.contest` (built lazily when `is_contested` is True)

Analyzes a contested proxy: parties, timeline, settlement status.

### ProxyContest Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `company_name` | `str` | no | Target company name |
| `is_contested` | `bool` | no | Always True (ProxySeason.contest is None when not contested) |
| `num_filings` | `int` | no | Total contest-related filings |
| `dissidents` | `List[str]` | cached (network) | Unique dissident party names, ordered by first appearance |
| `parties` | `Dict[str, str]` | cached (network) | All parties: {name: party_type} |
| `is_settled` | `bool` | cached (network) | True if management never filed DEFC14A (settled heuristic) |
| `timeline` | `pd.DataFrame` | cached (network) | Chronological table of all contest filings |
| `management_filings` | `List[SeasonFiling]` | cached (network) | Filings where party_type == 'management' |
| `dissident_filings` | `List[SeasonFiling]` | cached (network) | Filings where party_type == 'dissident' |
| `third_party_filings` | `List[SeasonFiling]` | cached (network) | Filings where party_type == 'third_party' |

### `timeline` DataFrame columns

| Column | Type | Description |
|--------|------|-------------|
| `date` | str | Filing date (YYYY-MM-DD) |
| `form` | str | Form type |
| `party` | str | Party name |
| `party_type` | str | 'management', 'dissident', 'third_party', or 'unknown' |
| `tier` | int | Tier classification (1-5) |
| `accession_no` | str | SEC accession number |

### ProxyContest Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `to_context(detail)` | `detail: str = 'standard'` | `str` | AI-optimized string; detail='minimal'/'standard'/'full' |

---

## Nested Class: ProxyContests

**Source**: `edgar/proxy/contests.py`
**Access**: `proxy_contests(year=None, quarter=None)`

Market-wide collection of proxy contests. Supports `len()`, `[]`, slicing, `.head()`.

### ProxyContests Properties

| Field | Type | Description |
|-------|------|-------------|
| `companies` | `ProxyContests` | Filtered to target companies only (have tickers or filed management-side forms) |
| `activists` | `ProxyContests` | Filtered to activist funds only (filed dissident-side forms) |
| `empty` | `bool` | True if no entries |

### ProxyContests Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `proxy_contests(year, quarter)` | `year: Optional[int] = None, quarter: Optional[int] = None` | `ProxyContests` | Top-level function; scans EDGAR contest forms, groups by filer CIK; year defaults to current year |
| `head(n)` | `n: int = 10` | `ProxyContests` | First n entries |
| `__getitem__(int)` | `int` | `ProxyContest` | Returns ProxyContest at index |
| `__getitem__(slice)` | `slice` | `ProxyContests` | Returns sliced ProxyContests |
| `__iter__` | — | iterator | Yields ProxyContest objects |
| `__len__` | — | `int` | Count of entries |

---

## Form Code Classification

### `classify_proxy_tier(form)` — `models.py`

Returns `int` 1-5 tier for a proxy form code (strips `/A` first).

| Tier | Forms | Description |
|------|-------|-------------|
| 1 | DEF 14A, DEFM14A, DEFR14A | Full definitive proxy |
| 2 | DEFC14A, DEFN14A | Contested definitive |
| 3 | PRE 14A, PREC14A, PREM14A, PREN14A, PRER14A, PRRN14A | Preliminary |
| 4 | DEFA14A, DFAN14A, DFRN14A | Supplemental campaign materials |
| 5 | PX14A6G, PX14A6N | Third-party exempt solicitations |

### Form Sets (from `models.py`)

| Constant | Forms | Purpose |
|----------|-------|---------|
| `PROXY_FORMS` | All 30 form codes | Routes to ProxyStatement via `filing.obj()` |
| `ANCHOR_FORMS` | DEF 14A, DEFC14A | Season anchor detection |
| `CONTEST_INDICATOR_FORMS` | DEFC14A, DEFC14C, PREC14A, PREC14C, DFAN14A, DEFN14A, PREN14A, DFRN14A, PRRN14A | Signals a proxy contest |
| `DISSIDENT_ONLY_FORMS` | DFAN14A, DEFN14A, PREN14A, DFRN14A, PRRN14A | Always dissident (N-suffix) |
| `SUPPLEMENTAL_FORMS` | DEFA14A, DFAN14A, DFRN14A | No structured proxy disclosures |
| `PRELIMINARY_FORMS` | PRE 14A, PREC14A, PREM14A, PREN14A, PRER14A, PRRN14A | Draft; subject to SEC revision |
| `EXEMPT_SOLICITATION_FORMS` | PX14A6G, PX14A6N | ISS, Glass Lewis, activist orgs |

---

## Error Paths

| Condition | Behavior |
|-----------|----------|
| `has_xbrl` is False | All XBRL properties return None; DataFrames return empty with correct columns |
| No XBRL but `company_name` accessed | Returns None (reads XBRL) |
| `named_executives` on non-dimensional filer (~40%) | Returns empty list |
| `has_individual_executive_data` False | `named_executives` always returns [] |
| `voting_proposals`: text extraction fails | Returns empty list |
| `ceo_pay_ratio`: section not found | Returns None; SRCs and EGCs are exempt |
| `summary_compensation_table`: no matching table | Returns empty DataFrame |
| `beneficial_ownership`: no matching table | Returns empty DataFrame |
| `director_compensation_table`: no matching table | Returns empty DataFrame |
| `audit_fees`: section not found | Returns None |
| `awards_close_to_mnpi`: no XBRL or concept absent | Returns empty DataFrame with correct columns |
| `season`: entity resolution fails | Returns None (not raise) |
| `ProxySeason.for_company(index=N)`: N >= anchors count | Returns None |
| `ProxyContest._labeled_filings`: SGML header parse fails | Party labeled 'unknown'; included conservatively |
| `proxy_contests()`: no contest forms in period | Returns empty ProxyContests |
| Form not in PROXY_FORMS passed to constructor | Raises `AssertionError` |

---

## Access Patterns

- Quickstart: `filing.obj()` where `filing.form in PROXY_FORMS`
- From company: `Company("AAPL").get_filings(form="DEF 14A").latest().obj()`
- Season: `ProxySeason.for_company(company)` or `proxy_stmt.season`
- Historical season: `ProxySeason.for_company(company, index=1)` (previous year)
- Market contests: `from edgar.proxy.contests import proxy_contests; proxy_contests(year=2024).companies`
- Individual executive drill-down: check `proxy.has_individual_executive_data` before `proxy.named_executives`
- XBRL guard pattern: check `proxy.has_xbrl` before accessing any XBRL-backed property in a loop
- HTML drill-down: `proxy.audit_fees.auditor_name`, `proxy.ceo_pay_ratio.ratio`
- Contest timeline: `proxy.season.contest.timeline` (triggers two network hops)
