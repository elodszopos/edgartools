## Offerings & Registration

### Overview

The `edgar/offerings/` package and `edgar/effect.py` handle all securities offering and registration form types filed on EDGAR. It provides structured Python data objects for Regulation CF crowdfunding (FormC), private placement notices (FormD), full registration statements (RegistrationS1 for S-1/F-1), shelf registrations (RegistrationS3 for S-3/F-3/ASR), draft registration statements (DraftRegistrationStatement), 424B* prospectuses (Prospectus424B with eight variants), the draft registration shortcut (DRS), and effectiveness notices (Effect). These are dispatched through the universal `filing.obj()` entry point defined in `edgar/__init__.py`. All public objects implement `to_context(detail)` for LLM consumption, `__rich__()` for terminal rendering, and `__repr__`.

---

### Public API surface

| Symbol | file:line | Purpose |
|---|---|---|
| `FormC` | `edgar/offerings/formc.py:528` | Crowdfunding offering (Reg CF) parsed from XML |
| `FundingPortal` | `edgar/offerings/formc.py:49` | Pydantic model: intermediary for a Reg CF offering |
| `IssuerCompany` | `edgar/offerings/formc.py:434` | Issuer wrapper with `get_offerings()` / `as_company()` |
| `Signer` | `edgar/offerings/formc.py:355` | Pydantic: named signer + titles |
| `FormD` | `edgar/offerings/formd.py:307` | Private placement offering parsed from XML |
| `RegistrationS1` | `edgar/offerings/registration_s1.py:105` | S-1/F-1 registration data object |
| `S1OfferingType` | `edgar/offerings/registration_s1.py:47` | Enum: ipo/spac/resale/debt/follow_on/unknown |
| `S1CoverPage` | `edgar/offerings/registration_s1.py:73` | Pydantic: S-1 cover page extracted fields |
| `RegistrationS3` | `edgar/offerings/registration_s3.py:261` | S-3/F-3/ASR shelf registration data object |
| `S3OfferingType` | `edgar/offerings/registration_s3.py:42` | Enum: universal_shelf/resale/debt/auto_shelf/unknown |
| `S3CoverPage` | `edgar/offerings/registration_s3.py:65` | Pydantic: S-3 cover page extracted fields |
| `Prospectus424B` | `edgar/offerings/prospectus.py:1163` | 424B1-B8 prospectus data object |
| `OfferingType` | `edgar/offerings/prospectus.py:41` | Enum: firm_commitment/atm/best_efforts/pipe_resale/… |
| `CoverPageData` | `edgar/offerings/prospectus.py:99` | Pydantic: 424B cover page fields |
| `Deal` | `edgar/offerings/prospectus.py:784` | Computed deal summary: price/shares/proceeds/fees/dilution |
| `ShelfLifecycle` | `edgar/offerings/prospectus.py:394` | Shelf position, expiry, takedown cadence analytics |
| `SellingStockholdersData` | `edgar/offerings/prospectus.py:228` | Selling stockholder table with `.to_dataframe()` |
| `SellingStockholderEntry` | `edgar/offerings/prospectus.py:187` | Single row: name, shares before/after, pct, warrants |
| `UnderwritingInfo` | `edgar/offerings/prospectus.py:264` | Underwriter syndicate + fee type |
| `StructuredNoteTerms` | `edgar/offerings/prospectus.py:280` | Structured note key terms (CUSIP, maturity, underlying) |
| `DilutionData` | `edgar/offerings/prospectus.py:300` | Per-share dilution table |
| `CapitalizationData` | `edgar/offerings/prospectus.py:311` | Actual vs. as-adjusted capitalization table |
| `RegistrationFeeTable` | `edgar/offerings/prospectus.py:357` | Shelf capacity: total offering amount + securities |
| `FeeTableSecurity` | `edgar/offerings/prospectus.py:345` | Single security line from Exhibit 107 |
| `FilingFeesData` | `edgar/offerings/prospectus.py:330` | 424B XBRL fee exhibit data |
| `DraftRegistrationStatement` | `edgar/offerings/drs.py:98` | DRS/DRS-A wrapper with underlying form detection |
| `Offering` | `edgar/offerings/campaign.py:92` | Complete Reg CF offering lifecycle tracker |
| `Campaign` | `edgar/offerings/campaign.py:695` | Alias for `Offering` (backward compatibility) |
| `Effect` | `edgar/effect.py:41` | EFFECT notice: effectiveness declaration |
| `EffectiveData` | `edgar/effect.py:20` | Data container: date, file number, source accession |
| `group_offerings_by_file_number` | `edgar/offerings/__init__.py:17` | Utility: group Form C filings by issuer file number (020-XXXXX) |

---

### Key classes

#### FormC (`edgar/offerings/formc.py:528`)
Top-level parsed representation of any Form C variant. Contains four sub-objects: `FilerInformation`, `IssuerInformation`, `OfferingInformation`, `AnnualReportDisclosure`, and `SignatureInfo`.

