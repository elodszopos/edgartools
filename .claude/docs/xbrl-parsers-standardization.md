## XBRL Linkbase Parsers & Concept Standardization

### Overview

The `edgar.xbrl.parsers` package implements a coordinator-plus-six-specialist architecture that converts raw SEC XBRL filing XML into typed in-memory structures. `XBRLParser` (the coordinator) owns all shared dictionaries and delegates every parse operation to one of six specialist parsers: `SchemaParser`, `LabelsParser`, `PresentationParser`, `CalculationParser`, `DefinitionParser`, and `InstanceParser`. Each specialist receives direct references (not copies) to the shared dictionaries so writes are immediately visible to every other specialist without copying.

The `edgar.xbrl.standardization` package is the concept normalization layer that sits above the raw parsed structures. It maps company-specific XBRL tags (e.g., `tsla:AutomotiveRevenues`) and US-GAAP tags to canonical human-readable display names (e.g., "Revenue") via a three-tier lookup: a pre-built reverse index (O(1) hash lookup), company-specific JSON files, and a fallback core `concept_mappings.json`. The entire layer is exposed through module-level singletons to avoid repeated file I/O across statement calls.

---

### Public API Surface

| Symbol | file:line | Purpose |
|---|---|---|
| `XBRLParser` | `edgar/xbrl/parsers/coordinator.py:33` | Main coordinator; only class users instantiate directly |
| `BaseParser` | `edgar/xbrl/parsers/base.py:16` | Shared XML utilities; not instantiated directly |
| `SchemaParser` | `edgar/xbrl/parsers/schema.py:19` | Parses `.xsd` files; builds `element_catalog` and `role_types` |
| `LabelsParser` | `edgar/xbrl/parsers/labels.py:20` | Parses `*_lab.xml`; populates `.labels` on each `ElementCatalog` entry |
| `PresentationParser` | `edgar/xbrl/parsers/presentation.py:19` | Parses `*_pre.xml`; builds `presentation_trees` |
| `CalculationParser` | `edgar/xbrl/parsers/calculation.py:17` | Parses `*_cal.xml`; builds `calculation_trees` |
| `DefinitionParser` | `edgar/xbrl/parsers/definition.py:17` | Parses `*_def.xml`; builds `tables`, `axes`, `domains` |
| `InstanceParser` | `edgar/xbrl/parsers/instance.py:22` | Parses `.xml` instance doc; builds `contexts`, `facts`, `units`, `footnotes` |
| `StandardConcept` | `edgar/xbrl/standardization/core.py:34` | `str` enum of ~50 canonical concept labels |
| `MappingStore` | `edgar/xbrl/standardization/core.py:145` | Loads/holds `concept_mappings.json` + company JSON files |
| `ConceptMapper` | `edgar/xbrl/standardization/core.py:511` | Maps a single concept with context; wraps `MappingStore` |
| `ReverseIndex` | `edgar/xbrl/standardization/reverse_index.py:65` | O(1) XBRL-tag→standard-concept hash index from `gaap_mappings.json` |
| `SectionMembership` | `edgar/xbrl/standardization/sections.py:19` | Maps standard concept → balance sheet section for disambiguation |
| `StandardizationCache` | `edgar/xbrl/standardization/cache.py:15` | Per-XBRL-instance label + statement result cache |
| `UnmappedTagLogger` | `edgar/xbrl/standardization/unmapped_logger.py:105` | Logs unmapped and ambiguous tags to CSV for mapping expansion |
| `standardize_statement()` | `edgar/xbrl/standardization/core.py:984` | Top-level function: adds `standard_concept` metadata to statement rows |
| `initialize_default_mappings()` | `edgar/xbrl/standardization/core.py:1123` | Creates a `MappingStore`; creates `concept_mappings.json` if absent |
| `get_default_store()` | `edgar/xbrl/standardization/__init__.py:24` | Module-level `MappingStore` singleton |
| `get_default_mapper()` | `edgar/xbrl/standardization/__init__.py:40` | Module-level `ConceptMapper` singleton |
| `get_reverse_index()` | `edgar/xbrl/standardization/reverse_index.py:609` | Module-level `ReverseIndex` singleton |
| `get_section_membership()` | `edgar/xbrl/standardization/sections.py:294` | Module-level `SectionMembership` singleton |
| `sic_to_fama_french()` | `edgar/xbrl/standardization/sic_industry.py:206` | Maps 4-digit SIC int → Fama-French 48 code |
| `get_balance_type()` | `edgar/xbrl/parsers/concepts.py:333` | Looks up debit/credit balance type for a US-GAAP concept |

