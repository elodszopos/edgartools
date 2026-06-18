# Form ATS-N — Alternative Trading System

**SEC form codes**: ATS-N, ATS-N/MA, ATS-N/UA, ATS-N/CA, ATS-N-W
**Python classes**: `AlternativeTradingSystem`, `AlternativeTradingSystemWithdrawal`
**Access**: `filing.obj()` → one of the two classes via `from_atsn_filing()`
**Base fields**: See `_base-filing.md`
**Source**: `edgar/ats/atsn.py`, `edgar/ats/models.py`

## Complete Field Reference

### From Filing (inherited)
See `_base-filing.md`

### AlternativeTradingSystem-Specific Fields

#### Direct Attributes (set in `__init__`)

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `form_type` | `str` | no | Submission type from XML header, e.g. `'ATS-N'`, `'ATS-N/MA'` |
| `amended_accession_number` | `Optional[str]` | no | Accession number being amended (from XML header) |
| `filer` | `FilerContact` | no | Header-level filer identity and contact |
| `amendment_statement` | `Optional[str]` | no | Free-text statement about the amendment from cover element |
| `identifying_info` | `ATSIdentifyingInfo` | no | Part I — identifying information |
| `operator_activities` | `ATSOperatorActivities` | no | Part II — broker-dealer operator activities |
| `operations` | `ATSOperations` | no | Part III — manner of operations |

#### Convenience Properties

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `cik` | `str` | no | Delegated from `filer.cik` |
| `mpid` | `Optional[str]` | no | `identifying_info.nms_stock_mpid` or `filer.mpid` |
| `ats_name` | `Optional[str]` | no | `identifying_info.ats_commercial_name` or `filer.nms_stock_ats_name` |
| `operator_name` | `Optional[str]` | no | `identifying_info.operator_legal_name` |
| `is_amendment` | `bool` | no | True when `form_type` in `('ATS-N/MA', 'ATS-N/UA', 'ATS-N/CA')` |
| `subscriber_types` | `list` | no | Delegated from `operations.subscriber_types` |
| `order_types` | `Optional[str]` | no | Delegated from `operations.order_types` |
| `fees` | `dict` | no | `{'direct': ..., 'bundled': ..., 'rebates': ...}` from `operations` |

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing` | `Optional[AlternativeTradingSystem]` | Classmethod. Parses XML, applies oversized PDF URLs. Returns None on XML error. |
| `to_context` | `detail: str = 'standard'` | `str` | AI context. `'minimal'`: identity. `'standard'`: + key Part III flags. `'full'`: + truncated narratives. |

### AlternativeTradingSystemWithdrawal-Specific Fields

#### Direct Attributes

| Field | Type | Lazy | Description |
|-------|------|------|-------------|
| `form_type` | `str` | no | Always `'ATS-N-W'` |
| `withdrawn_accession_number` | `Optional[str]` | no | Accession number being withdrawn |
| `filer` | `FilerContact` | no | Identity from header (no Part I in withdrawals) |
| `withdrawal_statement` | `Optional[str]` | no | Optional cover statement |

#### Convenience Properties

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `str` | `filer.cik` |
| `mpid` | `Optional[str]` | `filer.mpid` |
| `ats_name` | `Optional[str]` | `filer.nms_stock_ats_name` |

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_filing` | `filing` | `Optional[AlternativeTradingSystemWithdrawal]` | Classmethod. Parses XML header only (no formData for withdrawals). |

### Module-Level Factory

| Symbol | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `from_atsn_filing` | `filing` | `Optional[Union[AlternativeTradingSystem, AlternativeTradingSystemWithdrawal]]` | Routes ATS-N-W to withdrawal class, all others to full parser |

## Nested Objects

### FilerContact (Pydantic BaseModel — `edgar/ats/models.py`)

| Field | Type | Description |
|-------|------|-------------|
| `cik` | `str` | Filing entity CIK (leading zeros stripped) |
| `mpid` | `Optional[str]` | FINRA market participant ID (from header; ATS-N-W only) |
| `nms_stock_ats_name` | `Optional[str]` | ATS commercial name (from header; ATS-N-W only) |
| `contact_name` | `Optional[str]` | Contact person name |
| `contact_phone` | `Optional[str]` | Contact phone number |
| `contact_email` | `Optional[str]` | Contact email address |

### ATSIdentifyingInfo (Pydantic BaseModel — Part I)