- `from_filing(filing) -> FormC` — primary entry point; fetches `filing.xml()`, parses via `from_xml` — `edgar/offerings/formc.py:930`
- `from_xml(offering_xml, form) -> FormC` — XML parser; uses BeautifulSoup XML mode — `edgar/offerings/formc.py:938`
- `get_offering() -> Offering` — returns complete lifecycle `Offering` object — `edgar/offerings/formc.py:671`
- `issuer -> IssuerCompany` — cached property; wraps filer CIK + name — `edgar/offerings/formc.py:636`
- `get_issuer_company() -> IssuerCompany` — deprecated alias for `issuer` — `edgar/offerings/formc.py:659`
- `to_context(detail, filing_date) -> str` — LLM-optimized; detail levels: minimal/standard/full — `edgar/offerings/formc.py:693`
- `days_to_deadline -> Optional[int]` — days until offering deadline; negative if expired — `edgar/offerings/formc.py:606`
- `is_expired -> bool` — True if deadline passed — `edgar/offerings/formc.py:617`
- `campaign_status -> str` — human-readable status derived from form type — `edgar/offerings/formc.py:622`
- `portal_file_number -> Optional[str]` — portal's 007-XXXXX file number — `edgar/offerings/formc.py:564`
- `description -> str` — full form name string (e.g. "Form C/A - Offering Amendment") — `edgar/offerings/formc.py:546`
- `docs -> Docs` — in-repl documentation access — `edgar/offerings/formc.py:899`
- `parse_date(date_str) -> date` — parses MM-DD-YYYY format — `edgar/offerings/formc.py:916`

**Sub-models:**

- `OfferingInformation` (`edgar/offerings/formc.py:73`): all offering terms; computed properties `security_description`, `price_per_security`, `number_of_securities`, `percent_to_maximum`, `offering_deadline`
- `AnnualReportDisclosure` (`edgar/offerings/formc.py:160`): two-year financial snapshot; computed properties `total_debt_most_recent`, `debt_to_asset_ratio`, `revenue_growth_yoy`, `is_pre_revenue`, `burn_rate_change`, `asset_growth_yoy`; convenience aliases (`total_assets`, `revenues`, `net_income`, etc.); `is_offered_in_all_states`
- `FilerInformation` (`edgar/offerings/formc.py:32`): frozen Pydantic; `company -> Company` (LRU cached)
- `IssuerInformation` (`edgar/offerings/formc.py:58`): Pydantic; holds `FundingPortal`, `Address`
- `FundingPortal` (`edgar/offerings/formc.py:49`): name, cik, crd, file_number
- `SignatureInfo` (`edgar/offerings/formc.py:360`): contains `IssuerSignature`, `List[PersonSignature]`; `signers -> List[Signer]` deduplicates by name
- `IssuerCompany` (`edgar/offerings/formc.py:434`): `as_company() -> Company`; `get_offerings() -> List[Offering]`; `latest_offering() -> Optional[Offering]`

---

#### FormD (`edgar/offerings/formd.py:307`)
Top-level parsed Form D private placement notice.

- `from_xml(offering_xml) -> FormD` — single entry point; no `from_filing` (dispatched via `filing.xml()` in `__init__.py`) — `edgar/offerings/formd.py:331`
- `to_context(detail) -> str` — minimal/standard/full — `edgar/offerings/formd.py:384`
- `is_new -> bool` — True if new filing (not amendment) — `edgar/offerings/formd.py:327`
- Fields: `submission_type`, `is_live`, `primary_issuer: Issuer`, `related_persons: List[Person]`, `offering_data: OfferingData`, `signature_block: SignatureBlock`

**Sub-models:**

- `OfferingData` (`edgar/offerings/formd.py:156`): `from_xml(el) -> OfferingData`; holds `IndustryGroup`, `revenue_range`, `federal_exemptions`, `OfferingSalesAmounts`, `Investors`, `SalesCommissionFindersFees`, `UseOfProceeds`, `List[SalesCompensationRecipient]`
- `IndustryGroup` (`edgar/offerings/formd.py:54`): `industry_group_type` + optional `InvestmentFundInfo`
- `SalesCompensationRecipient` (`edgar/offerings/formd.py:77`): `from_xml(tag) -> SalesCompensationRecipient`; name, crd, address, states_of_solicitation; cleans "None" strings from XML
- `OfferingSalesAmounts`, `Investors`, `SalesCommissionFindersFees`, `UseOfProceeds`: plain Pydantic models, amounts as `object` (strings from XML)

---

#### RegistrationS1 (`edgar/offerings/registration_s1.py:105`)
S-1/F-1 full registration statement. Eagerly parses cover and fee table; lazily computes tables.