---

### Key Classes

**XBRLParser** (`edgar/xbrl/parsers/coordinator.py:33`)  
Owns all shared data dictionaries and instantiates the six component parsers. Delegates every `parse_*` call transparently for API compatibility with the original monolithic parser.

- `__init__() -> None` — allocates all shared dicts, calls `_init_parsers()` — `:41`
- `_init_parsers() -> None` — creates each specialist with reference-injected shared dicts; calls `schema_parser.set_linkbase_parsers(...)` to enable embedded linkbase dispatch — `:94`
- `parse_directory(directory_path) -> None` — discovers and parses `.xsd` first, then `*_lab/pre/cal/def.xml`, then `.xml` instance files — `:209`
- `parse_schema/labels/presentation/calculation/definition/instance(file_path) -> None` — thin delegation wrappers — `:260–306`
- `parse_*_content(content: str) -> None` — content-string variants of each parser — `:264–310`
- `get_facts_by_key(element_id, context_ref) -> List[Fact]` — handles both single and duplicate facts via hybrid key scheme — `:161`
- `get_fact(element_id, context_ref) -> Optional[Fact]` — returns first fact for a key — `:194`
- `count_facts(content: str) -> tuple[int, int]` — returns `(unique_facts, total_fact_instances)` without full parse — `:308`

**SchemaParser** (`edgar/xbrl/parsers/schema.py:19`)  
Builds the `element_catalog` from `<xs:element>` declarations and dispatches embedded linkbases.

- `parse_schema_content(content: str) -> None` — extracts element properties (`id`/`name`, `type`, `balance`, `periodType`, `abstract`), defaults `period_type` to `"duration"` — `:66`
- `set_linkbase_parsers(labels_parser, presentation_parser, calculation_parser, definition_parser) -> None` — stores content-parse callbacks for embedded linkbase forwarding — `:43`
- `_extract_embedded_linkbases(schema_content: str) -> Dict` — XPath-based extraction of `<link:roleType>` definitions and `<link:labelLink>` / `<link:presentationLink>` / `<link:calculationLink>` / `<link:definitionLink>` elements embedded inside `<xs:appinfo>` — `:140`

Populates `role_types` with `{uri: {id, definition, used_on}}` from `<link:roleType>` elements.

**LabelsParser** (`edgar/xbrl/parsers/labels.py:20`)  
Populates the `.labels` dict on every `ElementCatalog` entry from `*_lab.xml`.

- `parse_labels_content(content: str) -> None` — XPath-extracts all `<link:label>` elements into a lookup table `{label_id: {lang: {role: text}}}`, then connects them to elements via `<link:labelArc>` arcs and `<link:loc>` hrefs; uses `sys.intern()` to deduplicate the ~10 recurring role URI strings — `:43`
- `get_element_label(element_id: str) -> str` — returns the `STANDARD_LABEL` role text or falls back to element ID — `:156`

Only `en-US` labels are stored into the catalog.

**PresentationParser** (`edgar/xbrl/parsers/presentation.py:19`)  
Builds a `PresentationTree` per `<link:presentationLink>` role.

