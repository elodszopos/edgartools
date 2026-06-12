# edgar-sidecar — full edgartools HTTP wrapper

> Self-sufficient FastAPI sidecar inside this fork. Wraps the LOCAL `edgar` package as the single SEC egress.
> Full-fidelity Pydantic per form data object -> OpenAPI 3.1 -> generated Zod, committed here. Pluggable into any stack (knowledge-distiller is the first consumer — it wires this in itself; THIS plan never writes outside this repo).
> Status: ACTIVE. Loop-executable: each session runs the Session Protocol below.
> Supersedes (stale, background only): KD `.claude/plans/edgar-service.md`, secret-project `.claude/plans/edgar-service.md`.

## Why (v1 postmortem — what must never recur)

| v1 sin | This plan's answer |
|---|---|
| `clean()`/`_dump_obj` attribute-walking -> silent field drops | Explicit Pydantic models only; per-form field-parity gate fails CI on any uncaptured field |
| Manual concept maps (`XBRL_TAG_ALIASES`, `BS_MAP`/`IS_MAP`/`CF_MAP`, sign sets) | Expose edgartools standardized statements + scalar getters + TTM directly |
| Hand-written Zod (94 transforms, 1873 defaults) kept aligned by drift test | Zod GENERATED from OpenAPI; regen+diff gate; consumers re-built against generated shapes |
| Half-bridge: TS kept discovery + XML parsers | Sidecar owns 100% of SEC I/O; typed `data` for every investor-relevant form |
| Cross-process Redis rate limiter + promise chains | Single egress; edgartools-native throttle only |

## Hard constraints

- KD repo (`~/Projects/knowledge-distiller`) and secret-project are READ-ONLY. Never write/run anything there. Mining v1 fixture accession numbers (read) is allowed.
- All work in THIS fork, branch `main`, additive: new top-level `sidecar/` + this plan. `edgar/` library edits only as separate, flagged commits when a real library bug blocks a unit.
- No file deletion ever (user rule). Use `mv` if relocation needed.
- SEC traffic only via the recording protocol below. Tests replay cassettes offline.
- Stateless service: no DB, no Redis, no cron, no auth (single consumer on compose network).

## Loop-session rules (unattended operation)

- **No subagents.** Never spawn Agent/Task in loop sessions — work directly. (Agent spawns require a context-injection MCP that may be down overnight; a blocked spawn stalls the loop. Determinism beats parallelism here.)
- **Standing authorization.** This plan pre-approves, inside this repo only: the quality-gate commands, `sidecar/scripts/*`, pytest (incl. VCR recording within the SEC budget), codegen, `uv`/`bun` installs scoped to `sidecar/`, and `git add`/`git commit`. Anything outside that set (pushes, KD writes, library rewrites, new external services) -> `blocked(user)`.
- **Precedence.** For `sidecar/` work this plan supersedes the fork's `CLAUDE.md` workflow ceremony (beads issue tracking, triage commands — skip them). Fork `CLAUDE.md` still governs style when touching `edgar/` library code.
- **Anti-spin halt.** If no executable unit remains (everything `done`/`blocked`), or an iteration ends with zero state change twice in a row, append `HALT <reason>` to the Log, commit, and END the loop — do not idle-reschedule.
- **Context discipline.** If a unit outgrows the session, finish the smallest coherent slice, commit it, set `in-progress`, and write the exact next action into the Log line so the next iteration resumes without re-deriving.
- Outside this repo, read ONLY the named v1 fixture-mining path. Never read/write KD.
- **Overnight authorization (user, 2026-06-12).** Run continuously, do NOT stop. FULL authorization for all API interactions within rate limits and for everything inside this repo. Docker: the sidecar's own image/containers only — touching ANY other running container is strictly forbidden.

## Launch (zero manual setup)