- `from_filing(filing) -> RegistrationS1` — calls `_fee_table`, `_s1_cover`, `_s1_classifier` helpers once; reuses single `filing.html()` call — `edgar/offerings/registration_s1.py:141`
- `cover_page -> S1CoverPage` — `edgar/offerings/registration_s1.py:183`
- `offering_type -> S1OfferingType` — enum value — `edgar/offerings/registration_s1.py:187`
- `fee_table` — `RegistrationFeeTable | None` — `edgar/offerings/registration_s1.py:231`
- `total_offering -> Optional[float]` — total registered amount — `edgar/offerings/registration_s1.py:236`
- `net_fee -> Optional[float]` — net registration fee — `edgar/offerings/registration_s1.py:241`
- `securities -> List[FeeTableSecurity]` — per-security breakdown — `edgar/offerings/registration_s1.py:247`
- `selling_stockholders -> Optional[SellingStockholdersData]` — cached_property; uses `_424b_tables` — `edgar/offerings/registration_s1.py:280`
- `dilution -> Optional[DilutionData]` — cached_property — `edgar/offerings/registration_s1.py:292`
- `capitalization -> Optional[CapitalizationData]` — cached_property — `edgar/offerings/registration_s1.py:305`
- `underwriting -> Optional[UnderwritingInfo]` — cached_property — `edgar/offerings/registration_s1.py:316`
- `takedowns -> Optional[Filings]` — cached_property; queries 424B filings by registration file number — `edgar/offerings/registration_s1.py:342`
- `related_filings -> Optional[Filings]` — all filings under same registration number — `edgar/offerings/registration_s1.py:370`
- `effective_date -> Optional[str]` — finds EFFECT filing in related_filings — `edgar/offerings/registration_s1.py:389`
- `is_effective -> bool` — `edgar/offerings/registration_s1.py:402`
- `is_amendment -> bool` — checks '/A' in form — `edgar/offerings/registration_s1.py:208`

**S1CoverPage** fields: `company_name`, `registration_number` (333-XXXXXX), `state_of_incorporation`, `sic_code`, `ein`, filer category booleans (`is_large_accelerated_filer`, `is_accelerated_filer`, `is_non_accelerated_filer`, `is_smaller_reporting_company`, `is_emerging_growth_company`), rule booleans (`is_rule_415`, `is_rule_462b`, `is_rule_462e`), `security_description`, `confidence` (low/medium/high).

---

#### RegistrationS3 (`edgar/offerings/registration_s3.py:261`)
S-3/F-3/S-3ASR shelf registration. Architecturally similar to S1 but shorter (50-200K chars) because financials are incorporated by reference. Cover page extraction and offering classifier are defined inline (not in separate helper files).

- `from_filing(filing) -> RegistrationS3` — fee table first (used by classifier), then cover, then offering type; single `filing.html()` call — `edgar/offerings/registration_s3.py:293`
- `cover_page -> S3CoverPage` — `edgar/offerings/registration_s3.py:326`
- `offering_type -> S3OfferingType` — `edgar/offerings/registration_s3.py:330`
- `is_auto_shelf -> bool` — True if ASR in form or fee_deferred — `edgar/offerings/registration_s3.py:357`
- `fee_deferred -> bool` — True for S-3ASR; signals Rule 457(r) deferred fees — `edgar/offerings/registration_s3.py:395`
- `total_offering, net_fee, securities` — same pattern as S1 — `edgar/offerings/registration_s3.py:381-407`
- `takedowns -> Optional[Filings]` — 424B1-B8 filings under same file number — `edgar/offerings/registration_s3.py:413`
- `related_filings -> Optional[Filings]` — `edgar/offerings/registration_s3.py:441`

**S3CoverPage** fields: same as S1CoverPage minus `sic_code`; adds identical `confidence` scoring.

**Key difference from S1:** S3 has no `effective_date` property, no table extraction (`selling_stockholders`, `dilution`, `capitalization`, `underwriting`), and `_extract_s3_cover_page` / `_classify_s3_offering` are module-level functions rather than separate helper files.

---

#### Prospectus424B (`edgar/offerings/prospectus.py:1163`)
Handles all 424B variants. Variants and their primary use:
- **424B1**: exchange offers, IPOs (Rule 424(b)(1))
- **424B2**: structured notes, bank debt (large banks, CUSIP-level)
- **424B3**: resale prospectuses, PIPE resales, rights offerings
- **424B4**: final priced prospectuses, IPOs, shelf takedowns
- **424B5**: shelf takedowns, ATM, firm commitment, PIPE
- **424B7**: WKSI selling stockholder base updates
- **424B8**: prospectus supplements

- `from_filing(filing) -> Prospectus424B` — calls `filing.parse()` once; extracts cover + classifies offering type; stores document for lazy properties — `edgar/offerings/prospectus.py:1203`
- `cover_page -> CoverPageData` — eagerly extracted — `edgar/offerings/prospectus.py:1246`
- `offering_type -> OfferingType` — eagerly classified — `edgar/offerings/prospectus.py:1250`
- `variant -> str` — form without /A suffix — `edgar/offerings/prospectus.py:1258`
- `is_atm, is_preliminary, is_supplement, is_amendment` — boolean flags — `edgar/offerings/prospectus.py:1285-1295`
- `ticker -> Optional[str]` — exchange ticker from cover — `edgar/offerings/prospectus.py:1298`
- `offering_amount, offering_price -> Optional[str]` — raw strings from cover — `edgar/offerings/prospectus.py:1302-1307`
- `sections` — `Sections` dict from parsed document; `.text()` / `.tables()` per section — `edgar/offerings/prospectus.py:1313`
- `pricing -> Optional[PricingData]` — cached; pricing table (price/fee/proceeds per column) — `edgar/offerings/prospectus.py:1348`
- `offering_terms -> Optional[OfferingTerms]` — cached; key-value terms table — `edgar/offerings/prospectus.py:1358`
- `selling_stockholders -> Optional[SellingStockholdersData]` — cached; merges multiple tables — `edgar/offerings/prospectus.py:1367`
- `structured_note_terms -> Optional[StructuredNoteTerms]` — cached; merges multiple key_terms tables — `edgar/offerings/prospectus.py:1387`
- `dilution -> Optional[DilutionData]` — cached — `edgar/offerings/prospectus.py:1409`
- `capitalization -> Optional[CapitalizationData]` — cached — `edgar/offerings/prospectus.py:1418`
- `underwriting -> Optional[UnderwritingInfo]` — cached; table-first, falls back to text extraction — `edgar/offerings/prospectus.py:1427`
- `filing_fees -> FilingFeesData` — cached; from EX-FILING FEES XBRL exhibit (~43% coverage on 424B2, ~23% on 424B5) — `edgar/offerings/prospectus.py:1477`
- `lifecycle -> Optional[ShelfLifecycle]` — cached; uses cover page registration number to query related filings — `edgar/offerings/prospectus.py:1513`
- `shelf_registration -> Optional[Filing]` — delegates to lifecycle — `edgar/offerings/prospectus.py:1547`
- `related_filings` — delegates to lifecycle — `edgar/offerings/prospectus.py:1553`
- `related_8k -> Optional[Filing]` — 8-K filed same day — `edgar/offerings/prospectus.py:1559`
- `deal -> Deal` — always returns a Deal (never None); individual fields None if unavailable — `edgar/offerings/prospectus.py:1569`

