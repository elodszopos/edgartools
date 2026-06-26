# edgar-sidecar — full edgartools HTTP wrapper

> Self-sufficient FastAPI sidecar inside this fork. Wraps the LOCAL `edgar` package as the single SEC egress.
> Full-fidelity Pydantic per form data object -> OpenAPI 3.1 -> generated Zod, committed here. Pluggable into any stack (knowledge-distiller is the first consumer — it wires this in itself; THIS plan never writes outside this repo).
> Status: ACTIVE. Loop-executable: each session runs the Session Protocol below.
> Supersedes (stale, background only): KD `.claude/plans/edgar-service.md`, secret-project `.claude/plans/edgar-service.md`.

## Why (v1 + v1.5 postmortem — what must never recur)

| sin | This plan's answer |
|---|---|
| v1: `clean()`/`_dump_obj` attribute-walking -> silent field drops | Explicit Pydantic models; per-form parity gate fails on any unmapped field |
| v1: Manual concept maps (`XBRL_TAG_ALIASES`, `BS_MAP`/`IS_MAP`/`CF_MAP`, sign sets) | Expose edgartools standardized statements + scalar getters + TTM directly |
| v1: Hand-written Zod (94 transforms, 1873 defaults) kept aligned by drift test | Zod GENERATED from OpenAPI; regen+diff gate; consumers re-built against generated shapes |
| v1: Half-bridge: TS kept discovery + XML parsers | Sidecar owns 100% of SEC I/O; typed `data` for every investor-relevant form |
| v1: Cross-process Redis rate limiter + promise chains | Single egress; edgartools-native throttle only |
| v1.5: 530 hand-maintained `_CAPTURED`/`_EXCLUDED`/`_SERVED_ELSEWHERE`/`_ENVELOPE`/`_CLASS_LEVEL` entries across 20 parity tests | Parsed structured data inline. No hand-maintained field sets of any kind. Parity test: `data_surface(obj)` == wire model fields. If it fails, map the field. |
| v1.5: Form data split across 5+ endpoints with exclusion tracking | Parsed structured data inline in one response. Heavy parsed content (financial statements, full text sections) at separate endpoints -- same as calling a lazy property in edgar. No raw HTML ever. |
| v1.5: 776-line rewrite of edgar/financials.py disguised as "bug fix" | Surgical upstream fixes only: ~4 lines per method, reusing existing infrastructure. |

## Hard constraints

- KD repo (`~/Projects/knowledge-distiller`) and secret-project are READ-ONLY. Never write/run anything there. Mining v1 fixture accession numbers (read) is allowed.
- All work in THIS fork, branch `main`, additive: new top-level `sidecar/` + this plan ONLY.
- **`edgar/` IS STRICTLY READ-ONLY. NEVER patch, rewrite, regenerate, or "tame" core — no exceptions.** On a suspected edgar bug: STOP the unit, surface it, and discuss with the user before anything; default assumption is my own bug (99% of the time). A genuine gap is handled ADDITIVELY in the `sidecar/` layer, never in `edgar/`. Do NOT build regeneration/justification machinery (base snapshots, correction overlays, generators, "generated artifact" docstrings) around core files — that is core surgery in disguise. (Enforced after the v1.5 incident: a campaign rewrote ~68% of `gaap_mappings.json` and added a regen pipeline; all of it was purged.)
- No file deletion ever (user rule). Use `mv` if relocation needed.
- SEC traffic only via the recording protocol below. Tests replay fixtures offline.
- Stateless service: no DB, no Redis, no cron, no auth (single consumer on compose network).

## Loop-session rules (unattended operation)

- **Subagents: read-only research only (user lifted full ban, 2026-06-12).** Explore-type spawns for pre-reading edgar source / form docs for the NEXT unit or group are allowed; spawned agents must never write files, record SEC interactions, or commit. Spawn prompts must satisfy the context-injection hook. A failed or stalled spawn must NEVER block the loop — fall back to working directly, immediately. All implementation work stays in the main session.
- **Standing authorization.** This plan pre-approves, inside this repo only: the quality-gate commands, `sidecar/scripts/*`, pytest (incl. fixture recording via `EDGAR_FIXTURE_RECORD=1` within the SEC budget), codegen, `uv`/`bun` installs scoped to `sidecar/`, and `git add`/`git commit`. Anything outside that set (pushes, KD writes, library rewrites, new external services) -> `blocked(user)`.
- **Precedence.** For `sidecar/` work this plan supersedes the fork's `CLAUDE.md` workflow ceremony (beads issue tracking, triage commands — skip them). `edgar/` is never edited (read-only), so no question of editing-style there arises — a suspected core bug halts the unit for discussion instead.
- **Anti-spin halt.** If no executable unit remains (everything `done`/`blocked`), or an iteration ends with zero state change twice in a row, append `HALT <reason>` to the Log, commit, and END the loop — do not idle-reschedule.
- **Context discipline.** If a unit outgrows the session, finish the smallest coherent slice, commit it, set `in-progress`, and write the exact next action into the Log line so the next iteration resumes without re-deriving.
- Outside this repo, read ONLY the named v1 fixture-mining path. Never read/write KD.
- **Within-repo API authorization (standing).** FULL authorization for SEC API interactions within rate limits and for everything inside this repo. Docker: the sidecar's own image/containers only — touching ANY other running container is strictly forbidden.
- **Anti-overengineering (HARD RULE).** The sidecar is a pass-through wrapper for edgar's parsed output. Two kinds of data:
  - **Parsed structured data** (scalars, lists, nested objects from `filing.obj()`) -- goes inline in the JSON response. This is the sidecar's entire value.
  - **Heavy parsed content** (financial statements from XBRL, full text of sections like Business/MD&A/Risk Factors) -- separate API endpoint, same as calling a lazy property in Python. The consumer calls it when they need it.
  - **Raw HTML** -- never. Edgar does the parsing. SEC.gov serves raw HTML. The sidecar serves parsed results.
  No hand-maintained field sets of any kind. No `_CAPTURED`, `_EXCLUDED`, `_SERVED_ELSEWHERE`, `_ENVELOPE`, `_CLASS_LEVEL`, `_SKIP`, `_NESTED_IN_FUNDS` -- ALL of these are exclusion lists by different names. If a parity test fails because a field isn't on the wire, the fix is to map it. Complexity is a bug.

## Launch (zero manual setup)