One command from anywhere: `~/Projects/edgartools/sidecar/loop.sh` — zero prerequisites.
- `SEC_EDGAR_USER_AGENT` is hardcoded in the launcher (contact string, not a credential — same plaintext value as v1's `.env.tpl`).
- Starts `claude` anchored in the fork root with the /loop prompt baked in.
- Fork `.claude/settings.json` pre-allows comet + context7 MCP (the U03 research tools missing from global allows); Bash/Edit/Write under `~/Projects/**` are already globally allowed, so loop iterations never hit a permission prompt.
- Fork `.claude/settings.json` env sets `CLAUDE_CODE_AUTO_COMPACT_WINDOW=300000`: loop sessions auto-compact at 300k context tokens (user request 2026-06-12; per-N-iterations compaction is not supported by Claude Code — hooks cannot trigger compaction and agents cannot invoke built-in /compact).

## Layout

```
sidecar/
  loop.sh                 # overnight-loop launcher (op-resolved env, /loop prompt baked in)
  pyproject.toml          # name edgar-sidecar; deps: edgar @ file://../ (editable), fastapi, uvicorn[standard]; dev: pytest, pytest-vcr, vcrpy, httpx
  app/
    main.py               # FastAPI app, identity boot (fail without SEC_EDGAR_USER_AGENT), exception mapping
    settings.py           # env vars table below
    serialize.py          # JSON policy: numpy->int/float, Decimal->float, date->ISO, NaN/NaT->null, DataFrame -> typed records via explicit converters ONLY
    models/               # Pydantic: common.py, filings.py, company.py, financials.py, facts.py, forms/<form>.py
    converters/           # edgartools object -> model, explicit field-by-field. forms/<form>.py
    routers/              # filings.py, filing.py, company.py, financials.py, facts.py, reference.py, health.py
  tests/                  # pytest; cassettes/ (VCR, fork conventions); unit/ for pure helpers; integration/ per router
  ts/                     # bun project: zod pinned, eslint; src/generated/ (codegen output, do-not-edit), fixtures/responses/<endpoint>/<case>.json (goldens), tests/ validate every golden against generated Zod
  scripts/
    export_openapi.py     # app -> openapi.json (committed snapshot)
    generate_zod.sh       # openapi.json -> ts/src/generated/ (tool picked in U03)
    check_drift.sh        # regen openapi + zod + goldens-schema pass; git diff --exit-code
  Dockerfile              # python:3.12-slim, non-root, uvicorn app.main:app, HEALTHCHECK /health
  compose.yaml            # reference service block: name edgar, port 8000, env, optional edgar-cache volume
  README.md               # endpoint census, env, runbook, consumer wiring notes (incl. KD zod copy path)
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

| Phase | Endpoints | edgartools source |
|---|---|---|
| P1 | `GET /filings` (forms, date range, cik/ticker, paging) · `GET /filings/current` (RSS getcurrent) · `GET /search` (EFTS full-text) · `GET /tickers` | `get_filings`, `current_filings.py`, `search/efts.py`, `reference/tickers.py` |
| P2 | `GET /filing/{accession}` (envelope) · `/content?fmt=markdown\|text\|html` · `/sections` · `/attachments` · `/attachments/{seq}` (text/extracted) | `_filings.py`, `attachments.py`, `documents/` |
| P3 | `GET /company/{id}` (+`/submissions`) · `/company/{id}/financials` (5 statements + cover; annual/quarterly; `view=raw\|standardized`; `dimensions=` flag; + `/metrics` scalars) · `/financials/multi?periods=N` (XBRLS stitched) · `/financials/ttm` · `/facts` (+`/concept/{c}`, `/search?q=`) · `GET /filing/{accession}/xbrl` | `entity/core.py` (Company), `financials.py` (incl. statement_of_equity, comprehensive_income, cover, scalar getters), `xbrl/` (XBRL, Statements, StitchedStatement), `ttm/`, `standardization/`, `entity/entity_facts.py` + `entity/query.py` |
| P4 | typed `data` per form (units below) | `ownership/`, `company_reports.py`, `beneficial_ownership/`, `thirteenf/`, `form144.py`, `offerings/`, `proxy/`, `funds/`, `effect.py` |
| Always | `GET /health` (status, edgartools version, identity_set) · `GET /openapi.json` | — |

Statement shape: typed `values[]` records (`concept`, `label`, `preferred_sign`, `values[{period_label, period_end, period_type, value}]`) — never dynamic period columns. `presentation=False` raw signs; standardized view exposed alongside.

## Typed form coverage (end state)

Investor set — full-fidelity models: Form 3/4/5 · 8-K · 6-K · 10-K · 10-Q · 20-F · 40-F · SC 13D/13G · 13F-HR · 144 · D · C (+C-U/AR/TR) · proxy family (DEF 14A et al.) · S-1 · S-3 family · 424B family · DRS · 497K · NPORT-P/EX · N-MFP · N-CEN · N-CSR · N-PX · EFFECT · 10-D (CMBS).
Envelope-only (typed later only if ever needed): CORRESP/UPLOAD, ATS-N family, MA/MA-I/MA-W, TA-*, SBSE, CFPORTAL, X-17A-5, 24F-2NT.

**Full fidelity rule:** every public field/property the edgartools data object exposes is captured (nested tables, footnotes, signatures, remarks, flags). Exclusions ONLY for: rendering helpers (`__rich__`, `to_html`, repr), internal caches/private attrs, DataFrame views whose data is captured as typed records elsewhere. Each exclusion lives in the form's parity-gate test with a one-line justification.

**Lazy/expensive property policy:** envelope `data` is built ONLY from the filing's own artifacts (its documents/XML/XBRL — internal fetches bounded to that filing). Properties that trigger cross-filing or cross-entity SEC calls are excluded (justified in the parity gate) and served by dedicated endpoints instead. Envelope responses stay lean (soft budget ~1-2MB): long-form text (10-K items, MD&A) ships via `/content`, `/sections`, or explicit `include_*` opt-in params — `data` carries the structure (section titles, presence, bounded excerpts), not megabytes of prose.

## Codegen pipeline

1. Pydantic -> `scripts/export_openapi.py` -> committed `sidecar/openapi.json` (snapshot test).
2. `generate_zod.sh` -> `ts/src/generated/` with do-not-edit header, committed.
3. Drift gate: `check_drift.sh` = regenerate both + `git diff --exit-code` + bun test green. Run in every unit's verify step.
4. Tool picked in U03 against criteria: OpenAPI 3.1 in, discriminated unions -> `z.discriminatedUnion` (or acceptable equivalent), deterministic output, maintained. Candidates: `openapi-zod-client`, `orval`, `kubb`, `typed-openapi`. Zod 3 vs 4: WHATEVER the best tool emits (user decision — do not block on this). Use comet_ask for current tool state; if comet is unavailable, evaluate by installing candidates against the U03 spec sample directly.
5. If NO tool meets the criteria: mark U03 `blocked(user)` with the evidence table. Do NOT hand-roll a generator — that is a user decision.

## Test architecture (the centerpiece)

| Leg | What | How |
|---|---|---|
| Python integration | endpoint -> JSON correct per fixture | pytest + VCR cassettes (fork conventions: `record_mode=once`, filtered UA). FastAPI `TestClient`; assertions on real values, not just shape |
| Field-parity gate | no field ever forgotten | per form: introspect edgartools object public surface vs converter coverage; fail with named missing fields; explicit justified exclusion list |
| TS end-to-end | generated Zod accepts every real response | Python tests dump each response JSON as golden -> `ts/fixtures/responses/` -> bun test parses ALL goldens with generated Zod (strict) |
| Live smoke | true SEC round-trip | tiny opt-in suite, `@pytest.mark.live`, excluded by default |
| Unit | pure helpers only (CIK pad, period-type, serialize policy) | plain pytest |

VCR wiring: copy the fork's `tests/conftest.py` `vcr_config` pattern into `sidecar/tests/conftest.py` (`record_mode=once`, match on method/host/path/query, filter User-Agent, decode compressed).

Golden lifecycle: goldens are written once at fixture creation, committed, then asserted byte-equal on every run. Intentional regeneration ONLY via `GOLDEN_UPDATE=1` with the diff explained in the commit message. `check_drift.sh` validates committed goldens against freshly regenerated Zod.

Target: hundreds of cases = per typed form 5-15 real accessions x (model + parity + golden-Zod) + financials across ticker classes (mega-cap, REIT, bank, IFRS/ADR e.g. INFY, fund) + discovery/search/content cases.

### SEC recording budget (HARD RULES for unattended runs)

- Recording only inside a unit's step 5, bounded: <= ~60 new HTTP interactions per unit, throttle respected (edgartools native).
- `record_mode=once` — existing cassettes never re-hit SEC. Re-runs are offline.
- Any 429: stop recording immediately, mark unit `blocked(rate)`, continue with non-network work.
- Never run unbounded sweeps (no "fetch all filings since X" without `limit`).
- Cassette size discipline: prefer XML-data-rich filings for form tests; giant HTML content tests use <= 3 representative filings; repo fixture budget ~300MB total.
- Edge-case accession numbers: mine read-only from `~/Projects/secret-project/tests/fixtures/kd/edgar/` (682 Form4, 922 13D, 576 13F, 2100+ 8-K) + fork `docs/*.md` + EFTS search.

## Quality gates (every unit, before `done`)

```
cd sidecar && ruff check --fix . && ruff format .        # fork's ruff
pyright sidecar/                                          # scoped to sidecar only
pytest sidecar/tests -q -m "not live"
./sidecar/scripts/check_drift.sh                          # openapi + zod regen clean
cd sidecar/ts && bunx eslint --fix src tests && bun test
```

Commit per unit on green: `git add <unit files> && git commit -m "sidecar: U## <scope>"`. Neutral wording in messages (no delete/remove/prune words). Never `git push`.

## Session Protocol (each /loop iteration)

1. `cd ~/Projects/edgartools`. Read THIS file fully. Read fork `CLAUDE.md` if first touch this session.
2. Pick unit: first `in-progress`, else first `todo` in table order. If it needs SEC recording and `SEC_EDGAR_USER_AGENT` is unset -> mark `blocked(env)` + pick next non-network unit.
3. Set unit state `in-progress` (edit Units table only).
4. Execute per the Form Unit Recipe (form units) or the unit's scope line (infra units). A unit too big to finish in one iteration: split into `U##a/U##b` rows in the table, finish the first.
5. Run ALL quality gates. Green -> state `done`, append one Log line (`U## | done | key findings/decisions`), commit.
6. Failure: max 3 fix attempts -> state `blocked(<reason>)` + Log line with all 3 attempts' evidence, commit safe artifacts only, move on.
7. Edit only: Units states, splits, Log, Open decisions. Design sections are STABLE — changing them requires the user.
8. Stop the iteration after ONE unit (or when blocked). All units done -> final Log line `ALL DONE` and report. No executable unit left, or two consecutive zero-progress iterations -> `HALT <reason>` per Loop-session rules and end the loop.

## Form Unit Recipe (every P4 unit)

1. **Inventory**: read fork docs for the form (`docs/*.md`) + the data object source. Form docs are comprehensive but MAYBE slightly outdated or inaccurate (user, 2026-06-12) — verify every documented claim against the data object source and real filings, never trust blindly; record discrepancies in the unit Log. Write the field manifest as the parity-gate test skeleton (every public attr/property listed: captured | excluded+why).
2. **Models**: `app/models/forms/<form>.py` — full fidelity, `kind` literal, nested models for tables/footnotes/signatures. Register in envelope union.
3. **Converter**: `app/converters/forms/<form>.py` — explicit field-by-field from the edgartools object. No `vars()`, no `getattr` loops.
4. **Parity gate**: finish the introspection test; it must FAIL if edgartools grows a field this converter misses.
5. **Fixtures**: pick 5-15 real accessions per this form's edge-case matrix; record cassettes (budget rules).
6. **Integration tests**: envelope endpoint per fixture; assert real values (names, amounts, dates — not just parse-success); dump goldens.
7. **Codegen**: regen openapi + zod; bun test validates new goldens.
8. Quality gates; state `done`; commit.

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
| U00 | P0 | Scaffold: `sidecar/` pyproject (local `edgar` path dep), app skeleton, settings, identity boot, `/health`, Dockerfile, compose.yaml, ruff/pyright config | done |
| U01 | P0 | `serialize.py` policy + common models (FilingRef/FilingsPage/EntityRef/FilingEnvelope sans union) + exception->status mapping + CIK helpers (unit-tested) | done |
| U02 | P0 | Test harness: pytest+VCR wiring (fork conventions), golden-dump helper, live marker, budget-guard helper; first cassette+test (`/health`, `/tickers`) | done |
| U03 | P0 | Codegen: evaluate+pick tool (comet_ask), export_openapi.py, generate_zod.sh, check_drift.sh, ts/ scaffold (bun, eslint, zod), first golden->Zod test green | done |
| U10 | P1 | `/filings` + `/filings/current` (paging, owner filter) | done |
| U11 | P1 | `/search` EFTS full-text (verify pagination depth past 100/page) | done |
| U12 | P1 | `/tickers` full map (exchange field) | todo |
| U20 | P2 | `/filing/{accession}` envelope: multi-entity, related docs, `data=null` | todo |
| U21 | P2 | `/content` (markdown/text/html) + `/sections` | todo |
| U22 | P2 | `/attachments` list + `/attachments/{seq}` content | todo |
| U30 | P3 | `/company/{id}` full-fidelity profile + `/submissions` | todo |
| U31 | P3 | `/financials` annual+quarterly: IS/BS/CF/equity/comprehensive + cover, raw+standardized views, dimensions flag, `/metrics` scalars | todo |
| U32 | P3 | `/financials/multi` (XBRLS) + `/financials/ttm` | todo |
| U33 | P3 | `/facts` + `/facts/concept/{c}` + `/facts/search` (preserve form/filed/accn) | todo |
| U34 | P3 | `/filing/{accession}/xbrl` per-filing statements | todo |
| U40 | P4 | Form 4 typed data (ownership base machinery shared with 3/5) | todo |
| U41 | P4 | Form 3 | todo |
| U42 | P4 | Form 5 | todo |
| U43 | P4 | 8-K + 6-K/CurrentReport | todo |
| U44 | P4 | SC 13D + SC 13G | todo |
| U45 | P4 | 13F (multi-part merge, `is_multi_part`) | todo |
| U46 | P4 | 10-K (items/sections/auditor + financials linkage) | todo |
| U47 | P4 | 10-Q | todo |
| U48 | P4 | 20-F + 40-F | todo |
| U49 | P4 | Form 144 | todo |
| U50 | P4 | Form D | todo |
| U51 | P4 | Form C (+C-U/C-AR/C-TR) | todo |
| U52 | P4 | Proxy family (DEF 14A et al.) | todo |
| U53 | P4 | S-1 + DRS | todo |
| U54 | P4 | S-3 family | todo |
| U55 | P4 | 424B family + 497K | todo |
| U56 | P4 | NPORT FundReport | todo |
| U57 | P4 | N-MFP + N-CEN + N-CSR + N-PX (split if huge) | todo |
| U58 | P4 | EFFECT + 10-D (CMBS) | todo |
| U60 | P5 | Full sweep: all goldens x Zod strict, openapi snapshot, docker build + container `/health`, fixture census in README | todo |
| U61 | P5 | README runbook + consumer wiring notes (KD compose snippet + zod copy path — documentation only) | todo |

## Open decisions

| # | Question | Owner | Resolve |
|---|---|---|---|
| D1 | Codegen tool pick (+ Zod major it emits) | session | RESOLVED U03: orval@8.17.0 + zod@4.4.3, evidence in Log |
| D2 | `search_filings`/EFTS pagination past 100/page | session | RESOLVED U11: fixed 100/page (size ignored), from<=9900, cap details in Log |
| D3 | 13F multi-part merge behavior in `f.obj()` | session | U45 empirical (BlackRock/Vanguard) |
| D4 | Proxy/comp-table structure depth in edgartools | session | U52 inventory step |
| D5 | Sentry/error-tracking env gate | user | park until KD wiring |

## Log

(append-only; `U## | state | one-line findings`)

U00 | done | Gates run: ruff+pyright+TestClient boot checks (pytest/drift/ts gates land with U02/U03). Findings: edgar.core.get_identity() prompts interactively when unset -> /health reads EDGAR_IDENTITY env directly; EDGAR_RATE_LIMIT_PER_SEC is edgar-native (httpclient.py, lib default 9) -> sidecar pins 8 at boot before client creation; EDGAR_LOCAL_DATA_DIR/EDGAR_USE_LOCAL_DATA are edgar-native passthrough. Pins: fastapi 0.136.3, uvicorn 0.49.0, pytest 9.0.3, vcrpy 8.1.1, pytest-vcr 1.0.2, httpx 0.28.1, ruff 0.15.17, pyright 1.1.410 (dev dep; not on PATH). Ruff mirrors fork rules minus retired PD901 and minus tests/ exclude. Watch for U02: starlette deprecates plain-httpx TestClient (wants httpx2) but edgartools pins httpxthrottlecache<0.5.0 to stay on plain httpx. Dockerfile build context = fork root (editable ../ dep); container validation deferred to U60 per plan.

U02 | done | conftest mirrors fork vcr_config (once-mode, method/scheme/host/port/path/query match, UA+Auth filtered, decode_compressed) + pinned shared vcr_cassette_dir (pytest-vcr defaults to per-test-file dirs); budget guard via before_record_response counter (fires only while recording, hard-fails >60 new interactions/run); golden helper byte-equal asserts with GOLDEN_UPDATE=1 regeneration; identity env defaulted for offline replay. First cassette company_tickers_exchange.yaml (566KB, 1 interaction, UA verified filtered); replay offline 0.7s; first golden health/ok.json. 63 tests green; ruff+pyright clean. WARNING: root .venv + uv.lock created by a wrong-cwd uv run at 00:31 (no-deletion rule, user to remove); ALWAYS cd sidecar explicitly - shell state does not persist between Bash calls.
U01 | done | serialize.py strict scalar coercers (NaN/NaT/inf->null, bool refused for int/float, ISO-only date strings); cik.py pad_cik/parse_entity_id (ascii-digit guard vs unicode isdigit); models/common.py WireModel base with extra=forbid (anti-silent-drop) + CIK/ACCESSION regex patterns, FilingEnvelope.data typed None until U40 union; errors.py maps TooManyRequestsError/TooManyRequestsException->429 (+Retry-After header), IdentityNotSetException->503, InvalidDateException + enums.ValidationError->422, DataObjectException->502, httpx HTTPStatusError->404/429/502, other httpx->502, unknown exceptions stay unmapped (loud 500). 61 tests green (unit: serialize/cik/errors; integration: handler wiring via TestClient, no VCR needed). pytest config: pythonpath=["."], live marker registered. Gates: ruff+pyright+pytest (drift/ts land U03).
U03 | done | D1 RESOLVED: orval@8.17.0 + zod@4.4.3 (exact pins). Evidence: comet x2 (orval actively maintained with schemas-only zod mode; kubb has tracked z.union-not-discriminatedUnion bug; openapi-zod-client stalled Feb-2025, OpenAPI-3.0-targeted, zodios-coupled; typed-openapi incomplete OpenAPI support, simplified $ref) + empirical synthetic spec (discriminator+anyOf-null+const+pattern): byte-identical regen, strictObject everywhere, anyOf-null->union(null), const->literal, date->zod.iso.date(), generateReusableSchemas yields named component schemas. oneOf+discriminator emits zod.union of strict kind-literal members (orval zod plugin source has no discriminatedUnion path) = plan's acceptable equivalent: identical accept/reject set, TS narrowing via z.infer works; 8/8 runtime assertions green incl. strict-reject of unknown keys inside union members. Caveats: ajv@8.17.1 required as explicit dev dep (peer of orval's spec validation); orval autodetects zod major from package.json pin. Pipeline: export_openapi.py (run python -m from sidecar/; snapshot pytest), generate_zod.sh, check_drift.sh (worktree-vs-index diff + untracked check + bun test; negative-tested with perturbed staged spec), ts/ scaffold bun+eslint10 flat+tsc strict; goldens.test.ts walks fixtures/responses and FAILS on any endpoint dir missing a schema mapping. eslint lints generated output (passes recommended rules unmutated). Gates: 64 pytest, eslint, bun test 4, drift all green.
U10 | done | /filings: bounded date ranges only (open-ended would expand to every index since 1994 -> 422), year/quarter XOR date_from/date_to (422 on both; get_filings silently prefers filing_date), id param via parse_entity_id -> filter(cik=) or filter(ticker=). /filings/current: get_current_entries_on_page directly (public fn; get_current_filings hides start), client-side form re-filter per edgartools #501 (SEC ignores type=), has_more from raw pre-filter page fullness, page_size membership-checked in code (pydantic Literal[int] does NOT coerce query strings -> literal_error 422). NEW wire policy: datetimes UTC-Z via serialize.to_utc_datetime (naive raises - SEC mixes Eastern/UTC; feed accepted -04:00 normalized, pydantic renders Z, orval emits iso.datetime offset:true so both pass). Models tightened: nullable wire fields now REQUIRED (no = None defaults) -> zod drops .optional(), matching absent->null convention. CRITICAL harness find: edgartools 30-min disk HTTP cache (~/.edgar/_tcache) swallows requests before VCR -> conftest isolates EDGAR_LOCAL_DATA_DIR to session tmp dir; identity fixture now session-scoped (module TestClient boots before function autouse). Cassettes: index test 7.9MB (2025Q1 form.gz + tickers, scenarios share one cassette via warm in-session cache), current 34KB; ~5 new interactions total. Ground truth: 10-K window 2025-01-06:10 total=11, first=Anixa Biosciences 0001493152-25-001787 cik 0000715446; accepted 2026-06-12T01:59:17Z. Gates: 72 pytest, pyright 0, drift+bun 10, eslint green.
U11 | done | D2 RESOLVED (live probes 2026-06-12): EFTS returns a FIXED 100 hits/response - size param is IGNORED (size=50 still returns 100; edgartools limit only truncates client-side); from= offset works for arbitrary offsets; hard cap from+size<=10000 ("Result window is too large") returned as HTTP 200 + {errorType,errorMessage} body with NO hits key -> edgartools _fetch_page would silently render 0 results; total.value caps at 10000 with relation=gte. Sidecar: /search pre-guards start+page_size<=10000 (422), detects errorType bodies (window->422, other->502), exposes total_relation eq|gte, has_more clamps to min(total,10000). Param building mirrors search_filings encoding (q/forms/items/dateRange custom/ciks/from); hit+aggregation parsing reuses edgar.search.efts._parse_hit/_parse_aggregations (single source). Ticker scoping via reference find_cik (NOT Company(ticker) - avoids a full submissions fetch), unknown ticker 404. Full-fidelity SearchResult (15 fields incl. score/file_type/document_id/items/sic/location/state/inc_state) + facet aggregations (entities/sics/states/forms). Cassette 2.3MB (~6 small JSON interactions). Ground truth: "cybersecurity incident" 8-K 2024-H1 total=200 eq, first hit Brandywine Realty 8-K/A 0001193125-24-147625 Item 1.05 doc d774339d8ka.htm. Gates: 74 pytest, pyright 0, drift+bun 13, eslint green.