| Field | Type | Description |
|-------|------|-------------|
| `ats_commercial_name` | `Optional[str]` | Commercial ATS name from cover |
| `operator_legal_name` | `Optional[str]` | Legal name of BD operator (Part I Item 2) |
| `supersedes_prior_form_ats` | `Optional[bool]` | Whether filing supersedes prior Form ATS |
| `ats_names` | `List[ATSNameRecord]` | Repeating Item 3 name records (multi-venue operators) |
| `bd_file_number` | `Optional[str]` | Broker-dealer file number (Item 4a) |
| `bd_crd_number` | `Optional[str]` | Broker-dealer CRD number (Item 4a) |
| `sro_name` | `Optional[str]` | SRO full name (Item 5a) |
| `nms_stock_mpid` | `Optional[str]` | NMS stock MPID (Item 5c) |
| `website` | `Optional[str]` | ATS website URL (Item 6) |
| `primary_site` | `Optional[ATSAddress]` | Primary server/office site (Item 7) |
| `secondary_sites` | `List[ATSAddress]` | Secondary server sites (Item 7, repeating) |

### ATSNameRecord (Pydantic BaseModel)

| Field | Type | Description |
|-------|------|-------------|
| `ats_name` | `str` | ATS name from repeating atsName element attribute |
| `mpid` | `Optional[str]` | MPID for this venue (if present) |

### ATSAddress (Pydantic BaseModel)

| Field | Type | Description |
|-------|------|-------------|
| `street1` | `Optional[str]` | Street address line 1 |
| `street2` | `Optional[str]` | Street address line 2 |
| `city` | `Optional[str]` | City |
| `state_or_country` | `Optional[str]` | State or country code |
| `zip_code` | `Optional[str]` | ZIP code |

### ATSOperatorActivities (Pydantic BaseModel — Part II, ~30 fields)

| Field Group | Fields | Description |
|------------|--------|-------------|
| Item 1 — BD units | `bd_units_permit_order_entry`, `bd_units_description`, `bd_services_same_to_all`, `bd_services_difference_explanation`, `bd_has_third_party_arrangements`, `can_route_oat_interest` | BD units entering orders |
| Item 2 — Affiliates | `affiliates_permit_order_entry`, `affiliates_description`, `affiliates_services_same_to_subscribers`, `affiliates_have_third_party_arrangements`, `can_route_oat_interest_via_affl` | Affiliate order entry |
| Item 3 — Opt-out | `subscribers_can_opt_out_of_bd`, `subscriber_opt_out_bd_explanation`, `subscribers_can_opt_out_of_affl`, `subscriber_opt_out_affl_explanation`, `opt_out_same_to_all` | Subscriber opt-out rights |
| Item 4 — Trading centers | `has_trading_center_arrangements`, `trading_center_arrangements`, `affl_has_trading_center_arrangements` | Trading-center arrangements |
| Item 5 — Bundled products | `offers_bundled_products`, `bundled_products_description`, `bundled_services_same_to_all`, `affl_offers_bundled_products`, `affl_bundled_products_description`, `affl_bundled_services_same_to_all` | Bundled products/services |
| Item 6 — Employees | `employees_access_confidential`, `employee_services_description`, `has_third_party_service_providers`, `service_providers_description`, `service_provider_uses_ats_services` | Employee and provider access |
| Item 7 — Confidentiality | `safeguards_description`, `subscriber_can_consent_to_disclosure`, `roles_responsibilities_summary` | Confidentiality safeguards |

All bool fields are `Optional[bool]` — None when absent in XML. All description/narrative fields are `Optional[str]`.

### ATSOperations (Pydantic BaseModel — Part III, ~60 fields)