- `parse_presentation_content(content: str) -> None` — iterates `<link:presentationLink>` elements, pre-builds a `loc_map` per link, extracts `<link:presentationArc>` attributes (from/to/order/preferredLabel), calls `_build_presentation_tree()` — `:51`
- `_build_presentation_tree(role, relationships) -> None` — finds roots (elements appearing as `from` but never as `to`), sorts for determinism (Issue #601), creates `PresentationTree`, calls `_build_presentation_subtree()` recursively — `:143`
- `_build_presentation_subtree(element_id, parent_id, depth, from_map, all_nodes) -> None` — creates `PresentationNode`, copies labels from `element_catalog`, calls `is_abstract_concept()` for abstract detection, recurses children sorted by `order`; deduplicates sibling arcs to the same concept (GH-825), exempting roll-forward arcs — `:190`

**Presentation arc dedup (GH-825):** Within `_build_presentation_subtree()`, a `seen_children` set tracks element IDs already processed under the current parent. A second arc to the same child is silently dropped (keeps lowest-`order` occurrence). Exception: arcs with `periodStart`/`periodEnd` preferred labels are never deduplicated because roll-forward statements require both occurrences (beginning and ending balance). See `ROLL_FORWARD_LABELS` constant in `parsers/presentation.py`.

Role `definition` prefers the human-readable string from `role_types` (populated by SchemaParser) over the URI-fragment fallback.

**CalculationParser** (`edgar/xbrl/parsers/calculation.py:17`)  
Builds a `CalculationTree` per `<link:calculationLink>` role; each arc carries a `weight` attribute (±1.0).

- `parse_calculation_content(content: str) -> None` — uses `findall` (not XPath) for `<link:calculationArc>`; extracts `weight` as float; resolves locators by attribute lookup — `:49`
- `_build_calculation_tree(role, relationships) -> None` — same root-finding as Presentation; creates `CalculationTree` — `:120`
- `_build_calculation_subtree(element_id, parent_id, from_map, all_nodes) -> None` — creates `CalculationNode` with `balance_type`/`period_type` from element catalog; tries alternative element ID format (colon vs underscore) if primary lookup fails — `:167`

**DefinitionParser** (`edgar/xbrl/parsers/definition.py:17`)  
Builds dimensional structures: `Table` (hypercubes), `Axis`, `Domain`.

- `parse_definition_content(content: str) -> None` — extracts `<link:definitionArc>` elements; requires `arcrole` attribute to be present — `:52`
- `_process_dimensional_relationships(role, relationships) -> None` — groups arcs by four arcrole URIs: `hypercube-dimension` → builds `axes` from to-element; `dimension-domain` → links `domain_id` onto axes; `domain-member` → populates `Domain.members`; `all` → creates `Table` with axes attached — `:122`

Arcroles used:
- `http://xbrl.org/int/dim/arcrole/hypercube-dimension`
- `http://xbrl.org/int/dim/arcrole/dimension-domain`
- `http://xbrl.org/int/dim/arcrole/domain-member`
- `http://xbrl.org/int/dim/arcrole/all`

**InstanceParser** (`edgar/xbrl/parsers/instance.py:22`)  
The largest parser (~850 lines). Extracts all runtime data from the instance document.

- `parse_instance_content(content: str) -> None` — parses with `huge_tree=True, recover=True`; calls in order: `_extract_contexts()`, `_extract_units()`, `_extract_facts()`, `_extract_footnotes()`, `_extract_entity_info()`, `_build_reporting_periods()` — `:84`
- `_extract_contexts(root) -> None` — handles `instant`, `duration`, `forever` period types; extracts `explicitMember` and `typedMember` dimensions into `Context.dimensions` — `:210`
- `_extract_units(root) -> None` — handles simple `<measure>` and `divide` (numerator/denominator measure lists) — `:293`
- `_extract_facts(root) -> None` — uses `root.nsmap` (lxml) for fast namespace prefix lookup; skips `context`, `unit`, `schemaRef`, `roleRef`, `arcroleRef`, `linkbaseRef` tags; handles duplicate facts by appending `_0`, `_1`, etc. to the base key — `:332`
- `_extract_footnotes(root) -> None` — prefers `xlink:label` over `id` attribute for footnote identification (pre-2016 filings naming inconsistency); handles XHTML content in divs — `:498`
- `_extract_entity_info() -> None` — collects all `dei:*` facts into `self.dei_facts`; populates `entity_info` dict from well-known DEI concepts; determines `reporting_end_date` as max instant date across contexts; parses `CurrentFiscalYearEndDate` in `--MM-DD` format — `:582`
- `_build_reporting_periods() -> None` — groups contexts by period key; classifies duration length via `classify_duration()`; sorts periods newest-first; calls `_enrich_periods_with_fiscal_info()` — `:669`
- `_enrich_periods_with_fiscal_info() -> None` — assigns `fiscal_year`/`fiscal_period` (`FY`, `YTD9`, `YTD6`, `Q1`–`Q4`) based on duration and fiscal year end — `:784`
- `_create_normalized_fact_key(element_id, context_ref, instance_id=None) -> str` — converts `prefix:name` to `prefix_name`; appends `_instance_id` for duplicates — `:56`
- `count_facts(content: str) -> tuple[int, int]` — fast pass without building Fact objects; returns `(unique_count, total_instances)` — `:113`

**StandardConcept** (`edgar/xbrl/standardization/core.py:34`)  
`str` enum with ~50 members representing canonical financial concept labels. Each member's value is the user-visible display string (e.g., `REVENUE = "Revenue"`). Keys in `concept_mappings.json` must match these values.

Class methods:
- `get_from_label(label: str) -> Optional[StandardConcept]` — reverse lookup by value — `:119`
- `get_all_values() -> Set[str]` — all display strings as a set — `:135`

**MappingStore** (`edgar/xbrl/standardization/core.py:145`)  
Loads and holds the three-tier concept mapping dataset.

- `__init__(source=None, validate_with_enum=False, read_only=False)` — resolves `concept_mappings.json` path (module-relative → `importlib.resources` fallback); loads core mappings, company mappings, creates merged priority list, loads hierarchy rules — `:156`
- `_load_mappings() -> Dict[str, Set[str]]` — handles both flat and nested-by-statement-type JSON formats — `:335`
- `_load_all_company_mappings() -> Dict[str, Dict]` — reads all `*_mappings.json` files from `company_mappings/` subdirectory (currently: `brka`, `msft`, `tsla`) — `:265`
- `_create_merged_mappings() -> Dict[str, List[Tuple[str, str, int]]]` — merges core (priority 1) and company (priority 2) into one dict with `(concept, source, priority)` tuples — `:283`
- `get_standard_concept(company_concept, context=None) -> Optional[str]` — three-tier: ReverseIndex first (O(1)), merged mappings second (priority-sorted), core mappings third — `:418`
- `get_display_name(company_concept, context=None) -> Optional[str]` — delegates entirely to `ReverseIndex.get_display_name()` — `:477`
- `add(company_concept, standard_concept) -> None` — adds to in-memory mapping; calls `_save_mappings()` (no-op if `read_only=True`) — `:404`
- `validate_against_enum() -> Tuple[bool, List[str]]` — checks JSON keys vs enum values — `:218`
- `to_dataframe() -> pd.DataFrame` — produces `standard_concept` / `company_concept` rows — `:242`

**ConceptMapper** (`edgar/xbrl/standardization/core.py:511`)  
Higher-level mapper with in-process cache, statement-type keyword filtering, and similarity inference.

- `__init__(mapping_store: MappingStore)` — pre-computes lowercased enum values and keyword sets for three statement types — `:521`
- `map_concept(company_concept, label, context) -> Optional[str]` — checks `(concept, statement_type, section)` cache first; delegates to `mapping_store.get_standard_concept()` — `:540`
- `_infer_mapping(company_concept, label, context) -> Tuple[Optional[str], float]` — label-based quick patterns, then `SequenceMatcher` similarity with statement-type filtering; returns `(concept, confidence)` — `:568`
- `learn_mappings(filings: List[Dict]) -> None` — batch inference; adds ≥0.9-confidence mappings immediately, queues 0.5–0.9 to `pending_mappings` — `:665`
- `save_pending_mappings(destination: str) -> None` — serializes pending mappings to JSON — `:713`

**ReverseIndex** (`edgar/xbrl/standardization/reverse_index.py:65`)  
The primary fast-path lookup. Loaded from `gaap_mappings.json` and `display_names.json`.

- `__init__(gaap_mappings_path=None, display_names_path=None)` — loads both JSON files; builds `_normalized_cache` for case-insensitive / namespace-stripped lookups; computes stats — `:89`
- `lookup(xbrl_tag, industry=None) -> Optional[MappingResult]` — checks `EXCLUDED_TAGS` first; normalizes tag; applies industry overrides; returns `MappingResult` dataclass with `standard_concepts`, `display_names`, `is_ambiguous`, `is_deprecated` — `:238`
- `get_standard_concept(xbrl_tag, context=None, log_ambiguous=False, industry=None) -> Optional[str]` — primary lookup method; for ambiguous tags calls `_disambiguate_by_context()` — `:289`
- `get_display_name(xbrl_tag, context=None, industry=None) -> Optional[str]` — display-name variant; disambiguates and resolves display name — `:510`
- `_normalize_tag(tag: str) -> Optional[str]` — strips `us-gaap:`, `us-gaap_`, `ifrs-full:`, `ifrs-full_`, `ifrs:`, `dei:` prefixes; case-insensitive cache lookup — `:168`
- `_apply_industry_override(entry, industry) -> dict` — merges `industry_overrides[industry]` dict into base entry; recalculates `ambiguous` flag — `:204`
- `_disambiguate_by_context(xbrl_tag, candidates, context) -> Optional[str]` — Phase 3/4 logic: prefers "total" concepts when `is_total=True`; tag-name hints for `noncurrent`/`current`; `SectionMembership` section matching via `_sections_match()` — `:370`

**MappingResult** (`edgar/xbrl/standardization/reverse_index.py:32`)  
Dataclass returned by `ReverseIndex.lookup()`.

Fields: `standard_concepts: List[str]`, `display_names: List[str]`, `is_ambiguous: bool`, `is_deprecated: bool`, `deprecated_year: Optional[str]`, `comment: Optional[str]`.

Properties: `primary_concept`, `primary_display_name`.

**SectionMembership** (`edgar/xbrl/standardization/sections.py:19`)  
Loaded from `section_membership.json`. Provides concept → section mapping to support disambiguation.

- `get_section(concept, statement_type=None) -> Optional[str]` — returns section name (e.g., `"Current Assets"`) — `:102`
- `get_statement_for_concept(concept) -> Optional[str]` — primary statement type for a concept — `:128`
- `is_current/is_asset/is_liability/is_equity(concept) -> Optional[bool]` — semantic helpers — `:192–273`

**StandardizationCache** (`edgar/xbrl/standardization/cache.py:15`)  
Per-XBRL-instance cache. Attached to an `XBRL` object as `.standardization`.

- `get_standard_label(concept, label, context=None) -> Optional[str]` — caches on `(concept, label, statement_type)` tuple — `:92`
- `standardize_statement_data(raw_data, statement_type, use_cache=False) -> List[Dict]` — calls `standardize_statement()` module function; statement-level caching off by default because raw_data varies by period/view — `:121`
- `set_industry_from_sic(sic_code) -> Optional[str]` — converts SIC → FF48 via `sic_str_to_fama_french()`; setting industry clears all cached results — `:66`
- `clear_cache(statement_type=None) -> None` — clears label and/or statement caches — `:165`

**UnmappedTagLogger** (`edgar/xbrl/standardization/unmapped_logger.py:105`)  
Diagnostic tool for mapping coverage expansion (Phase 5 of Issue #494).

- `log_unmapped(concept, label, **kwargs) -> None` — deduplicates by `concept:statement_type`; auto-suggests mappings via `_suggest_mapping()` — `:142`
- `log_ambiguous(concept, label, candidates, resolved_to, resolution_method, **kwargs) -> None` — deduplicates by `concept:section:resolved_to` — `:194`
- `save_to_csv(output_dir) -> tuple[int, int]` — writes `unmapped_tags.csv` and `ambiguous_resolutions.csv` — `:393`

---

### Class Hierarchy

```
BaseParser
├── SchemaParser
├── LabelsParser
├── PresentationParser
├── CalculationParser
├── DefinitionParser
└── InstanceParser

XBRLParser  (aggregates all six via composition)

# Standardization
StandardConcept(str, Enum)

MappingStore          (holds concept_mappings.json + company mappings)
ConceptMapper         (wraps MappingStore, adds cache + inference)

ReverseIndex          (wraps gaap_mappings.json + display_names.json)
  └── MappingResult   (dataclass, returned by lookup())

SectionMembership     (wraps section_membership.json)
StandardizationCache  (per-XBRL instance, wraps ConceptMapper + ReverseIndex)
UnmappedTagLogger     (standalone diagnostic tool)

# Data models (pydantic.BaseModel unless noted)
ElementCatalog        (plain class, not BaseModel)
Context               (BaseModel)
Fact                  (BaseModel)
Footnote              (BaseModel)
PresentationNode      (BaseModel)
PresentationTree      (BaseModel)
CalculationNode       (BaseModel)
CalculationTree       (BaseModel)
Axis                  (BaseModel)
Domain                (BaseModel)
Table                 (BaseModel)
XBRLProcessingError   (Exception)
```

---

### Configuration & Options

| Option | Type | Default | Effect |
|---|---|---|---|
| `XBRLParser.__init__()` | — | — | No args; all shared dicts initialized empty |
| `SchemaParser(element_catalog, role_types)` | `Dict, Dict` | `{}` | Injected shared references |
| `LabelsParser(element_catalog)` | `Dict` | — | Injected shared reference |
| `PresentationParser(…, role_types)` | Dict refs + `role_types` | `{}` | `role_types` from schema feeds human-readable definitions |
| `MappingStore(source, validate_with_enum, read_only)` | `Optional[str], bool, bool` | `None, False, False` | `source=None` → auto-locate `concept_mappings.json`; `read_only=True` skips disk writes |
| `ConceptMapper(mapping_store)` | `MappingStore` | — | Statement keyword sets pre-computed for filtering |
| `ReverseIndex(gaap_mappings_path, display_names_path)` | `Optional[str], Optional[str]` | module-dir files | Custom paths only needed for testing |
| `StandardizationCache(xbrl)` | `XBRL` | — | Industry initially `None` |
| `StandardizationCache.industry` | `Optional[str]` | `None` | Fama-French 48 code; setting it clears all caches |
| `ConceptMapper._infer_mapping` confidence thresholds | float | `≥0.9` auto-add, `0.5–0.89` pending, `<0.5` discard | Controls learning aggressiveness |
| `standardize_statement(…, industry)` | `Optional[str]` | `None` | Passes FF48 code to `ReverseIndex.get_standard_concept()` |
| `ElementCatalog.period_type` default | `str` | `"duration"` | Schema parser defaults if attribute absent |
| `lxml.XMLParser(huge_tree=True, recover=True)` | — | Instance parser only | Handles very large and malformed XBRL files |

---

### Data Flow / Lifecycle

**Parser layer (coordinator → six parsers):**

1. Caller instantiates `XBRLParser()` → six parsers created with injected shared dicts.
2. `parse_schema()` runs first. Populates `element_catalog` with name/type/period/balance/abstract and `role_types` with human-readable definitions. Forwards any embedded linkbases to the other parsers via stored callbacks.
3. `parse_labels()` runs next. Reads `*_lab.xml`, builds a `{label_id: {lang: {role: text}}}` lookup, uses arcs+locators to connect labels to element IDs, and mutates `element_catalog[id].labels`.
4. `parse_presentation()` reads `*_pre.xml`. For each `<link:presentationLink>` it builds a `PresentationTree` (root + `all_nodes: Dict[str, PresentationNode]`). Nodes carry `labels`, `depth`, `order`, `preferred_label`, `is_abstract`. Stored in `presentation_trees[role_uri]`.
5. `parse_calculation()` reads `*_cal.xml`. Builds `CalculationTree` per role with `CalculationNode` carrying `weight`/`balance_type`/`period_type`. Stored in `calculation_trees[role_uri]`.
6. `parse_definition()` reads `*_def.xml`. Uses arcrole URIs to classify arcs and populates `tables[role_uri]`, `axes[element_id]`, `domains[element_id]`.
7. `parse_instance()` runs last (depends on schema for namespaces, may cross-reference calculation_trees). Builds `contexts`, `units`, `facts`, `footnotes` in one traversal. Post-processing: `_extract_entity_info()` (DEI facts → entity_info), `_build_reporting_periods()` (dedup by date, classify duration, sort, enrich fiscal info).
8. After `parse_directory()` the coordinator exposes the unified data surface directly on `self.*` attributes.

**Standardization layer (per statement call):**

1. `standardize_statement(statement_data, mapper, industry)` is called per statement type.
2. First pass: for each non-abstract, non-dimension item, builds a `context` dict with `statement_type`, `level`, `is_total`, `calculation_parent`, `balance`, `weight`; derives `section` from `calculation_parent` via `_derive_section_from_parent()`.
3. `_assign_sections_bottom_up()` scans items bottom-to-top looking for level-0/1 totals whose labels match `subtotal_to_section` patterns; assigns `section` to all items above until the next subtotal.
4. Second pass: calls `reverse_index.get_standard_concept(concept, context, industry)` for each item. For ambiguous tags, `_disambiguate_by_context()` is tried first; falls back to first candidate.
5. Matching items get `standard_concept` key added (a mpreiss9 taxonomy concept ID like `"CommonEquity"`); non-matching items are returned unchanged (original labels preserved).
6. `StandardizationCache.get_standard_label()` caches `(concept, label, statement_type) → result` in memory. Statement-level caching (`use_cache=True`) is opt-in because input varies by period.
7. Module-level singletons (`_default_store`, `_default_mapper`, `_default_index`, `_default_membership`) are lazily initialized on first call, then reused for the process lifetime.

---

### Design Patterns

- **Composition over inheritance (parsers).** Each specialist parser extends `BaseParser` for shared XML utilities, but the coordinator uses composition: it holds all six as instance attributes, injecting shared dict references. No multi-inheritance.
- **Reference injection / shared mutable state.** All six parsers receive `dict` references pointing at the coordinator's own attributes. Writes by any parser are immediately visible to all others and to the caller without copying. This is the key performance mechanism.
- **Facade (coordinator).** `XBRLParser` exposes the original monolithic API surface while internally delegating to specialists. Callers need not know about the six sub-parsers.
- **Module-level singletons (standardization).** `_default_store`, `_default_mapper`, `_default_index`, `_default_membership` are process-lifetime singletons initialized lazily. Avoids repeated JSON file I/O on every statement call.
- **Reverse-index + three-tier fallback (standardization).** Lookup order: ReverseIndex (O(1) hash) → merged company+core priority lookup → core-only fallback. Fast path covers ~95% of US-GAAP tags; slower paths handle company-specific extensions.
- **Bottom-up section assignment.** Rather than requiring accurate calculation trees (which can be missing), `standardize_statement()` scans statement rows from bottom to top, uses subtotals as section boundary markers, and propagates sections upward. This is the mpreiss9 algorithm.
- **Priority scoring for company mappings.** Core mappings get priority 1; company-file mappings get priority 2; exact company-prefix match gets boosted to priority 4 at lookup time.
- **sys.intern for label role URI deduplication.** `LabelsParser` interns the ~10 recurring role URI strings to save memory across large filings — `:73–82`.
- **Deterministic tree ordering.** Both `PresentationParser` and `CalculationParser` sort root elements from set subtraction using `sorted()` to prevent hash-randomization-driven non-determinism across processes (Issue #601).
- **Hybrid fact key scheme for duplicates.** Base key `element_id_context_ref`; on collision, existing fact is moved to `element_id_context_ref_0` and new fact to `element_id_context_ref_1`. `get_facts_by_key()` tries base key then iterates instance IDs.

---

### Cross-Domain Interactions

**What this domain imports from other edgar.* modules:**

- `edgar.core.log` — used by all parsers for debug/warning logging
- `edgar.xbrl.core.NAMESPACES` — shared namespace URI constants
- `edgar.xbrl.core.extract_element_id`, `classify_duration`, `STANDARD_LABEL` — utility functions
- `edgar.xbrl.core.STANDARD_TAXONOMIES` — frozenset of known taxonomy prefixes (`us-gaap`, `dei`, `srt`, `ifrs-full`, etc.); used by `calculation_linkbase()` and `Statement.extension_arcs()` to distinguish filer extensions from standard concepts — `core.py:20`
- `edgar.xbrl.core.split_element_id(element_id)` — splits `us-gaap_Revenues` → `('us-gaap', 'Revenues')` on first `_`; handles hyphenated prefixes correctly — `core.py:27`
- `edgar.xbrl.models.*` — all data model classes (`ElementCatalog`, `Context`, `Fact`, `Footnote`, `PresentationNode/Tree`, `CalculationNode/Tree`, `Axis`, `Domain`, `Table`, `XBRLProcessingError`)
- `edgar.xbrl.abstract_detection.is_abstract_concept` — called from `PresentationParser._build_presentation_subtree()` to enhance abstract detection beyond schema flag

**What consumes these parsers:**

- `edgar.xbrl.xbrl.XBRL` — instantiates `XBRLParser`; exposes `.facts`, `.contexts`, `.presentation_trees`, etc.; attaches `StandardizationCache` as `.standardization`
- `edgar.xbrl.statements.Statement` — reads presentation trees and facts to build statement rows
- `edgar.xbrl.facts.FactsView` — queries the `facts` dict built by `InstanceParser`
- `edgar.xbrl.models.select_display_label()` — calls `get_default_store().get_standard_concept()` when no company-preferred label is available
- `edgar.xbrl.stitching.*` — reads `calculation_trees` and `facts` for multi-filing stitching

**What the standardization layer imports from parsers:**

- `edgar.xbrl.standardization.core` imports nothing from parsers at module level; circular-import guards are in place via lazy imports inside methods
- `StandardizationCache` imports `XBRL` only in `TYPE_CHECKING` block

---

### Gotchas & Notable Behaviors

**Parser layer:**

- Schema must parse before labels, presentation, calculation, definition. Instance must parse last. `parse_directory()` enforces this order; callers invoking individual `parse_*` methods must respect it manually.
- `SchemaParser` accepts linkbases embedded directly inside `<xs:appinfo>` in the XSD file. This path is common in older and some newer SEC filings. The `set_linkbase_parsers()` call from coordinator is mandatory before `parse_schema_content()` can forward embedded linkbases; the coordinator does this in `_init_parsers()`.
- `InstanceParser` uses `lxml`'s `root.nsmap` for prefix resolution (fast). If lxml is unavailable it falls back to regex-extracting namespace declarations, which is slower.
- Duplicate facts (same element + context in one filing) are handled via the `instance_id` mechanism. The base key stores the first fact; on duplicate the first is moved to `_0` and subsequent get `_1`, `_2`, etc. Both `get_fact()` and `get_facts_by_key()` are aware of this.
- Footnote identification uses `xlink:label` (not `id`) because pre-2016 filings inconsistently name them; arcs reference `xlink:label` values.
- `_extract_entity_info()` reads `reporting_end_date` as the maximum instant date across all contexts (not a DEI fact), which can differ from `DocumentPeriodEndDate`.
- `CurrentFiscalYearEndDate` is expected in `--MM-DD` or `MM-DD` format (ISO 8601 partial date). Parse failure is silently swallowed.
- 52/53-week filers pin quarter end dates to a weekday near the nominal date. `_quarter_for_date()` compensates: if `end_date.day <= 7` it treats the end date as belonging to the prior month before computing quarter offset (Issue #816).
- Period classification thresholds: FY = 350–380 days, YTD9 = 260–290, YTD6 = 170–200, Q1–Q4 = 85–95.
- `CONSISTENT_POSITIVE_CONCEPTS` and `LEGITIMATE_NEGATIVE_CONCEPTS` in `concepts.py` are deprecated (Issue #463). Raw SEC XBRL values are already sign-consistent; these lists fixed symptoms of a misapplied calculation-weight sign flip that no longer exists.
- The `US_GAAP_BALANCE_TYPES` dict in `concepts.py` covers ~100 common concepts; `get_balance_type()` normalizes `us_gaap_X` / `us-gaap_X` / `us-gaap:X` forms before lookup.

**Standardization layer:**

- `gaap_mappings.json` contains ~2,067 US-GAAP tag entries with fields `standard_tags`, `display_name`, `ambiguous`, `deprecated`, `comment`, and optional `industry_overrides` / `section` / `is_total` metadata.
- `display_names.json` is a fallback for standard-concept-to-display-name resolution; `gaap_mappings.json` embedded `display_name` fields take precedence for non-ambiguous entries.
- `EXCLUDED_TAGS` has 276 entries (EPS details, per-share metrics, OCI line items, pro-forma metrics). `should_exclude()` strips namespace prefix before checking the set. Two entries were explicitly removed from exclusions to support cash flow stitching: `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` and `IncomeLossFromContinuingOperationsIncludingPortionAttributableToNoncontrollingInterest`.
- Industry overrides in `gaap_mappings.json` use Fama-French 48 codes (e.g., `"Banks"`, `"Chips"`, `"Autos"`). `sic_to_fama_french()` maps 4-digit SIC codes to FF48 codes using binary range scan; result is `lru_cache(maxsize=256)` cached.
- Company mapping files live in `edgar/xbrl/standardization/company_mappings/` as `{ticker}_mappings.json`. Currently bundled: `brka`, `msft`, `tsla`. Each file contains `metadata` + `concept_mappings` + optional `hierarchy_rules`.
- `standardize_statement()` adds `standard_concept` (mpreiss9 concept ID) to each row but never replaces the original label. Callers use `standard_concept` for cross-company grouping.
- `_should_preserve_label()` (called from label selection in models.py) skips standardization when the original label contains qualifiers like `"other "`, `", net"`, `"long-term"`, `"current"` that would be lost in the standard label — prevents over-generalization.
- `StandardizationCache.use_cache=False` is the default for `standardize_statement_data()` because the raw_data input varies by period/view parameters even for the same statement type. Enable explicitly only when the caller guarantees consistent input.
- `MappingStore` in `read_only=True` mode (used by the module singleton) never writes to disk; `add()` is accepted in-memory but `_save_mappings()` is a no-op.
- `_detect_entity_from_concept()` infers entity by splitting on `_` and checking if the prefix appears in `company_mappings`. This fires a priority-4 boost for exact entity matches.
- `ConceptMapper._cache` keyed on `(concept, statement_type, section)` not just concept, enabling context-sensitive disambiguation to produce different results for the same tag in different contexts.
- `UnmappedTagLogger` deduplicates by `concept:statement_type` (unmapped) and `concept:section:resolved_to` (ambiguous). The module-level singleton `_default_logger` is never automatically enabled; callers must opt in by passing `log_ambiguous=True` to `ReverseIndex.get_standard_concept()`.
