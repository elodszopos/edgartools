# edgar-sidecar -- LLM architecture reference

Stateless FastAPI wrapper around edgartools. Single SEC egress. Pydantic models -> OpenAPI -> generated Zod.

## File layout

| Path | Purpose |
|------|---------|
| `app/main.py` | FastAPI app, router registration |
| `app/routers/` | Endpoint handlers (thin -- delegate to converters) |
| `app/models/filing.py` | `FilingEnvelope`, `FilingData` discriminated union (all 25 form types) |
| `app/models/forms/<form>.py` | Per-form wire model (WireModel subclass, `kind` Literal discriminator) |
| `app/models/common.py` | Shared types: `WireModel`, `Address`, `DocumentRef`, CIK/accession patterns |
| `app/models/financials.py` | Statement/facts response models |
| `app/converters/filing.py` | `_DATA_BUILDERS` dispatch map (form list -> converter function), `filing_envelope()` |
| `app/converters/forms/<form>.py` | Per-form converter: edgar object -> wire model, explicit field-by-field |
| `app/converters/forms/offering.py` | Shared offering legs (fee_table, selling_stockholders, underwriting, dilution, capitalization) |
| `app/converters/financials.py` | Statement/facts/metrics converters |
| `app/serialize.py` | Coercion policy: `to_str`, `to_float`, `to_int`, `to_iso_str`, `to_date` |
| `app/cik.py` | `pad_cik()` -- zero-pad to 10 digits |
| `app/sgml_series.py` | SGML SERIES-AND-CLASSES-CONTRACTS-DATA parser (N-CSR) |
| `openapi.json` | Committed snapshot (snapshot test enforces match) |
| `ts/src/generated/zod.ts` | Generated Zod from OpenAPI via orval |
| `ts/tests/goldens.test.ts` | Every golden strict-parsed against Zod -- the TS validation backbone |
| `ts/fixtures/responses/` | Golden JSON files by endpoint |
| `tests/integration/` | Per-form integration + parity tests |
| `tests/conftest.py` | `data_surface()`, `golden()` fixture, SEC replay wiring |
| `tests/sec_replay.py` | URL-keyed SEC fixture store (replay default, record via `EDGAR_FIXTURE_RECORD=1`) |
| `tests/fixtures/sec/` | SEC replay files (one per URL, git-lfs tracked) |
| `scripts/export_openapi.py` | Regenerate `openapi.json` from app |
| `scripts/check_drift.sh` | Gate: regen openapi + zod, assert no diff |

## The typed-form pattern (P4)

Every form follows this pipeline:

```
edgar obj() -> converter (field-by-field) -> WireModel (Pydantic) -> FilingData union -> openapi -> zod -> golden
```

### Adding a new form

1. **Model**: `app/models/forms/<form>.py` -- `class <Form>Data(WireModel)` with `kind: Literal["<kind>"] = "<kind>"`
2. **Converter**: `app/converters/forms/<form>.py` -- `def <form>_data(obj) -> <Form>Data`, explicit field-by-field using `to_str`/`to_float`/`to_iso_str`
3. **Dispatch**: `app/converters/filing.py` -- add `(["FORM-TYPE"], <form>_data)` to `_DATA_BUILDERS`
4. **Union**: `app/models/filing.py` -- add `| <Form>Data` to `FilingData`
5. **Parity test**: `tests/integration/test_<form>_parity.py` -- `data_surface(obj)` must equal wire model fields
6. **Integration test**: `tests/integration/test_<form>.py` -- endpoint assertions + `golden()` calls
7. **Regen**: `uv run python -m scripts.export_openapi && cd ts && bun run generate`
8. **Verify**: `bash scripts/check_drift.sh`

### Parity gate mechanics

`data_surface(obj)` in `tests/conftest.py` introspects the edgar object:
- Filters: methods, classmethods, DataFrames, private attrs (`_`), edgar-module objects (unless dataclass or Enum)
- Returns: set of attribute names whose values are scalars, lists, dataclasses, or Enums
- Blind spot: Pydantic BaseModel instances from edgar modules are filtered -> use `_STRUCTURAL` guard for those

Parity test anatomy:
- `_RENAMES`: edgar attr name -> wire field name (when renamed)
- `_SPLITS`: one edgar attr -> multiple wire fields (e.g. `non_derivative_table` -> `holdings` + `transactions`)
- `_RAW_SOURCE`: edgar attrs excluded from wire (raw HTML/text blobs, not parsed output)
- `_EXCLUDE`: backing stores (e.g. `primary_doc` on NPX, `effectiveness_data` on Effect)
- `_STRUCTURAL`: nested fields invisible to data_surface -- explicit guard test checks they exist on the wire model

## Coercion policy

| Function | Input | Output | Rule |
|----------|-------|--------|------|
| `to_str(v)` | any | `str \| None` | `str(v).strip()`, empty -> None |
| `to_float(v)` | Decimal/float/str | `float \| None` | None/NaN -> None |
| `to_int(v)` | numeric | `int \| None` | None -> None |
| `to_iso_str(v)` | date/datetime/str | `str \| None` | ISO 8601 string |
| `to_date(v)` | date/datetime/str | `date \| None` | Python date object |

## Form kind -> model file

| kind | Model file | Edgar class |
|------|-----------|-------------|
| `ownership` | `forms/ownership.py` | `Ownership` |
| `form8k` | `forms/eightk.py` | `EightK` |
| `form6k` | `forms/sixk.py` | `SixK` |
| `form10k` | `forms/tenk.py` | `TenK` |
| `form10q` | `forms/tenq.py` | `TenQ` |
| `form20f` | `forms/twentyf.py` | `TwentyF` |
| `form40f` | `forms/fortyf.py` | `FortyF` |
| `form13f` | `forms/thirteenf.py` | `ThirteenF` |
| `form144` | `forms/form144.py` | `Form144` |
| `formd` | `forms/formd.py` | `FormD` |
| `formc` | `forms/formc.py` | `FormC` |
| `proxy` | `forms/proxy.py` | `ProxyStatement` |
| `sc13d` | `forms/schedule13.py` | `Schedule13D` |
| `sc13g` | `forms/schedule13.py` | `Schedule13G` |
| `registration_s1` | `forms/registration_s1.py` | `RegistrationS1` |
| `registration_s3` | `forms/registration_s3.py` | `RegistrationS3` |
| `drs` | `forms/drs.py` | `DraftRegistrationStatement` |
| `prospectus_424b` | `forms/prospectus_424b.py` | `Prospectus424B` |
| `prospectus_497k` | `forms/prospectus_497k.py` | `Prospectus497K` |
| `nport` | `forms/nport.py` | `FundReport` |
| `nmfp` | `forms/nmfp.py` | `MoneyMarketFund` |
| `ncen` | `forms/ncen.py` | `FundCensus` |
| `ncsr` | `forms/ncsr.py` | `FundShareholderReport` |
| `npx` | `forms/npx.py` | `NPX` |
| `effect` | `forms/effect.py` | `Effect` |

## Rules

- `edgar/` is READ-ONLY for sidecar work -- never patch core
- No file creation (goldens and SEC fixtures are the exception -- those are test artifacts)
- No hand-maintained exclusion lists -- if parity fails, map the field
- Generated artifacts (openapi.json, zod.ts) require explicit user authorization to regenerate
- SEC fixtures: replay by default, record via `EDGAR_FIXTURE_RECORD=1` within budget
- Commit messages: no destructive words (delete, remove, prune) -- use neutral alternatives