| Field Group | Key Fields | Description |
|------------|-----------|-------------|
| Item 1 — Subscribers | `subscriber_types: List[str]` | List of subscriber category strings |
| Item 2 — Access | `requires_registered_bd`, `has_other_access_conditions`, `access_conditions_summary`, `access_conditions_same_for_all`, `requires_written_agreement` | Access conditions |
| Item 3 — Exclusion | `can_exclude_subscribers`, `exclusion_conditions_summary`, `exclusion_conditions_same_for_all` | Subscriber exclusion |
| Item 4 — Hours | `hours_of_operation`, `hours_same_for_all` | Operating hours |
| Item 5 — Protocols | `permits_order_trading_via_protocol`, `protocol_description`, `protocol_same_for_all`, `has_other_connectivity_means`, `other_connectivity_description`, `other_connectivity_same_for_all` | Connectivity |
| Item 6 — Co-location | `offers_colocation_services`, `colocation_description`, `colocation_terms_same_for_all`, `has_other_colocation_means`, `offers_reduced_speed_access` | Co-location services |
| Item 7 — Order types | `order_types`, `order_types_pdf_url`, `order_types_same_for_all` | Order type descriptions; PDF URL when XML overflows |
| Item 8 — Sizes | `has_size_requirements`, `size_requirements_description`, `size_requirements_same_for_all`, `size_requirements_difference_explanation`, `accepts_odd_lots`, `accepts_mixed_lots`, `mixed_lots_description`, `mixed_lots_same_for_all` | Order size requirements |
| Item 9 — IOIs | `uses_indication_messages`, `conditional_orders`, `conditional_orders_pdf_url`, `conditional_orders_same_for_all` | Conditional orders and IOIs |
| Item 10 — Open/close | `opening_reopening_details`, `opening_reopening_same_for_all`, `unexecuted_orders_treatment`, `trading_hours_execution_differs`, `pre_open_execution_differs` | Open/close procedures |
| Item 11 — NMS matching | `nms_stock_structure`, `nms_structure_same_for_all`, `nms_matching_rules`, `nms_matching_rules_pdf_url`, `nms_matching_rules_same_for_all` | Matching rules |
| Item 12 — Arrangements | `has_informal_arrangements` | Informal arrangements |
| Item 13 — Segmentation | `has_segmentation`, `segmentation_description`, `segmentation_description_pdf_url`, `segmentation_same_for_all`, `segmentation_category_disclosed`, `segmentation_disclosure_description`, `segmentation_disclosure_same_for_all`, `customer_order_segmentation` | Order flow tiering |
| Item 14 — Counter-party | `permits_counterparty_selection`, `counterparty_selection_description`, `counterparty_selection_same_for_all` | Counter-party selection |
| Item 15 — Display | `uses_electronic_display_communication`, `displays_subscriber_order_book`, `display_description`, `display_same_for_all` | Display of trading interest |
| Item 16 — Routing | `routes_orders_outside_ats` | Order routing |
| Item 17 — Treatment | `has_treatment_differences`, `treatment_same_for_all` | Differential treatment |
| Item 18 — After hours | `trades_outside_regular_hours` | Outside regular hours trading |
| Item 19 — Fees | `fees_direct`, `fees_bundled`, `fees_rebates` | Fee structure (free text) |
| Item 20 — Suspension | `suspension_procedures`, `suspension_procedures_same_for_all` | Suspension procedures |
| Item 21 — Reporting | `trade_reporting_arrangements`, `trade_reporting_same_for_all` | Trade reporting |
| Item 22 — Clearance | `clearance_settlement`, `clearance_settlement_same_for_all` | Clearance and settlement |
| Item 23 — Data | `market_data_sources`, `market_data_same_for_all` | Market data sources |
| Item 24 — Outside | `routes_subscriber_orders_outside` | Subscriber orders routed outside |
| Item 25 — Fair access | `exceeds_fair_access_threshold` | Fair access threshold flag |
| Item 26 — Stats | `publishes_execution_stats` | Execution statistics publication |

All bool fields are `Optional[bool]`. All narrative/description fields are `Optional[str]`. `subscriber_types` is `List[str]`.

## Error Paths

| Condition | Behavior |
|-----------|----------|
| XML parse fails | `from_filing` returns None; logs warning |
| No `formData` element in XML | `_parse_xml` returns None → `from_filing` returns None |
| Gate flag absent in XML | `_gate()` returns None (not True/False) |
| No EX-102 oversized PDF attachment | `*_pdf_url` fields remain None |

## Access Patterns

- `filing.obj()` → `AlternativeTradingSystem` or `AlternativeTradingSystemWithdrawal`
- `from_atsn_filing(filing)` — module-level dispatcher
- `ats.operations.subscriber_types` — list of subscriber category strings
- `ats.operations.order_types` — full narrative text; check `order_types_pdf_url` for PDF supplement
- `ats.fees` — convenience dict; same as accessing `operations.fees_direct/bundled/rebates`
- Gate flag interpretation: None = absent in XML, True = "Y", False = "N"
- Oversized narrative items (7A, 9A, 11C, 13A) may have `*_pdf_url` set even when XML narrative is non-empty — PDF is extended version, not replacement