One command from anywhere: `~/Projects/edgartools/sidecar/loop.sh` — zero prerequisites.
- `SEC_EDGAR_USER_AGENT` is hardcoded in the launcher (contact string, not a credential — same plaintext value as v1's `.env.tpl`).
- Starts `claude` anchored in the fork root with the /loop prompt baked in.
- Fork `.claude/settings.json` pre-allows comet + context7 MCP (the U03 research tools missing from global allows); Bash/Edit/Write under `~/Projects/**` are already globally allowed, so loop iterations never hit a permission prompt.
- Fork `.claude/settings.json` env sets `CLAUDE_CODE_AUTO_COMPACT_WINDOW=300000`: loop sessions auto-compact at 300k context tokens (user request 2026-06-12; per-N-iterations compaction is not supported by Claude Code — hooks cannot trigger compaction and agents cannot invoke built-in /compact).

## Layout

```
sidecar/
  loop.sh                 # overnight-loop launcher (hardcoded SEC identity fallback, env-overridable; /loop prompt baked in)
  pyproject.toml          # name edgar-sidecar; deps: edgartools (editable ../), fastapi, uvicorn[standard], numpy/pandas/pyarrow/orjson; dev: pytest, httpx, pyyaml, ruff, pyright
  uv.lock                 # resolved dependency lock; Dockerfile installs via uv sync --frozen
  openapi.json            # exported OpenAPI 3.1 snapshot (zod codegen source + snapshot test)
  app/
    main.py               # FastAPI app, identity boot (fail without SEC_EDGAR_USER_AGENT), router wiring
    settings.py           # env vars table below
    cik.py                # CIK pad/parse helpers
    errors.py             # exception -> HTTP status mapping
    serialize.py          # JSON policy: numpy->int/float, Decimal->float, date->ISO, NaN/NaT->null, DataFrame -> typed records via explicit converters ONLY
    models/               # Pydantic wire models: common, company, filing, filings, financials, search, tickers
    converters/           # edgartools object -> model, explicit field-by-field: company, filing, filings, financials, search, tickers
    routers/              # company, filing, filings, financials, health, search, tickers
  tests/
    conftest.py           # offline-replay wiring + shared fixtures
    sec_replay.py         # URL-keyed SEC fixture store + httpx replay transport (offline by default)
    fixtures/sec/         # recorded SEC responses keyed by host/path (decoded body + .meta.json sibling)
    unit/                 # pure-helper tests (cik, serialize, errors, search params, openapi snapshot, fixture store)
    integration/          # per-router endpoint tests (FastAPI TestClient)
  ts/                     # bun project: zod pinned, eslint, orval.config.ts; src/generated/ (codegen output, do-not-edit), fixtures/responses/<endpoint>/<case>.json (goldens), tests/ validate every golden against generated Zod
  scripts/
    export_openapi.py     # app -> openapi.json (committed snapshot)
    generate_zod.sh       # openapi.json -> ts/src/generated/ (orval, picked in U03)
    check_drift.sh        # regen openapi + zod + goldens-schema pass; git diff --exit-code
    decompose_cassettes.py # one-off CLI: decompose VCR cassettes into the URL-keyed fixtures/sec store
  Dockerfile              # python:3.12-slim, non-root, uvicorn app.main:app, HEALTHCHECK /health
  compose.yaml            # reference service block: name edgar, port 8000, env, optional edgar-cache volume
```

| Env | Default | Purpose |
|---|---|---|
| `SEC_EDGAR_USER_AGENT` | required | `set_identity()`; boot fails without it |
| `EDGAR_RATE_LIMIT_PER_SEC` | 8 | edgartools-native throttle |
| `EDGAR_PORT` | 8000 | uvicorn |
| `EDGAR_LOCAL_DATA_DIR` / `EDGAR_USE_LOCAL_DATA` | optional | edgartools disk cache volume |

Tooling: `uv`-managed venv at `sidecar/.venv`, Python 3.12 (matches container). Local `edgar` as editable path dep (`uv add --editable ../`). All deps exact-pinned. Run locally: `uv run uvicorn app.main:app`. TS side: bun, deps exact-pinned.

## Wire conventions

- `id` params accept ticker or CIK; all returned CIKs 10-digit zero-padded strings.
- Dates ISO `YYYY-MM-DD`. Numbers float/int, never NaN. Absent -> `null`, never dropped keys.
- Paging: `start`/`page_size` in, `has_more`/`next_start` out.
- `FilingEnvelope.data`: Pydantic discriminated union on `kind` literal (one member per typed form) -> Zod `discriminatedUnion`. `obj_type` = edgartools class name. Envelope-only forms: `data=null`.
- Errors: FastAPI `{detail}`; 404 not-found-at-SEC, 422 bad params, 429 SEC limit, 502 edgartools/SEC upstream error, 503 starting/identity unset.

## Endpoint surface

Edgar has X, sidecar has X. The sidecar serves edgar's parsed output -- never raw HTML, never invented interfaces.

**Inline data** (parsed structured fields from `filing.obj()`):

| Endpoint | edgar call | What you get |
|---|---|---|
| `GET /filing/{accession}` | `Filing(accession)` + `filing.obj()` | Filing envelope + all parsed structured data from the form object |
| `GET /filings` | `get_filings(form=, cik=, ...)` | Filing list with paging |
| `GET /filings/current` | `current_filings.py` | RSS current filings |
| `GET /search` | `efts_search(q=)` | EFTS full-text search |
| `GET /company/{id}` | `Company(id)` | Company info + submissions |
| `GET /tickers` | `reference/tickers.py` | Ticker reference data |
| `GET /health` | -- | Status, edgartools version, identity_set |

**Heavy parsed content** (separate call -- mirrors calling a lazy property in Python):

| Endpoint | edgar call | What you get |
|---|---|---|
| `GET /filing/{accession}/xbrl` | `filing.xbrl()` | Parsed XBRL financial statements for this filing |
| `GET /filing/{accession}/sections` | `filing.sections()` | Parsed text sections (Business, MD&A, Risk Factors, etc.) |
| `GET /filing/{accession}/attachments` | `filing.attachments` | Document list + content |
| `GET /company/{id}/financials` | `company.get_financials()` | Company-level statements (annual/quarterly/multi/ttm/metrics) |
| `GET /company/{id}/facts` | `company.get_facts()` | Entity facts (+concept, +search) |

**Filing envelope `data`**: discriminated union on `kind` literal. One typed member per form. `filing.obj()` gives you a parsed form object -- the sidecar serializes all its parsed structured fields. Heavy content (financials, full text, documents) is at its own endpoint, just like calling a lazy property in Python triggers a separate load.

Statement shape: typed `values[]` records (`concept`, `label`, `preferred_sign`, `values[{period_label, period_end, period_type, value}]`).

## Typed form coverage (end state)

Investor set — full-fidelity models: Form 3/4/5 · 8-K · 6-K · 10-K · 10-Q · 20-F · 40-F · SC 13D/13G · 13F-HR · 144 · D · C (+C-U/AR/TR) · proxy family (DEF 14A et al.) · S-1 · S-3 family · 424B family · DRS · 497K · NPORT-P/EX · N-MFP · N-CEN · N-CSR · N-PX · EFFECT · 10-D (CMBS).
Envelope-only (typed later only if ever needed): CORRESP/UPLOAD, ATS-N family, MA/MA-I/MA-W, TA-*, SBSE, CFPORTAL, X-17A-5, 24F-2NT.

**The one rule: edgar parses it, sidecar serves the parse.** `filing.obj()` returns a parsed form object. Every parsed structured field goes inline in the `data` blob. Heavy content (XBRL statements, full section text, raw documents) goes at a separate endpoint -- the HTTP equivalent of calling a lazy property in Python. No hand-maintained field sets. No exclusion lists by any name. If a parity test fails, the fix is to map the field. Structural transforms allowed: renames, compound splits (e.g. `non_derivative_table` -> holdings + transactions). No raw HTML ever -- edgar does the parsing.

## Codegen pipeline

1. Pydantic -> `scripts/export_openapi.py` -> committed `sidecar/openapi.json` (snapshot test).
2. `generate_zod.sh` -> `ts/src/generated/` with do-not-edit header, committed.
3. Drift gate: `check_drift.sh` = regenerate both + `git diff --exit-code` + bun test green. Run in every unit's verify step.
4. Tool picked in U03 against criteria: OpenAPI 3.1 in, discriminated unions -> `z.discriminatedUnion` (or acceptable equivalent), deterministic output, maintained. Candidates: `openapi-zod-client`, `orval`, `kubb`, `typed-openapi`. Zod 3 vs 4: WHATEVER the best tool emits (user decision — do not block on this). Use comet_ask for current tool state; if comet is unavailable, evaluate by installing candidates against the U03 spec sample directly.
5. If NO tool meets the criteria: mark U03 `blocked(user)` with the evidence table. Do NOT hand-roll a generator — that is a user decision.

## Test architecture (the centerpiece)

| Leg | What | How |
|---|---|---|
| Python integration | endpoint -> JSON correct per fixture | pytest + URL-keyed SEC fixture store (`sec_replay.py`): replay is default and offline, recording via `EDGAR_FIXTURE_RECORD=1`. FastAPI `TestClient`; assertions on real values, not just shape |
| Field-parity gate | no field ever forgotten | per form: `data_surface(obj)` auto-filters methods/classmethods. Every remaining field must be on the wire model. No hand-maintained exclusion sets of any kind. Failure = map the field. |
| TS end-to-end | generated Zod accepts every real response | Python tests dump each response JSON as golden -> `ts/fixtures/responses/` -> bun test parses ALL goldens with generated Zod (strict) |
| Live smoke | true SEC round-trip | tiny opt-in suite, `@pytest.mark.live`, excluded by default |
| Unit | pure helpers only (CIK pad, period-type, serialize policy) | plain pytest |

Replay wiring (`sec_replay.py`, replaces vcrpy): a session-scoped fixture patches `httpx.HTTPTransport`/`AsyncHTTPTransport` so every SEC request resolves to the store — one file per URL under `tests/fixtures/sec/<host>/<path>` (decoded body + sibling `.meta.json`), edgartools' disk cache + rate limiter disabled so the store is the sole arbiter. Default is replay: a miss is a hard `FixtureMissError` naming the URL, never a silent fetch.

Golden lifecycle: goldens are written once at fixture creation, committed, then asserted byte-equal on every run. Intentional regeneration ONLY via `GOLDEN_UPDATE=1` with the diff explained in the commit message. `check_drift.sh` validates committed goldens against freshly regenerated Zod. **NEVER regenerate goldens, openapi.json, or generated zod without explicit user authorization. Agents MUST NOT run GOLDEN_UPDATE=1 or any regen script. This is a HARD RULE -- violation overwrites ground-truth values with potentially wrong data.**

Target: hundreds of cases = per typed form 5-15 real accessions x (model + parity + golden-Zod) + financials across ticker classes (mega-cap, REIT, bank, IFRS/ADR e.g. INFY, fund) + discovery/search/content cases.

### SEC recording budget (HARD RULES for unattended runs)

- Record only inside a unit's fixture step (`EDGAR_FIXTURE_RECORD=1`): pass through to real SEC, persist, then serve; edgartools' native throttle stays on. Bounded: `RECORD_BUDGET=60` NEW fixture files per run (enforced in `sec_replay._capture`).
- Replay is the default and offline: existing fixtures never re-hit SEC; a run that records no new URL touches no network.
- Any 429: stop recording immediately, mark unit `blocked(rate)`, continue with non-network work.
- Never run unbounded sweeps (no "fetch all filings since X" without `limit`).
- Large fixtures tracked by git-lfs (`.gitattributes` tracks `sidecar/tests/fixtures/sec/**/*.txt`). Pick whatever filings make the best tests. Prefer smaller filings when they exercise the same code paths -- a 5MB bank 10-K tests the same logic as JPMorgan's 52MB one.
- Edge-case accession numbers: mine read-only from `~/Projects/secret-project/tests/fixtures/kd/edgar/` (682 Form4, 922 13D, 576 13F, 2100+ 8-K) + fork `docs/*.md` + EFTS search.

## Quality gates (every unit, before `done`)

```
cd sidecar && ruff check --fix . && ruff format .        # fork's ruff
pyright --project .                                       # MUST be --project . from sidecar/; bare `pyright`/`pyright sidecar/` silently loads the PARENT pyrightconfig.json (include=["edgar"], no venv) and checks ZERO sidecar files. Clean == "0 errors". See memory: sidecar-pyright-gate-invocation
pytest sidecar/tests -q -m "not live"
./sidecar/scripts/check_drift.sh                          # openapi + zod regen clean
cd sidecar/ts && bunx eslint --fix src tests && bun test
```

Commit per unit on green: `git add <unit files> && git commit -m "sidecar: U## <scope>"`. Neutral wording in messages (no delete/remove/prune words). Never `git push`.

## Session Protocol (each /loop iteration)

1. `cd ~/Projects/edgartools`. Read THIS file fully. Read fork `CLAUDE.md` if first touch this session.
2. Pick unit: first `in-progress`, else first `todo` in table order. Replay needs no identity; recording uses the exported SEC contact (`loop.sh` provides the bundled one). A recording unit that can't reach SEC (429/offline) -> `blocked(rate)` + next unit.
3. Set unit state `in-progress` (edit Units table only).
4. Execute per the Form Unit Recipe (form units) or the unit's scope line (infra units). A unit too big to finish in one iteration: split into `U##a/U##b` rows in the table, finish the first.
5. Run ALL quality gates. Green -> state `done`, append one Log line, commit. **Log line format (HARD RULE — no exceptions): `U## | done | <architecture + cross-unit gotchas ONLY>`. Record ONLY: structural decisions (model/kind/dispatch/layer choices), decisions that constrain later units, recurring fixture/survey gotchas. NEVER: prose narration, accession numbers, exact values/counts/thresholds, company names, blow-by-blow, or restatement of the harness section — those live in code/tests/goldens; reference test files for specifics. Cap ~600 chars; longer means you are DUMPING — trim to architecture. A Log line is an index for the next unit, not a journal.**
6. Failure: max 3 fix attempts -> state `blocked(<reason>)` + Log line with all 3 attempts' evidence, commit safe artifacts only, move on.
7. Edit only: Units states, splits, Log, Open decisions. Design sections are STABLE — changing them requires the user.
8. Stop the iteration after ONE unit GROUP (or when blocked). Groups (user-approved 2026-06-12, measured: warm follow-on units run 5-15m vs 25-86m cold): a group is one iteration's scope; within a group still execute units IN ORDER, each with its own gates-green -> `done` -> Log line -> commit (bisectability preserved). If mid-group context runs low, stop after the current unit's commit — the rest of the group is just the next iteration. Units not listed below are their own group.

   | Group | Units | Shared machinery |
   |---|---|---|
   | G1 | U31+U32 | XBRL statements stack |
   | G2 | U33+U34 | facts/xbrl per-filing stack |
   | G3 | U40+U41+U42 | ownership forms 4/3/5 |
   | G4 | U46+U47 | 10-K/10-Q items+sections |
   | G5 | U49+U50+U51 | small notice/offering forms |
   | G6 | U53a+U54+U53b+U55a+U55b | registration/prospectus family |
   | G7 | U56+U57 | fund report family |

   All units done -> final Log line `ALL DONE` and report. No executable unit left, or two consecutive zero-progress iterations -> `HALT <reason>` per Loop-session rules and end the loop.

## Form Unit Recipe (every P4 unit)

0. **Harness first (U40 only, user-approved 2026-06-12)**: before any form work, U40 establishes the shared P4 harness and WRITES IT DOWN as a new STABLE plan section `## P4 typed-form harness` (envelope `data` union wiring + `kind` discriminator registration, converter/model module layout, parity-gate test template, fixture+golden naming conventions, goldens.test.ts mapping recipe). Every later P4 unit follows that section verbatim instead of re-deriving — deviations require a Log-recorded reason.
1. **Inventory**: read fork docs for the form (`docs/*.md`) + the data object source. Form docs are comprehensive but MAYBE slightly outdated or inaccurate (user, 2026-06-12) — verify every documented claim against the data object source and real filings, never trust blindly; record discrepancies in the unit Log. Write the parity-gate test skeleton: `data_surface(obj)` must equal wire model fields (no exclusion sets).
2. **Models**: `app/models/forms/<form>.py` — full fidelity, `kind` literal, nested models for tables/footnotes/signatures. Register in envelope union.
3. **Converter**: `app/converters/forms/<form>.py` — explicit field-by-field from the edgartools object. No `vars()`, no `getattr` loops.
4. **Parity gate**: finish the introspection test; it must FAIL if edgartools grows a field this converter misses.
5. **Fixtures**: pick 5-15 real accessions per this form's edge-case matrix; record fixtures (`EDGAR_FIXTURE_RECORD=1`, budget rules).
6. **Integration tests**: envelope endpoint per fixture; assert real values (names, amounts, dates — not just parse-success); dump goldens.
7. **Codegen**: regen openapi + zod; bun test validates new goldens.
8. Quality gates; state `done`; commit.

## P4 typed-form harness

> STABLE (U40, 2026-06-12). Every P4 form unit follows this verbatim. Changing it requires the user.

**Module layout** (one pair per form; `forms/` package dirs hold an `__init__.py` only):

| Path | Holds |
|---|---|
| `app/models/forms/<form>.py` | wire models; the top-level is `<Form>Data(WireModel)` whose FIRST field is `kind: Literal["<form>"]` |
| `app/converters/forms/<form>.py` | `<form>_data(obj) -> <Form>Data`, explicit field-by-field from the edgartools data object (no `vars()`/`getattr` loops) |

**Envelope `data` union** (`app/models/filing.py`):
- `FilingEnvelope.data` carries the typed payload; `obj_type` stays the edgartools class-name string (informational).
- One member: `data: <Form>Data | None`. Two+ members: `data: Annotated[<A> | <B> | ..., Field(discriminator="kind")] | None` — clean-break to the discriminated form when the 2nd unit lands (no transitional shim, single member needs no discriminator).
- `kind` values are lowercase, one per structurally-DISTINCT payload (distinct from `obj_type`'s PascalCase class name): `ownership` (Forms 3/4/5 share the one edgar `Ownership` object — same `OwnershipData` model + converter, the specific form is a field), `form8k`, ... Structurally identical forms never get a second model.

**Converter dispatch** (`app/converters/filing.py::filing_envelope`): call `filing.obj()`; dispatch on its concrete type to the per-form `<form>_data(...)`; unmapped type or `None` -> `data=None`. One dispatch row per form unit is the single registration point. `obj()` returns parsed structured data; heavy content (XBRL statements, full section text) lives at separate endpoints. A parse exception -> `data=None`, never a partial object.

**Parity gate** (`tests/integration/test_<form>_parity.py`): instantiate `filing.obj()` from ONE recorded fixture; `data_surface(obj)` auto-filters methods/classmethods and dunder attrs. Every remaining field must appear on the wire model. No `_EXCLUDED`, `_SERVED_ELSEWHERE`, `_ENVELOPE`, `_CLASS_LEVEL`, or any other hand-maintained set. If the test fails, the fix is to add the field to the wire model -- never to add it to an exclusion list. Structural transforms (renames, compound splits) use a small `_RENAMES` dict mapping edgar name -> wire name.

**Fixtures + goldens:**
- SEC fixtures auto-key by URL in the existing store; record with `EDGAR_FIXTURE_RECORD=1` within budget. Mine accessions from `~/Projects/secret-project/tests/fixtures/kd/edgar/` (read-only) + EFTS.
- Envelope goldens live under the EXISTING `ts/fixtures/responses/filing/` dir, named `<form>_<case>.json` (e.g. `form4_open_market_buy.json`); the typed `data` is validated as part of the envelope.
- Integration tests hit `GET /filing/{accession}` and assert real values INSIDE `data` (names, amounts, dates), never bare parse-success.

**goldens.test.ts:** NO new `RESPONSE_SCHEMAS` entry per form — the `filing` dir already maps to `GetFilingFilingAccessionGetResponse`, whose regenerated Zod carries the `data` union and enforces every member. Adding a form = (1) model file, (2) extend the `data` union, (3) converter + dispatch row, (4) parity gate, (5) fixtures + `filing/<form>_*` goldens, (6) regen codegen.

## Edge-case matrices (fixture selection)

| Form | Must cover |
|---|---|
| 4 | buy, sell, option exercise+expiration, multi-owner, amendment, footnoted price (null), 10b5-1 flag, derivative+underlying, indirect ownership |
| 3 / 5 | initial holdings only; annual summary; derivative holdings |
| 8-K | single item, multi-item, earnings (2.02 + EX-99), M&A (2.01), officer change (5.02), amendment; press-release extraction |
| 13D/G | XML (post-Dec-2024) AND legacy HTML, 13D vs 13G, amendments, owner-CIK present/absent, group filers, Item 4 purpose (13D) |
| 13F | multi-part (BlackRock/Vanguard), pre/post-2023 units, amendment, put/call, other-managers, voting splits |
| 10-K/Q | standard, IFRS/ADR filer (20-F too), REIT, bank, missing-section filer; Items/MD&A/risk-factors text |
| Financials | mega-cap, REIT revenue priority, IFRS (INFY-class), missing `us-gaap_Liabilities` filer, fiscal-year offset filer (AAPL), quarterly Q vs YTD labels |
| NPORT | equity fund, bond fund (derivatives), money market (N-MFP separately) |
| Proxy | standard DEF 14A, contested (DEFC14A), merger (DEFM14A) |
| Offerings/registration | S-1 IPO, S-3ASR, 424B5 takedown, DRS, Form D, Form C + C-AR |

## Units

| ID | Phase | Scope | State |
|---|---|---|---|
| U00 | P0 | Scaffold: `sidecar/` pyproject (local `edgar` path dep), app skeleton, settings, identity boot, `/health`, Dockerfile, compose.yaml, ruff/pyright config | confirmed |
| U01 | P0 | `serialize.py` policy + common models (FilingRef/FilingsPage/EntityRef/FilingEnvelope sans union) + exception->status mapping + CIK helpers (unit-tested) | confirmed |
| U02 | P0 | Test harness: pytest + URL-keyed fixture-store wiring, golden-dump helper, live marker, budget guard; first fixture+test (`/health`, `/tickers`) | confirmed |
| U03 | P0 | Codegen: evaluate+pick tool (comet_ask), export_openapi.py, generate_zod.sh, check_drift.sh, ts/ scaffold (bun, eslint, zod), first golden->Zod test green | confirmed |
| U10 | P1 | `/filings` + `/filings/current` (paging, owner filter) | confirmed |
| U11 | P1 | `/search` EFTS full-text (verify pagination depth past 100/page) | confirmed |
| U12 | P1 | `/tickers` full map (exchange field) | confirmed |
| U20 | P2 | `/filing/{accession}` envelope: multi-entity, related docs, `data=null` | confirmed |
| U21 | P2 | `/content` (markdown/text/html) + `/sections` | confirmed |
| U22 | P2 | `/attachments` list + `/attachments/{seq}` content | confirmed |
| U30 | P3 | `/company/{id}` full-fidelity profile + `/submissions` | confirmed |
| U31 | P3 | `/financials` annual+quarterly: IS/BS/CF/equity/comprehensive + cover, raw+standardized views, dimensions flag, `/metrics` scalars | confirmed |
| U32 | P3 | `/financials/multi` (XBRLS) + `/financials/ttm` | confirmed |
| U33 | P3 | `/facts` + `/facts/concept/{c}` + `/facts/search` (preserve form/filed/accn) | confirmed |
| U34 | P3 | `/filing/{accession}/xbrl` per-filing statements | confirmed |
| U40 | P4 | Form 4 typed data (ownership base machinery shared with 3/5) | confirmed |
| U41 | P4 | Form 3 | confirmed |
| U42 | P4 | Form 5 | confirmed |
| U43 | P4 | 8-K + 6-K/CurrentReport | confirmed |
| U44 | P4 | SC 13D + SC 13G | confirmed |
| U45 | P4 | 13F (single-filing holdings; D3 resolved no auto-merge) | confirmed |
| U46 | P4 | 10-K (items/sections/auditor + financials linkage) | confirmed |
| U47 | P4 | 10-Q | confirmed |
| U48 | P4 | 20-F + 40-F | confirmed |
| U49 | P4 | Form 144 | confirmed |
| U50 | P4 | Form D | confirmed |
| U51 | P4 | Form C (+C-U/C-AR/C-TR) | confirmed |
| U52a | P4 | Proxy foundation: full ProxyStatement model+converter+dispatch+parity+core fixtures (DEF 14A w/ XBRL+HTML tables, degraded/no-XBRL) +codegen | confirmed |
| U52b | P4 | Proxy edge-case matrix: DEFM14A merger / DEFC14A contested / PRE 14A preliminary / DFAN14A dissident / PX14A6G exempt fixtures + ground-truth comp assertions | confirmed |
| U53a | P4 | S-1 + F-1 (RegistrationS1) + shared offering nested models (offering.py) | confirmed |
| U54 | P4 | S-3 family | confirmed |
| U53b | P4 | DRS (wraps S-1/S-3 -> embeds U53a+U54 converters; runs AFTER U54 by dependency) | confirmed |
| U55a | P4 | 424B family (Prospectus424B): B1/B2/B3/B4/B5/B7/B8 + structured notes + ATM + resale | confirmed |
| U55b | P4 | 497K (Prospectus497K) fund summary prospectus | confirmed |
| U56 | P4 | NPORT FundReport | confirmed |
| U57a | P4 | N-MFP (MoneyMarketFund: N-MFP2 + N-MFP3) | confirmed |
| U57b | P4 | N-CEN (FundCensus) | confirmed |
| U57c | P4 | N-CSR (FundShareholderReport) | done |
| U57d | P4 | N-PX (proxy voting record) | done |
| U58a | P4 | EFFECT (effectiveness notice) | done |
| U58b | P4 | 10-D (CMBS ABS distribution report) | deferred |
| U60 | P5 | Full sweep: all goldens x Zod strict, openapi snapshot, docker build + container `/health`, fixture census in README | done |
| U61 | P5 | README runbook + consumer wiring notes (KD compose snippet + zod copy path — documentation only) | done |

## Open decisions

| # | Question | Owner | Resolve |
|---|---|---|---|
| D1 | Codegen tool pick (+ Zod major it emits) | session | RESOLVED U03: orval@8.17.0 + zod@4.4.3, evidence in Log |
| D2 | `search_filings`/EFTS pagination past 100/page | session | RESOLVED U11: fixed 100/page (size ignored), from<=9900, cap details in Log |
| D3 | 13F multi-part merge behavior in `f.obj()` | session | RESOLVED U45: obj() parses the single filing's OWN infotable, NO auto-merge (`is_multi_part` is not a real attr); cross-filing merge would need related-filing fetches excluded by the envelope policy. Envelope serves one filing's holdings. |
| D4 | Proxy/comp-table structure depth in edgartools | session | RESOLVED U52a: ProxyStatement exposes the comp tables as DataFrames (documented stable columns) over frozen dataclass lists -> all captured as typed rows (U31 unpivot); two legs (XBRL ecd: PVP/governance scalars + HTML-extracted SCT/director/beneficial/voting/pay-ratio/audit). `season` excluded (cross-entity Company.proxy_season scan). |
| D5 | Sentry/error-tracking env gate | user | park until KD wiring |

## Log

(append-only; `U## | state | what the unit delivered`)

U00 | done | App skeleton + /health endpoint. Identity boots from the EDGAR_IDENTITY env directly (edgar.core.get_identity() prompts interactively when unset, so the sidecar never calls it); EDGAR_RATE_LIMIT_PER_SEC pinned to 8 at boot before any client is created; EDGAR_LOCAL_DATA_DIR/EDGAR_USE_LOCAL_DATA pass through to edgar. Dockerfile build context = fork root (editable ../ dep).

U02 | done | Offline-replay verification harness: a URL-keyed SEC fixture store (sec_replay.py) patches the httpx transports so replay is the sole arbiter (offline by default; a miss is a hard error); recording is gated behind EDGAR_FIXTURE_RECORD=1 with a 60-new-file/run budget; golden() byte-equal asserts compact JSON with GOLDEN_UPDATE=1 regeneration; identity defaulted and the live suite deselected by default.
U01 | done | Wire foundation: serialize.py strict scalar coercers (NaN/NaT/inf->null, bool refused for int/float, ISO-only date strings); cik.py pad_cik/parse_entity_id (ascii-digit guard, not unicode isdigit); models/common.py WireModel base with extra=forbid (anti-silent-drop) + CIK/ACCESSION regex patterns; errors.py exception->HTTP map (429 + Retry-After, IdentityNotSet->503, validation->422, DataObject->502, httpx->404/429/502, unknown stays a loud 500).
U03 | done | Codegen pipeline: export_openapi.py emits openapi.json (snapshot-tested); generate_zod.sh runs orval in zod mode -> ts/src/generated; check_drift.sh regenerates openapi+zod+goldens and fails on any git diff; ts/ scaffold is bun + eslint flat + tsc strict. oneOf+discriminator emits a zod.union of strict kind-literal members (orval has no discriminatedUnion path - identical accept/reject set, z.infer narrows); anyOf-null->union(null), const->literal, date->zod.iso.date(); goldens.test.ts fails on any endpoint dir missing a schema mapping.
U10 | done | /filings: bounded date ranges only (open-ended would expand to every index since 1994 -> 422); year/quarter XOR date_from/date_to (422 on both); id -> filter(cik=) or filter(ticker=). /filings/current: get_current_entries_on_page (public fn), client-side form re-filter (SEC ignores type=, per edgartools #501), has_more from raw pre-filter page fullness. Wire policy: datetimes serialized UTC-Z (naive raises - SEC mixes Eastern/UTC); nullable wire fields are REQUIRED not optional, so absent->null and zod drops .optional().
U11 | done | /search (EFTS full-text): params mirror search_filings encoding (q/forms/items/dateRange/ciks/from); EFTS returns a fixed 100 hits/response (size ignored), offset via from=, hard cap from+page_size<=10000 pre-guarded (422); errorType bodies -> window 422 / other 502; exposes total_relation eq|gte, has_more clamps to min(total,10000). Ticker scoping via reference find_cik (avoids a full submissions fetch), unknown ticker 404. Full-fidelity 15-field SearchResult + facet aggregations (entities/sics/states/forms), hit+aggregation parsing reuses edgar.search.efts helpers.
U12 | done | /tickers: serves the full company_tickers_exchange map (cik/ticker/name/exchange) with uniform paging (page_size default 20000 returns all ~10k rows in one request); exchange null for unlisted/OTC entries (to_str empty->None); rows keep SEC file order (market-cap-ish). cik padded; ticker always present.
U20 | done | /filing/{accession} via get_by_accession_number_enriched (scans the quarterly indexes for all entity rows; current-year accessions missing from indexes fall back to the getcurrent feed -> slow 404). Envelope = index entities + full SEC-HEADER model (filers/reporting_owners/issuer/subject_companies with addresses, former names, filing values) + primary docs + URLs + data=null. ITEM INFORMATION re-parsed from raw header text (filing_metadata comma-joins repeated tags, lossy); serialize.eastern_naive_to_utc added (SEC-HEADER ACCEPTANCE-DATETIME is naive US-Eastern).
U21 | done | /content: fmt=markdown(default)|text|html + page_breaks (markdown-only, else 422). /sections: fmt=text|markdown via the modern edgar.documents.HTMLParser(ParserConfig(form=)), NOT the deprecated Filing.sections()/htmltools chunker; sections carry name/title/part/item/detection_method/confidence, ordered by start_offset; a non-HTML primary (e.g. rendered Form 4 XML) -> total=0, not an error.
U22 | done | /attachments: lists every SGML submission document (documents-then-data_files order, is_primary/is_binary flags, display_description merges FilingSummary report names + standard exhibit text, purpose for R-files). /attachments/{seq}: fmt=text(default)|raw|markdown extracted from the in-memory SGML (no new SEC fetch); raw on binary/uudecoded bytes -> 422 carrying the download url; text of binary -> null content; missing seq -> 404 naming seq+accession.

U30 | done | /company/{id} (CIK or ticker): profile from the SEC submissions store JSON ONLY (expensive cross-filing/facts properties - filer_type, latest_tenk/q, public_float - excluded by design; they belong to dedicated endpoints); is_foreign via is_foreign_company(state) only when a state code exists else null; display_name reverses individuals' "Last First". /company/{id}/submissions: pages the full filings table (trigger_full_load pulls the pagination files back to 1994), form filter client-side, items CSV->list, isXBRL/isInlineXBRL->bool|null. CompanyNotFoundError->404 (carries "did you mean" suggestions); dead CIK->404.

U31 | done | /company/{id}/financials + /financials/metrics. Statement shape: Statement.to_dataframe (SUMMARY or DETAILED via the dimensions flag) unpivoted into typed values[] records keyed by XBRL period keys; the library exposes no public period->column map, so the converter mirrors statements.py's (FY)/(Qn)/(YTD) naming and maps by name - an unmapped column raises (loud drift detection); transition-period column collisions (#582) keep-first. Form selection mirrors the get_financials chains (10-K/20-F/40-F, 10-Q/6-K) but lives in the router so the response carries provenance; filing-without-XBRL and exhausted-chain -> distinct 404s.

U32 | done | /financials/multi: XBRLS.from_filings stitches head(n) of the form chains (n 2-8, default 4), one column per filing, provenance flags each filing parsed/failed; SUMMARY|DETAILED via the dimensions flag. /financials/ttm: get_ttm_revenue/net_income convenience (errors->null) + explicit ?concept= (404 on miss); as_of ISO date or YYYY-QN else 422.

U33 | done | /company/{id}/facts (get_all_facts, paged), /facts/concept/{c} (query.by_concept: fuzzy substring on concept OR label by default; exact=true hits the taxonomy-qualified index key, so a bare name -> 0), /facts/search?q= (query.by_text case-insensitive regex; eager re.compile so a bad pattern -> 422). Fact = full-fidelity mirror of FinancialFact (33 dataclass fields, same names + is_dimensioned property; rendering helpers excluded; parity gate compares dataclasses.fields). value kept as int|float|str (raw) beside numeric_value (float). FactsResponse mirrors SubmissionsPage paging, sliced in-memory. get_facts() None -> 404 (CIK0001347842, an individual, is the no-facts case). Zero new recordings (AAPL companyfacts already in store from U32). Ground truth: AAPL FY2024 net sales 391,035,000,000 (10-K 0000320193-24-000123), 24,852 facts total; companyfacts is non-dimensional so is_dimensioned is always False.

U34 | done | /filing/{accession}/xbrl: ONE filing's own XBRL statements addressed by accession (filing.xbrl()), distinct from /financials' company-level latest-form selection. Reuses the enriched _lookup (agent-safe: resolves via the accession-YEAR quarterly index, not filer-CIK-from-accession which breaks for agent-filed filings) AND the single-filing _statement shaping, so /filing/{accession}/xbrl and /financials agree on a given filing. FilingXBRLResponse = FinancialsResponse's 6-statement shape minus the company-level selection fields (no period/amendments/superseded_by). filing.xbrl() None (no-XBRL filing, e.g. Form 4) -> 404 "has no XBRL data", never an empty-statement 200. Ground truth: NVIDIA FY2025 10-K (0001045810-25-000023, filed 2025-02-26, FY ended 2025-01-26) revenue 130,497M / 60,922M / 26,974M (us-gaap_Revenues, standardized); resolved offline from the already-recorded 2025 Q1 form index -> 1 new fixture (the 10-K SGML). No-XBRL case reuses U20's recorded NVIDIA Form 4 (0001045810-25-000002); nonexistent-404 reuses the 1995 accession (small early-EDGAR indexes). G2 group complete.

U40 | done | Form 4 establishes the P4 base: one OwnershipData (kind=ownership) backs Forms 3/4/5, the `form` field discriminates. Architectural call (deviation from harness "obj() then dispatch"): gate by form via matches_form BEFORE filing.obj(), since edgar.obj() falls through to a costly xbrl() parse for untyped forms. HTTPError re-raised; other parse errors -> data=null. Wire-shape gotcha (all ownership forms): edgar coerces a column to float only if EVERY cell parses, so a footnoted value stays the literal "[F1]" string, not null. Parity gate over the full Ownership surface. 5 fixtures; see test_form4.py.

U41 | done | Form 3: reuses OwnershipData via one dispatch row (no schema change — openapi/zod byte-identical). Form 3/4/5 are thin Ownership subclasses, so U40's parity gate covers all three; no new gate. Shape note: holding dataclasses have no footnotes attr (only transactions do), so holdings carry footnote refs inline in their values. Form 3 carries holdings, never transactions. 4 fixtures (initial holdings, no-securities, derivative holdings); see test_form3.py.

U42 | done | Form 5: reuses OwnershipData via one dispatch row (openapi/zod byte-identical). Shape note: a transaction row's `form` field is the per-row reportable form as filed (a gift carries "4" on a Form-5 doc), not the document form. Closes G3 (ownership 3/4/5): one shared model+converter, three dispatch rows, one parity gate. 4 fixtures; see test_form5.py.

U43 | done | 8-K + 6-K: two distinct kinds (form8k, form6k) in separate model files — NOT the ownership shared-model pattern. Envelope `data` clean-broke to a discriminated Annotated union. LAYER FIX (reused by every later P4 unit): DocumentRef + builder live in models/common.py + converters/common.py to break the envelope<->form-model import cycle. Survey gotcha (reused since): Company().get_filings() full-loads pagination back to 1994 and blows the record budget — use index-based get_filings(year,quarter,form) in a disposable /tmp store. See test_form8k.py / test_form6k.py.

U44 | done | SC 13D + SC 13G: two kinds (sc13d/sc13g) over ONE shared set of cover-page nested models — only narrative items differ (13D free-text, 13G flags). Nested models prefixed (Schedule13*) to avoid OpenAPI component collisions. Dispatch row carries both modern and legacy form strings; matches_form adds /A. Degraded path (recurs for any XML-mandated form): pre-mandate HTML-only filings parse via from_header -> has_structured_data=False, empty lists, null totals. Storage rule (reused since): source finalists from already-recorded quarterly indices, never record multi-MB indices for one fixture. See test_schedule13*.py.

U45 | done | 13F family (HR/NT/CTR + /A): one ThirteenF -> single kind form13f, `form` carries the variant; dispatch reuses edgar's THIRTEENF_FORMS accept set. D3 RESOLVED: obj() parses only the filing's OWN infotable (no cross-filing auto-merge), per the envelope own-artifacts policy. Capture choice: holdings[] = DISAGGREGATED infotable rows; aggregated `holdings` excluded as client-derivable. Recurring gotcha: thousands-era values read from obj.total_value (normalized x1000), not raw summary_page. See test_thirteenf.py.

U46 | done | 10-K + 10-K/A: one TenK -> kind form10k, `form` is the variant. LEAN big-form envelope (the pattern for U47/U48): `data` = STRUCTURE only -- item index (part/title from the static obj.structure catalog), auditor (inline-XBRL DEI), EX-21 subsidiaries, has_financials linkage; long-form item text stays in /content + /sections, statements in /xbrl. Cross-unit gotcha (any EX-21 consumer): edgar parse_subsidiaries is heuristic -- on non-clean layouts it leaks the table header + footnote markers in as Subsidiary rows; faithful passthrough, NOT munged. See test_tenk.py.

U47 | done | 10-Q + 10-Q/A: one TenQ -> kind form10q, SEPARATE from form10k (no EX-21 + part-qualified items = distinct payload, 8-K/6-K split rule). EXTRACTED shared `forms/company_report.py` pair (models Auditor + ReportItem, converter auditor()) = canonical CompanyReport-family home; U46 refactored onto it (TenKItem -> ReportItem). U48 (20-F/40-F) MUST reuse these. Item gotcha vs 10-K: TenQ.items is part-qualified ('Part I, Item 1' != 'Part II, Item 1') so part comes from the item string + title is a PART-AWARE lookup get_item(item,part); items arrive in detection order, unsorted. See test_tenq.py.
U48 | done | 20-F + 40-F = TWO kinds (split-rule like 8-K/6-K): form20f is item-structured, reusing the 10-K's report_item_from_catalog (EXTRACTED to the shared company_report.py converter; tenk refactored onto it); form40f is LEAN, NO items -- its AIF/MD&A are EX-99 exhibits needing cross-document fetches, EXCLUDED by the lazy-property policy + served via /attachments + /content. 20-F gotchas: items in detection-order (unsorted), unique by number across 5 Parts; sub-items past the static catalog (16A-16K, 10J) -> part=null/title=null (faithful, not synthesized). FPIs tag the DEI auditor (unlike the unaudited 10-Q); a 40-F/A may tag none -> null. See test_twentyf/test_fortyf.py.
U51 | done | Form C -> one FormC backs EVERY Reg-CF variant (C/C-A/C-U/C-U-A/C-AR/C-AR-A/C-TR) -> kind formc; `form` IS the variant, exposed directly (like FormD submission_type). 3-TIER optionality drives the wire: offering+funding_portal null for C-AR AND C-TR, annual_report null for C-TR (test each None branch). DIVERGENCE from D's as-filed strings: FormC offering_amount/maximum_offering_amount are FLOATS -- edgar maybe_float coerces a blank to 0.0 (so missing reads 0.0 NOT null; reused by U55 offerings, watch the 0.0-vs-null trap). NEW bug-handling pattern (divergence from D's faithful-null passthrough): 3 edgar FilerInformation.from_xml bugs handled by OMITTING the field, because a wrong scalar misleads worse than absence in a financial API -- ccc reads <filerCik> (dups cik; real <filerCcc> masked XXXXXXXX), live_or_test reads testOrLive under <filer> but the element is <liveTestFlag> under <filerInfo> -> constant False (every live filing mislabeled). Both surfaced to user for a possible edgar fix; the <flags> block (confirming/return/override copy) parses correctly -> captured. Dispatch row mirrors edgar obj()'s accept set ["C","C-U","C-AR","C-TR"] (matches_form expands /A). AnnualReport field names mirror edgar 1:1 (18 floats + employees + jurisdictions). Fixtures 2025 Q1 (index already recorded). See test_formc.py.

U50 | done | Form D -> one FormD -> kind formd (D + D/A; `submission_type` IS the variant, used directly -- unlike Form144's DERIVED form, FormD exposes submission_type). Full faithful offeringData tree captured (issuer / related_persons / industry+fund_info / amounts / investors / sales-comp recipients / use-of-proceeds / signatures); NO analytical layer to strip (contrast 144). Dollar amounts + counts kept AS-FILED strings -- "Indefinite" is a valid totalOfferingAmount, never coerce (U49 as-filed-string precedent; reused by U51/U55 offerings). GOTCHA reused by offerings forms: edgar OfferingData.is_new is INVERTED -- it holds the <isAmendment> flag (True<=>amendment), captured under its true name offering.is_amendment (verified empirically D=False vs D/A=True). Three provable edgar parse bugs, faithful passthrough + surfaced to user for a possible edgar fix: SalesCompensationRecipient.associated_bd_name is annotated-not-assigned (formd.py:112 -> AttributeError -> defensive getattr None, TODO(BLOCKED)); recipient address zipcode looks up a hard-coded tag name (formd.py:133 -> always null even with a real zip); foreignSolicitation never parsed (not on object -> omitted). Fixtures from 2025 Q1 (form index already recorded, U44 storage rule). See test_formd.py.

U49 | done | Form 144 -> one Form144 -> kind form144 (144 + 144/A; `form` DERIVED from is_amendment, Form144 exposes no public .form). Captured = AS-FILED rows only: the 3 tables as disaggregated records + issuer identity + filer/contact + notice_signature; edgar's whole analytical layer (totals/percent/holding-period/10b5-1 inference/anomaly flags) EXCLUDED as client-derivable (U45 precedent), company EXCLUDED (cross-entity Company(issuer_cik)). Gotchas reused by later DataFrame-backed forms: edgar row.to_dict() DROPS broker/seller ADDRESSES before they reach the object -> only names capturable (faithful to object, no XML re-parse); nothing_to_report is annotated bool but holds the raw child_text 'Y'/'N' -> kept as str, never re-interpreted; 144 date fields kept as-filed MM/DD/YYYY (form permits 1933 placeholders, to_date is ISO-only) -- justified deviation from the wire ISO convention; Form 144 XML mandatory only since Apr-2023 -> pick post-mandate fixtures (older = paper, data=null). See test_form144.py.

EDGARFIX | done | Cross-cut (a14846bf..df9c5674): edgar parse bugs U46/U49/U50/U51 worked around (omit / getattr-None / faithful-passthrough) are FIXED in-library + propagated to sidecar, SUPERSEDING those bug notes. Now CAPTURED, not worked-around: formc ccc+live_or_test, formd recipient associated_bd_name+zipcode+foreign_solicitation, form144 broker/seller addresses (row.to_dict keeps them)+nothing_to_report-as-bool, ownership aff_10b5_one, EX-21 no longer leaks header rows as subsidiaries. Buried green absence-tests -> correct-value assertions; parity gates + filing goldens regenerated per form. STILL VALID (orthogonal to these fixes): U50/U51 as-filed-string + maybe_float 0.0-vs-null traps, heed for U55.

U52a | done | DEF 14A + every 14A variant -> one ProxyStatement -> kind=proxy; `form` IS the variant; dispatch reuses edgar's PROXY_FORMS (matches_form expands /A) -> U52b adds fixtures only, no model change. Two legs: XBRL ecd: PVP/governance scalars + HTML comp tables. Tables are edgar DataFrame-views over frozen dataclass lists -> typed rows via to_dict('records') (U31 unpivot); typed-object props (voting/named_execs/ceo_pay_ratio/audit_fees) come straight off dataclasses. season EXCLUDED (cross-entity Company.proxy_season scan). Row period_end is ISO str on some legs / Timestamp on others -> _date_str handles both. Degraded has_xbrl=False -> all comp empty, object still parses (never partial/500). See test_proxy.py.

U52b | done | Proxy edge forms (DEFM/DEFC/PRE 14A/DFAN14A/PX14A6G) are all in PROXY_FORMS -> all dispatch to ProxyStatement; fixtures-only, U52a's parity gate already covers them. Shape varies by FORM not model: DEFC14A is the only edge form with PVP XBRL; DEFM14A has no PVP; PRE 14A has_xbrl=True yet NO pvp facts -> PVP scalars null despite has_xbrl; DFAN14A (SUPPLEMENTAL) + PX14A6G (EXEMPT_SOLICITATION) -> degraded-empty, never 500. GOTCHA (any past-quarter recording unit): enriched lookup resolves PAST-quarter accessions via full-index/<yr>/QTRn/form.gz -> stage that index as a replay dep; current-quarter accessions skip it. GOTCHA: edgar HTML proposal-extractor over-triggers on supplemental letters (date phrases -> phantom proposals). Closes proxy family. See test_proxy_edge.py.

U53a | done | S-1 + F-1 (+/A) -> ONE RegistrationS1 -> kind=registration_s1 via matches_form(['S-1','F-1']) (auto-expands /A). Shared offering legs (fee_table/selling_stockholders/underwriting/dilution/capitalization) live in NEW offering.py shared module (company_report.py precedent) -- U54/U53b/U55 reuse these converters+models. Fidelity: mirror edgar STORED fields 1:1 (raw strings where edgar stores strings, floats where it parsed; derived numeric @property NOT mirrored). GOTCHA: fee_table can be a non-None empty SHELL (Exhibit 107 located, securities/totals don't parse) -- assert the shell, distinct from genuine None. GOTCHA: edgar selling-stockholders HTML extractor OVER-TRIGGERS on non-resale IPOs (lifts header fragments as names) -> only genuine resale asserts holders; IPO/SPAC assert fee/underwriting/dilution. offering_type enum -> .value; cross-entity legs (takedowns/related_filings/effective_date via Company.get_filings) EXCLUDED. See test_registration_s1.py + _parity.py.

U54 | done | S-3/F-3 shelf family (S-3/S-3ASR/S-3D/S-3DPOS/F-3/F-3ASR +/A) -> ONE RegistrationS3 -> kind=registration_s3 (edgar's exact obj() accept set; matches_form expands /A). The SIMPLE registration: cover_page (S3CoverPage = S1's cover minus sic_code+security_description) + fee_table ONLY -- NO selling_stockholders/dilution/capitalization/underwriting (those are S-1 prospectus tables, absent from shelves). Reuses offering.py OfferingFeeTable + fee_table(). is_auto_shelf captured as a top-level bool (parallel to is_amendment). GOTCHA for U55: the SHARED extract_registration_fee_table (S-1/S-3/424B all use it) column-MISALIGNS deferred Rule 457(r) ASR tables (row#->security_type, type->security_title, '457(r)'->amount_registered), with zero totals + fee_deferred=True -- mirror faithfully, assert structural facts not the misaligned cells. fee_table is a non-None SHELL when the exhibit is found but unparsed, vs genuine None when there is no Ex-107 (typical of amendments). For U53b DRS: DRS.underlying_object -> RegistrationS1|RegistrationS3, so it embeds U53a+U54 converters directly. See test_registration_s3.py + _parity.py.

U53b | done | DRS + DRS/A -> ONE DraftRegistrationStatement -> kind=drs via matches_form('DRS') (auto-expands /A). The WRAPPER form: underlying_form detected from COVER TEXT (the EDGAR label is just 'DRS'); edgar builds underlying_object ONLY for S-1/F-1 (->RegistrationS1) + S-3 (->RegistrationS3), else None (S-4/F-4/20-F/Form 10/Unknown -> None; wrapper still parses). KEY PATTERN: underlying_object is a NESTED discriminated union (DRSUnderlying = RegistrationS1Data|RegistrationS3Data on their own `kind`) under the envelope's top-level one -- orval emits valid zod for it, goldens validate; embeds U53a+U54 converters VERBATIM (isinstance dispatch). Drafts predate the fee filing -> embedded fee_table None/empty-shell. amendment_number parsed from 'Amendment No. N' cover text. company_name EXCLUDED (dup of company). No real S-3 DRS exists (seasoned S-3 issuers already public) -> RegistrationS3 branch present for completeness, NO fixture. See test_drs.py + _parity.py.

U55a | done | 424B family (B1/B2/B3/B4/B5/B7/B8 +/A) -> ONE Prospectus424B -> kind=prospectus_424b (edgar's exact accept set; matches_form expands /A); `form` IS the variant, offering_type = the classifier's verdict. Reuses offering.py legs (selling_stockholders/underwriting/dilution/capitalization) VERBATIM; NEW 424B-only models cover_page/pricing/offering_terms/structured_note + filing_fees (NON-optional SHELL -- header totals can coexist with zero offering_rows). CORRECTION to U54: filing_fees is the EX-FILING-FEES XBRL leg (extract_filing_fees_xbrl, as-filed STRINGS), DISTINCT from the S-1/S-3 HTML RegistrationFeeTable floats -> the 457(r) ASR column-misalignment is HTML-ONLY; 424B's XBRL fees are clean. EDGAR DETERMINISM FIX (separate flagged commit, cross-cut): FilingHeader.file_numbers returned list(set(...)) -- set iteration is hash-seed-ordered, so cover registration_number flipped across runs for co-registrant filings (424B/S-1/DRS cover all take file_numbers[0]); fixed to list(dict.fromkeys()) = document order, primary registrant's base number first. GOTCHA: envelope company is the SEC FILER entity (enriched-accession path), NOT the cover issuer (SPE/holdco co-registrant). edgar selling_stockholders/underwriting extractors over-trigger on prose -> assert genuine rows not list purity (U53a). variant + cover-delegating scalars (registration_number/ticker/offering_*) EXCLUDED from parity. See test_prospectus_424b.py + _parity.py.
U55b | done | 497K (+/A) -> ONE Prospectus497K -> kind=prospectus_497k via matches_form(["497K"], expands /A). FIRST fund form: ZERO XBRL (HTML-parsed); fund identity (fund_name/series_id/share_classes+fees+$10K-expense-example) REPLACES the family's issuer scalars -- precedent for G7 reports. performance_returns from PRIVATE _performance_returns (typed list) NOT public `performance` DF (drops inception_date + breaks serialize no-DF-walk); per U53a fidelity. FIXTURE GOTCHA: enriched resolves 497K from .txt alone -- no submissions JSON. Closes G6. See test_prospectus_497k.py + _parity.py.

U56 | done | NPORT-P/EX (+N-PORT/A) -> ONE FundReport -> kind=nport via NPORT_FORMS. ZERO XBRL: lxml XML -> 4 stored structures (header/general_info/fund_info/investments[]); parity captures ONLY those -- *_data views, cross-entity resolvers, and rich tables EXCLUDED (rows ARE the typed records; pattern reused by U57 fund forms). Derivative holdings nest a sub-record keyed by derivative_category; GOTCHA: a WAR row populates option_derivative (not its own model), so the warrant fixture covers the option path. FIXTURE: enriched resolves from .txt alone (no submissions JSON, as 497K). G7 open: U57 next. See test_nport.py + _parity.py.

U57a | done | N-MFP2+N-MFP3 (+/A) -> ONE MoneyMarketFund -> kind=nmfp via MONEY_MARKET_FORMS; BOTH schema versions parse to the SAME object. ZERO XBRL (lxml). Stored structs general_info/series_info/share_classes[]/securities[] (securities nest ratings[]+repo_agreement->collateral[]); parity = U56 pattern. GOTCHA v2: null registrant/series, synthetic ts labels (week_N/null) vs v3 ISO, cusip->otherUniqueId. GOTCHA ratings: edgar reads ONLY security-level assigningNRSRORating (NOT demand-feature/guarantee NRSRO); empty=correct, not an edgar bug. FIXTURE: v2 forces pre-mid-2024 filing -> 2023 form.gz index (~5MB, normal). G7: U57b/c/d next. See test_nmfp.py.

U57b | done | N-CEN (+/A) -> ONE FundCensus -> kind=ncen via NCEN_FORMS. ZERO XBRL (lxml). 5 stored structs: report_date, is_period_lt_12_months, registrant (governance), series[] (deep per-series tree: provider lists + brokers + principal_transactions + securities_lending + line_of_credit + etf_info->authorized_participants), signature_info; parity = U56 pattern. GOTCHA: line_of_credit.is_committed is as-filed TEXT (Committed/Uncommitted) NOT bool. GOTCHA: BrokerDealer/Accountant file_number+lei keep literal 'N/A' (edgar _text not _clean_na; only CRD nulled). is_diversified tri-state bool|None. FIXTURE: etf_info needs an ETF trust; liquidity_providers empty (in-house norm). G7: U57c/d next. See test_ncen.py.

U57d | done | N-PX (+/A) -> ONE NPX -> kind=npx via explicit ["N-PX"] list (edgar has no NPX_FORMS constant; matches_form auto-expands /A). XML-parsed (primary_doc.xml + proxy vote table attachment), zero XBRL. Two report families: FUND VOTING/NOTICE (mutual funds, has series_reports + report_series_class_infos) and INSTITUTIONAL MANAGER VOTING/NOTICE (investment advisers, no series). proxy_votes can be None (notice reports) -> wire sends []. 44 scalar/list fields (45 data_surface minus primary_doc exclusion). primary_doc is the raw PrimaryDoc dataclass backing store -- every NPX property delegates to it, so it's excluded from parity (would double every field). `address` and `agent_for_service_address` are computed concats on NPX (not structured fields) -- mirrored as-is. `other_included_managers_count` and `series_count` are STRINGS not ints (as-filed). GOTCHA: large fund families can have tens of thousands of vote records (Vanguard Index Funds: 28K votes = ~5MB JSON). FIXTURES: perritt (FUND VOTING, 291 votes, 2 series), imst (FUND NOTICE, 0 votes, 6 series + report_series_class_infos), provident (IM NOTICE, degraded -- no series/votes), hbk (N-PX/A amendment, amendment_no=6). Closes G7 fund family. See test_npx.py + test_npx_parity.py.

U58a | done | EFFECT -> ONE Effect -> kind=effect via explicit ["EFFECT"] (no /A variant -- EFFECT is itself the terminal SEC notice). Tiny XML-parsed form: 8 fields on data_surface + source_file_number from the backing store. effectiveness_data (plain class) excluded from parity (every useful field exposed as a direct property except file_number -> mapped as source_file_number). `address` is NOT on Effect (unlike NPX); the filer identity is just cik + entity name. source_submission_type is what was made effective (S-1, POS AM, etc.); source_accession_no links to the source filing (often null -- most EFFECT filings carry only the file number). FIXTURES: aim (S-1 source, no source_accession_no), toyo (POS AM source, source_accession_no populated). U58b (10-D CMBS) deferred -- edgar's HTML extraction has ~42% accuracy. See test_effect.py + test_effect_parity.py.

U57c | done | N-CSR + N-CSRS (+/A) -> ONE FundShareholderReport -> kind=ncsr via NCSR_FORMS. UNLIKE all other fund forms (NPORT/N-MFP/N-CEN = lxml zero-XBRL), N-CSR carries Inline XBRL in the open-end-fund (oef:) taxonomy via filing.xbrl() + FactQuery. Only open-end funds carry this taxonomy; closed-end/BDC filings return obj()=None -> data=null. A single filing covers a WHOLE TRUST: funds[] (one NcsrFund per SEC series), each with net_assets/portfolio_turnover/advisory_fees_paid/holdings_count and share_classes[]. Identity (series_id/fund_name/class_id/class_name/class_ticker) is authoritative SGML from the header (app/sgml_series.py parses SERIES-AND-CLASSES-CONTRACTS-DATA); figures are oef facts keyed by ClassAxis dimension. The converter bypasses edgar's flat object and builds from SGML+XBRL directly. GOTCHA: oef:HoldingPctOfNav is never tagged by filers -- holdings_count is populated but holdings[] is always empty (the per-holding data lives in unstructured HTML, not oef XBRL). GOTCHA: load classes report each annual-return horizon twice (standardized max-load + without-sales-load), keyed by SalesLoadAxis; no-load classes report once. GOTCHA: single-class funds file facts undimensioned (no ClassAxis). FIXTURES: bny_muni (annual, 1 fund, 5 classes, load+no-load returns), gator (annual, 1 fund, 1 class, authoritative SGML name), bny_intl (N-CSRS semi-annual, 3-fund trust, anti-flattening), emkt (N-CSR/A amendment dispatch). See test_ncsr.py + test_ncsr_parity.py.