**Deal** (`edgar/offerings/prospectus.py:784`): triangulates price, shares, gross/net proceeds from cover_page + pricing + offering_terms. Key computed `cached_property` fields: `price`, `shares`, `gross_proceeds`, `net_proceeds`, `fee_per_share`, `total_fees`, `discount_rate`, `lead_bookrunner`, `underwriter_count`, `dilution_per_share`, `dilution_pct`, `shares_before/after`, `ntbv_before/after`. `to_dict()` returns all non-None values as flat dict.

**ShelfLifecycle** (`edgar/offerings/prospectus.py:394`): constructed from `(current_filing, related_filings_set)`. All properties are `cached_property`. Key properties: `shelf_registration`, `effective_date`, `shelf_expires` (filed date + 3 years), `days_to_expiry`, `review_period_days`, `takedowns: List[Filing]`, `total_takedowns`, `takedown_number` (1-based), `is_latest_takedown`, `avg_days_between_takedowns`, `related_8k`, `shelf_capacity: Optional[RegistrationFeeTable]`, `total_offering_capacity`.

---

#### DraftRegistrationStatement (`edgar/offerings/drs.py:98`)
Wraps DRS and DRS/A filings; detects the underlying public form type from cover page text.

- `from_filing(filing) -> DraftRegistrationStatement` — detects underlying form via `_detect_underlying_form(html)`; extracts 377-XXXXXX registration number from header then HTML fallback; builds `underlying_object` for S-1/F-1 and S-3 — `edgar/offerings/drs.py:134`
- `underlying_form -> str` — detected form type (S-1/F-1/S-3/S-4/F-4/20-F/40-F/Form 10/Unknown) — `edgar/offerings/drs.py:196`
- `underlying_object` — `RegistrationS1 | RegistrationS3 | None` — `edgar/offerings/drs.py:232`
- `registration_number -> Optional[str]` — 377-XXXXXX prefix (distinct from S-1's 333-XXXXXX) — `edgar/offerings/drs.py:225`
- `amendment_number -> Optional[int]` — parsed from "Amendment No. X" in cover — `edgar/offerings/drs.py:220`

**Detection patterns**: 10 ordered regexes in `_FORM_PATTERNS` list (`edgar/offerings/drs.py:45`); compound forms (S-4, F-4) checked before simpler ones (S-3, S-1) to avoid prefix collisions.

---

#### Offering / Campaign (`edgar/offerings/campaign.py:92`)
Complete Reg CF offering lifecycle tracker. `Campaign` is an alias kept for backward compatibility (`edgar/offerings/campaign.py:695`).

- `__init__(filing_or_file_number, cik=None)` — accepts `Filing` or file number string; when Filing: eagerly converts to EntityFiling, parses FormC, extracts both file numbers; when string: defers all — `edgar/offerings/campaign.py:110`
- `file_number / issuer_file_number -> str` — 020-XXXXX offering identifier — `edgar/offerings/campaign.py:172-189`
- `portal_file_number -> Optional[str]` — 007-XXXXX (only available from Filing init) — `edgar/offerings/campaign.py:193`
- `initial_formc -> Optional[FormC]` — cached FormC from init Filing — `edgar/offerings/campaign.py:207`
- `company -> Company` — cached_property — `edgar/offerings/campaign.py:219`
- `all_filings -> EntityFilings` — cached_property; queries by issuer file number — `edgar/offerings/campaign.py:224`
- `filings_by_stage -> Dict[str, List[Filing]]` — cached; groups into initial/amendment/update/report/termination — `edgar/offerings/campaign.py:249`
- `initial_offering -> Optional[FormC]` — `edgar/offerings/campaign.py:281`
- `amendments -> List[FormC]` — `edgar/offerings/campaign.py:289`
- `updates -> List[FormC]` — `edgar/offerings/campaign.py:293`
- `annual_reports -> List[FormC]` — `edgar/offerings/campaign.py:298`
- `termination -> Optional[FormC]` — `edgar/offerings/campaign.py:303`
- `timeline() -> List[Dict]` — chronological events list — `edgar/offerings/campaign.py:315`
- `latest_financials() -> Optional[AnnualReportDisclosure]` — searches C-AR > C-U > C — `edgar/offerings/campaign.py:352`
- `is_active, is_terminated, is_expired -> bool` — status predicates — `edgar/offerings/campaign.py:395-447`
- `current_status -> str` — "Terminated"/"Reporting Phase"/"Active (with updates)"/"Expired"/"Active"/"Unknown" — `edgar/offerings/campaign.py:450`
- `days_since_launch, launch_date, latest_activity_date` — timeline metrics — `edgar/offerings/campaign.py:479-504`
- `to_context(detail) -> str` — minimal (~300 tokens)/standard (~700)/full (~1500) — `edgar/offerings/campaign.py:510`

---

#### Effect (`edgar/effect.py:41`)
Represents an EFFECT notice — the SEC's automated notification that a registration statement has been declared effective.

- `from_xml(submission_xml) -> Effect` — single entry point; parses `<edgarSubmission>` XML — `edgar/effect.py:153`
- `effective_date -> str` — `edgar/effect.py:58`
- `cik` — from `effectiveness_data.filer.cik` — `edgar/effect.py:62`
- `entity` — entity name from filer — `edgar/effect.py:67`
- `source_submission_type -> str` — the form that was made effective (e.g., "POS AM", "S-3") — `edgar/effect.py:73`
- `source_accession_no -> Optional[str]` — `edgar/effect.py:77`
- `get_source_filing()` — navigates back to the filing that triggered effectiveness; tries accession_no first, then file_number+form — `edgar/effect.py:79`
- `summary() -> pd.DataFrame` — cached (`_cached_summary`); columns: cik, entity, source, live, effective — `edgar/effect.py:96`
- `to_context(detail) -> str` — `edgar/effect.py:110`

**EffectiveData** (`edgar/effect.py:20`): plain class; fields: `final_effective_date`, `file_number`, `accession_no`, `submission_type`, `form`, `filer: Filer`.

---

### Class hierarchy

```
# Crowdfunding (Regulation CF)
FormC
  └── contains FilerInformation (Pydantic, frozen)
                  └── company -> Company (LRU cached)
      IssuerInformation (Pydantic)
                  └── FundingPortal (Pydantic)
                      Address
      OfferingInformation (Pydantic)
      AnnualReportDisclosure (Pydantic)
      SignatureInfo (Pydantic)
                  └── IssuerSignature (Pydantic)
                      List[PersonSignature] (Pydantic)
IssuerCompany
  └── as_company() -> Company
      get_offerings() -> List[Offering]
Offering (= Campaign alias)
  └── contains FormC (via initial_formc)
      EntityFilings (via all_filings)

# Private Placement
FormD
  └── contains Issuer (from edgar._party)
      List[Person] (from edgar._party)
      OfferingData
          └── IndustryGroup
              InvestmentFundInfo
              OfferingSalesAmounts
              Investors
              SalesCommissionFindersFees
              UseOfProceeds
              List[SalesCompensationRecipient]
      SignatureBlock
          └── List[Signature]

# Registration Statements
RegistrationS1
  └── _filing: Filing
      _cover_page: S1CoverPage (Pydantic)
      _offering_type: S1OfferingType (Enum, str)
      _fee_table: RegistrationFeeTable | None (Pydantic)
      cached_property: selling_stockholders, dilution, capitalization,
                       underwriting, takedowns, related_filings, effective_date

RegistrationS3
  └── _filing: Filing
      _cover_page: S3CoverPage (Pydantic)
      _offering_type: S3OfferingType (Enum, str)
      _fee_table: RegistrationFeeTable | None (Pydantic)
      cached_property: takedowns, related_filings

DraftRegistrationStatement
  └── _filing: Filing
      _underlying_form: str
      _underlying_object: RegistrationS1 | RegistrationS3 | None

# 424B Prospectus
Prospectus424B
  └── _filing: Filing
      _cover_page: CoverPageData (Pydantic)
      _offering_type: OfferingType (Enum, str)
      _document: parsed Document | None
      cached_property:
        pricing -> PricingData (Pydantic)
            └── List[PricingColumnData]
        offering_terms -> OfferingTerms (Pydantic)
        selling_stockholders -> SellingStockholdersData (Pydantic)
            └── List[SellingStockholderEntry]
        structured_note_terms -> StructuredNoteTerms (Pydantic)
        dilution -> DilutionData (Pydantic)
        capitalization -> CapitalizationData (Pydantic)
        underwriting -> UnderwritingInfo (Pydantic)
            └── List[UnderwriterEntry]
        filing_fees -> FilingFeesData (Pydantic)
            └── List[FilingFeesRow]
        lifecycle -> ShelfLifecycle | None
        deal -> Deal (always present)
            └── references Prospectus424B (back-ref)

ShelfLifecycle
  └── _current: Filing
      _related: Filings
      cached_property:
        shelf_registration -> Filing | None
        shelf_capacity -> RegistrationFeeTable | None

# EFFECT notice
Effect
  └── effectiveness_data: EffectiveData
      is_live: bool
      schema_version: Optional[str]
EffectiveData
  └── filer: Filer (edgar._party.Filer)

# Shared data models (in edgar/offerings/prospectus.py)
RegistrationFeeTable (Pydantic)
  └── List[FeeTableSecurity]  (securities)
      List[FeeTableSecurity]  (carry_forwards)
```

---

### Configuration & options

| Option | Type | Default | Effect |
|---|---|---|---|
| `S1CoverPage.confidence` | `str` | `"low"` | Extraction confidence: low/medium/high (computed from fields found) |
| `S3CoverPage.confidence` | `str` | `"low"` | Same as above |
| `S1CoverPage.is_rule_415` | `bool` | `False` | Rule 415 delayed/continuous offering flag |
| `S1CoverPage.is_rule_462b` | `bool` | `False` | Rule 462(b) automatic effectiveness |
| `S1CoverPage.is_rule_462e` | `bool` | `False` | Rule 462(e) auto-shelf flag |
| `S3CoverPage.is_rule_462e` | `bool` | `False` | Set True if ASR in form name |
| `RegistrationFeeTable.fee_deferred` | `bool` | `False` | True when all securities use Rule 457(r) — S-3ASR pattern |
| `RegistrationFeeTable.has_carry_forward` | `bool` | `False` | True when carry-forward securities present |
| `Offering.__init__` `filing_or_file_number` | `Filing | str` | required | When Filing: eager init (fast); when str: lazy (requires `cik`) |
| `FormC.from_xml` `form` | `str` | required | Form variant string used to populate `description` and `campaign_status` |
| `FormD.from_xml` | no options | — | Fully determined by XML content |
| `DraftRegistrationStatement` `underlying_form` | `str` | detected | 'Unknown' if no pattern matched in first 8000 chars of cover text |
| `ShelfLifecycle.shelf_expires` | `date` | filed + 3 years | Feb 29 edge case: falls back to Feb 28 |
| `to_context(detail)` | `str` | `'standard'` | 'minimal' / 'standard' / 'full' across all classes |

---

### Data flow / lifecycle

**FormC / FormD dispatch:**
1. `filing.obj()` → `data_object()` → `edgar/__init__.py` dispatcher
2. `matches_form(sec_filing, ["C", "C-U", "C-AR", "C-TR"])` → `FormC.from_filing(filing)` (`edgar/__init__.py:378`)
3. `matches_form(sec_filing, "D")` → `xml = filing.xml()` → `FormD.from_xml(xml)` (`edgar/__init__.py:374`)
4. `FormC.from_filing` calls `filing.xml()`, delegates to `FormC.from_xml(xml, form)`
5. BeautifulSoup XML parsing extracts all four sub-objects; `AnnualReportDisclosure` and `OfferingInformation` are optional (None when tag is empty)

**S-1/S-3 dispatch:**
1. `matches_form(sec_filing, ['S-1', 'F-1'])` → `RegistrationS1.from_filing(filing)` (`edgar/__init__.py:385`)
2. `from_filing` calls `filing.html()` once; passes same HTML to `_s1_cover.extract_s1_cover_page` and `_s1_classifier.classify_s1_offering_type`
3. `extract_registration_fee_table(filing)` downloads and HTML-parses EX-FILING FEES attachment separately
4. Table properties (`dilution`, `selling_stockholders`, etc.) are `cached_property`: lazily call `filing.parse()` then `_424b_tables.classify_tables_in_document()`
5. `takedowns` and `related_filings` query `Company.get_filings(file_number=...)` on demand

**424B dispatch:**
1. `matches_form(sec_filing, [...424B forms...])` → `Prospectus424B.from_filing(filing)` (`edgar/__init__.py:393`)
2. `filing.parse()` called once; document stored on instance
3. `extract_cover_page_fields(filing, document=doc)` — 11 fields from metadata + text regex
4. `classify_offering_type(filing, document=doc)` — priority cascade over cover text signals (424B7 is hardcoded to `base_prospectus_update`)
5. All other properties are `cached_property` against stored `_document`
6. `lifecycle` uses `cover_page.registration_number` to query `Company.get_filings(file_number=...)`, wraps result in `ShelfLifecycle`
7. `deal` always constructs `Deal(self)`; Deal triangulates across multiple sub-objects using its own `cached_property` chain

**DRS dispatch:**
1. `matches_form(sec_filing, "DRS")` → `DraftRegistrationStatement.from_filing(filing)` (`edgar/__init__.py:381`)
2. `filing.html()` fetched; `_detect_underlying_form(html)` scans first 8000 chars of text
3. Registration number: tries `filing.header.file_numbers` first, then HTML regex for `377-\d{5,7}`
4. If underlying_form is S-1 or F-1: attempts `RegistrationS1.from_filing(filing)` as `underlying_object` (exceptions silently caught)

**EFFECT dispatch:**
1. `matches_form(sec_filing, "EFFECT")` → `xml = filing.xml()` → `Effect.from_xml(xml)` (`edgar/__init__.py:370`)
2. BeautifulSoup XML mode; parses `<edgarSubmission>/<effectiveData>`
3. `get_source_filing()` lazily navigates back to the original registration by calling `get_entity(cik).get_filings()`

**Offering lifecycle:**
- Initialized from Filing: eager conversion to EntityFiling, eager FormC parse, both file numbers extracted at `__init__` time
- `all_filings`: queries `company.get_filings(file_number=issuer_file_number)` — uses 020-XXXXX not 007-XXXXX
- `filings_by_stage` classifies each filing form into 5 lifecycle stages
- `latest_financials()` searches in reverse: C-AR/A → C-U/U-A → C → C/A for the first non-None `annual_report_disclosure`

**Caching patterns across all objects:**
- `cached_property` for anything requiring network I/O or heavy parsing (all table extractions, `lifecycle`, `takedowns`, `related_filings`, `deal`)
- `lru_cache(maxsize=1)` on `FilerInformation.company` property
- `_cached_summary` manual attribute on `Effect.summary()` (not using `cached_property` decorator)
- `ShelfLifecycle` uses `cached_property` throughout — the whole object is itself a `cached_property` on `Prospectus424B`

---

### Design patterns

- **Factory class method**: `from_filing(filing)` and `from_xml(xml)` pattern across every domain class; `from_filing` always fetches document once and passes it down to helpers to avoid re-fetching.
- **Lazy cached_property**: all expensive properties (table extraction, lifecycle, deal, underwriting) are `cached_property` — computed on first access, stored forever.
- **Eager partial construction**: `RegistrationS1/S3.from_filing` fetches HTML once at construction time and passes it to both cover extractor and classifier, avoiding a second network call.
- **Document-once pattern**: `Prospectus424B.from_filing` calls `filing.parse()` once and stores the `_document`; all `cached_property` methods reuse it.
- **Priority cascade classifier**: both `_424b_classifier.classify_offering_type` and `_s1_classifier.classify_s1_offering_type` use signal-collection dicts followed by a hard-ordered decision cascade with confidence levels.
- **Signal collection with confidence scoring**: classifiers collect all signals first, then apply priority rules; return `{type, confidence, signals, sub_type}` dicts.
- **Pydantic for sub-models, plain class for top-level**: FormC, FormD, RegistrationS1/S3, Prospectus424B, Effect are plain classes; their components (CoverPageData, S1CoverPage, FeeTableSecurity, etc.) are Pydantic BaseModel for validation.
- **Backward-compatible alias**: `Campaign = Offering` at module level; `get_issuer_company()` deprecated in favor of `issuer` property.
- **Two-phase lifecycle**: `Offering` performs all expensive operations at `__init__` when a Filing is provided; file-number-only init defers everything.
- **Triangulation in Deal**: `Deal` tries cover_page → pricing table → computed (price × shares) in order for each numeric field to maximize data availability.

---

### Cross-domain interactions

**Imports from other edgar modules:**
- `edgar._party.Filer, Issuer, Person, Address` — used by FormC, FormD, Effect
- `edgar.entity.Company` — used by IssuerCompany, Offering, lifecycle navigation (RegistrationS1/S3, ShelfLifecycle)
- `edgar.entity.EntityFilings` — type of `Offering.all_filings`
- `edgar.xmltools.child_text, child_value` — XML extraction helpers used by FormC, FormD, Effect
- `edgar.richtools.repr_rich, Docs` — terminal rendering
- `edgar.core.get_bool` — FormC XML parsing
- `edgar.reference.states` — state code lookup in FormC and AnnualReportDisclosure
- `edgar.documents.document.Sections` — `Prospectus424B.sections`
- `edgar.documents.table_nodes.TableNode` — `_424b_tables.py` type hints

**Consumed by:**
- `edgar/__init__.py:data_object()` — the central dispatcher; routes all 40+ form types to domain objects
- `edgar/__init__.py:get_obj_info()` — form-to-class-name mapping registry (`edgar/__init__.py:195`)
- `edgar/shelfofferings.py:list_takedown_forms()` — simple utility querying form metadata; holds canonical list of 424B* form codes

**`edgar/shelfofferings.py` role**: minimal module (`edgar/shelfofferings.py:1`) — exports one function `list_takedown_forms()` that returns a filtered DataFrame from `list_forms()`. Contains the canonical `takedown_forms` list including 424A, all 424B variants, 497, 486BPOS, F-3MEF. No parsing logic; acts as a reference/discovery utility.

---

### Gotchas & notable behaviors

**FormC:**
- Date parsing expects MM-DD-YYYY format (not ISO 8601); `parse_date` raises `ValueError` on mismatch; `maybe_date()` returns None on failure — `edgar/offerings/formc.py:916,393`
- `AnnualReportDisclosure` is None for C-TR and often for C-U filings; always check before access
- `OfferingInformation` is None for C-AR forms; it is also None if the XML tag exists but is empty (`edgar/offerings/formc.py:1006`)
- `portal_file_number` is None for C-AR forms (no funding portal element)
- `FilerInformation.company` property uses `@lru_cache(maxsize=1)` on a `@property` — this is applied to an instance method; it caches per-instance correctly
- `group_offerings_by_file_number` uses PyArrow operations for performance; defined in both `formc.py` (line 396) and re-exported from `__init__.py` (line 17)

**FormD:**
- `from_xml` is the only entry point; there is no `from_filing` — dispatch in `__init__.py` calls `filing.xml()` then `FormD.from_xml(xml)` directly
- `SalesCompensationRecipient` strips literal "None" strings from XML fields (regex `re.sub("None", "")`) — this is a real-data cleanup, not an error — `edgar/offerings/formd.py:121`
- Amount fields (`total_offering_amount`, `total_amount_sold`, etc.) are typed as `object`, not `float` — they remain raw strings from XML
- `UseOfProceeds` is always extracted (not optional); will raise if `useOfProceeds` tag missing — `edgar/offerings/formd.py:271`
- No `C/A` form dispatch: Form C/A amendments match `matches_form(sec_filing, ["C", "C-U", "C-AR", "C-TR"])` because `matches_form` uses prefix matching; but `C-U/A`, `C-AR/A` do NOT match this list; they must be accessed as raw filings or through `Offering.amendments`

**RegistrationS1/S3:**
- `confidence` in cover page is "low" when fewer than 2 fields extracted; this is normal for older filings using non-standard HTML
- `takedowns` and `related_filings` rely on `registration_number` from cover page; if extraction fails (None), returns None
- `effective_date` on S1 searches for EFFECT filing in `related_filings` — can be slow as it triggers a network call for `related_filings`
- S3's `_classify_s3_offering` is inline (not a separate file); uses `fee_table.fee_deferred` as the primary AUTO_SHELF signal before HTML scanning
- S3 variant codes: S-3D and S-3DPOS (direct registration systems) also dispatch to `RegistrationS3` — `edgar/__init__.py:265-266`
- `takedowns` filters to 424B1-B8 only (no 424B6); 424B6 is not in the list

**Prospectus424B:**
- 424B7 is short-circuited by classifier: always returns `base_prospectus_update` with high confidence — `edgar/offerings/_424b_classifier.py:42`
- `filing_fees` (XBRL): coverage is ~43% of 424B2, ~23% of 424B5, ~7% of 424B3; 424B1 and 424B4 have 0% coverage; available only from 2022+ (SEC Rule 408)
- `selling_stockholders` merges multiple tables (e.g., common shares + warrants in separate tables) — `edgar/offerings/prospectus.py:1368`
- `structured_note_terms` also merges multiple key_terms tables and fills None fields from extras — `edgar/offerings/prospectus.py:1394`
- `CoverPageData.offering_amount` can be sentinel strings: "exchange-offer", "at-the-market", "preliminary-TBD", "market-price" — `offering_amount_float` returns None for these — `edgar/offerings/prospectus.py:133`
- `Deal.price` triangulation order: cover_page offering_price → pricing table per-unit column; `Deal.gross_proceeds`: cover_page → pricing table total → price × shares
- `ShelfLifecycle.shelf_expires` adds exactly 3 years; Feb 29 raises ValueError caught and falls back to Feb 28 — `edgar/offerings/prospectus.py:466`
- `ShelfLifecycle` is `cached_property` on `Prospectus424B`; `Deal` is also `cached_property`; both are constructed lazily on first access
- `sections` property returns empty `Sections({})` if `_document` is None (parse failed) — `edgar/offerings/prospectus.py:1332`

**DraftRegistrationStatement:**
- Registration numbers use 377-XXXXXX prefix (confidential DRS), not 333-XXXXXX (public S-1/S-3)
- `underlying_form` is "Unknown" if no pattern matches; `underlying_object` is None for S-4, F-4, 20-F, 40-F, Form 10 — only S-1/F-1 and S-3 get a delegate object
- Pattern matching is ordered: S-4/F-4 checked before S-3/F-3 before S-1/F-1 to avoid prefix collision — `edgar/offerings/drs.py:45`
- `_detect_underlying_form` uses BeautifulSoup lxml (not xml) to handle malformed HTML in drafts

**Effect:**
- `source_submission_type` falls back to `effectiveness_data.form` if `submission_type` is None — handles both `<submissionType>` and `<form>` XML paths — `edgar/effect.py:73`
- `get_source_filing()` makes live API calls; no caching; can fail silently (returns None)
- `summary()` uses a manual `_cached_summary` attribute pattern rather than `cached_property`
- `is_live` is False if `testOrLive` element is missing (element is checked with `and`) — `edgar/effect.py:177`

**Classifier accuracy notes:**
- `_424b_classifier`: 12/12 validation accuracy; structured note detection uses `pricing_supplement` in narrow cover (first 3000 chars) as highest-priority signal
- `_s1_classifier`: SPAC detection uses `blank check` as highest-priority single signal; resale requires both `no_proceeds` + `selling_stockholder` for high confidence
- Both classifiers return `{type, confidence, signals, sub_type}` dict; `signals` list is useful for debugging misclassifications

**`_fee_table.py` nuances:**
- Handles two HTML formats: 2023+ ("Fees to be Paid" row category column present) and 2022 format (direct security type in first column, no row category) — `edgar/offerings/_fee_table.py:178`
- `total_offering_amount` computed from per-security aggregates when summary row is absent or contains only the fee (2022 format bug) — `edgar/offerings/_fee_table.py:205`
- `fee_deferred` detected if ALL securities use Rule 457(r), or if `net_fee_due == 0.0` with no offering amount

**`_424b_xbrl.py` nuances:**
- Parses Inline XBRL (iXBRL) context IDs using two patterns: `offrl_N` and `_NTypedMember` for row number extraction
- Duplicate `(name, ctx)` pairs are deduplicated via `seen_keys` set
- `is_final_prospectus` comes from `ffd:FnlPrspctsFlg` XBRL element
