## AI Core & MCP Server/Tools

### Overview

`edgar.ai` is an optional sub-package (`pip install "edgartools[ai]"`) that adds three orthogonal capabilities to EdgarTools: (1) an AI-optimized text-formatting layer (`formats.py`, `core.py`) for turning edgar objects into token-efficient LLM input; (2) convenience helpers (`helpers.py`) for high-level filing analysis workflows; and (3) a full Model Context Protocol (MCP) server (`mcp/`) that exposes 13 intent-based tools plus 7 pre-built analysis prompts to any MCP-compatible client (Claude Desktop, Cline, etc.). The package also ships an "AI Skills" system (not in scope here) for packaging documentation for Claude Desktop.

---

### Public API Surface

| Symbol | file:line | Purpose |
|--------|-----------|---------|
| `AIEnabled` | `edgar/ai/core.py:155` | Abstract base mixin for AI-capable edgar objects |
| `TokenOptimizer` | `edgar/ai/core.py:15` | Token estimation + progressive content truncation |
| `SemanticEnricher` | `edgar/ai/core.py:64` | Concept definitions, relationships, value interpretation |
| `enhance_financial_fact_llm_context` | `edgar/ai/core.py:205` | Top-level function enriching a FinancialFact for LLM consumption |
| `check_ai_capabilities` | `edgar/ai/core.py:311` | Returns dict of available capabilities (mcp, tiktoken, etc.) |
| `FinancialFactAIWrapper` | `edgar/ai/core.py:265` | Non-invasive wrapper adding AI methods to existing FinancialFact instances |
| `to_markdown_kv` | `edgar/ai/formats.py:16` | Dict → Markdown Key-Value string (60.7% LLM accuracy benchmark) |
| `to_tsv` | `edgar/ai/formats.py:56` | List[Dict] → TSV with header row; most token-efficient for tables |
| `get_filings_by_period` | `edgar/ai/helpers.py:46` | Wrapper for `get_filings(year, quarter, ...)` |
| `get_today_filings` | `edgar/ai/helpers.py:92` | Wrapper for `get_current_filings()` |
| `get_revenue_trend` | `edgar/ai/helpers.py:122` | `Company.income_statement(periods, annual)` with clear API |
| `get_filing_statement` | `edgar/ai/helpers.py:176` | XBRL statement from specific filing (income/balance/cash_flow) |
| `compare_companies_revenue` | `edgar/ai/helpers.py:246` | Dict[ticker → MultiPeriodStatement] for multiple companies |
| `filter_by_industry` | `edgar/ai/helpers.py:306` | Zero-API-call industry filter using local SIC reference data |
| `filter_by_company_subset` | `edgar/ai/helpers.py:388` | Filter filings by CompanySubset or DataFrame with 'cik' column |
| `get_pharmaceutical_companies` (+ 9 others) | `edgar/ai/helpers.py:484–676` | Industry convenience getters wrapping `edgar.reference` |
| `install_skill` | `edgar/ai/__init__.py:81` | Install EdgarTools AI skill to `~/.claude/skills/` |
| `package_skill` | `edgar/ai/__init__.py:240` | Create ZIP for Claude Desktop upload |
| `AI_AVAILABLE`, `MCP_AVAILABLE`, `TIKTOKEN_AVAILABLE` | `edgar/ai/__init__.py:68` | Runtime capability flags |
| `main` | `edgar/ai/mcp/server.py:421` | MCP server entry point (stdio or HTTP) |
| `test_server` | `edgar/ai/mcp/server.py:509` | Pre-flight check: edgar, mcp, tools, EDGAR_IDENTITY |
| `TOOLS` | `edgar/ai/mcp/tools/base.py:19` | Global dict registry: tool name → {name, description, handler, schema} |
| `tool` | `edgar/ai/mcp/tools/base.py:90` | `@tool(name, description, params, required)` decorator |
| `ToolResponse` | `edgar/ai/mcp/tools/base.py:27` | Dataclass: success, data, error, error_code, suggestions, next_steps |
| `success` / `error` | `edgar/ai/mcp/tools/base.py:60,73` | Factory helpers for ToolResponse |
| `resolve_company` | `edgar/ai/mcp/tools/base.py:188` | Flexible identifier → Company object (ticker, CIK, name) |
| `call_tool_handler` | `edgar/ai/mcp/tools/base.py:146` | Async router: name + arguments → awaits registered handler |
| `classify_error` | `edgar/ai/mcp/tools/base.py:445` | Maps exceptions to {error_code, message, suggestions} dict |

---

### Key Classes

**`TokenOptimizer`** (`edgar/ai/core.py:15`) — stateless utility class
- `estimate_tokens(content) -> int` — ~4 chars/token heuristic — `:19`
- `optimize_for_tokens(content, max_tokens) -> dict` — progressive summarization using priority key list — `:30`

**`SemanticEnricher`** (`edgar/ai/core.py:64`) — stateless, uses class-level dicts
- `get_concept_definition(concept) -> Optional[str]` — strips namespace prefix, looks up CONCEPT_DEFINITIONS — `:93`
- `get_related_concepts(concept) -> List[str]` — CONCEPT_RELATIONSHIPS map — `:99`
- `interpret_value(concept, value, unit, period_type) -> str` — scale/sign interpretation strings — `:106`

**`AIEnabled`** (`edgar/ai/core.py:155`) — abstract base mixin (ABC)
- `to_llm_context(detail_level, max_tokens) -> Dict[str, Any]` — abstract, must implement — `:163`
- `to_agent_tool() -> Dict[str, Any]` — concrete; returns `{data, context, metadata}` using `to_dict()` + `to_llm_context()` — `:177`
- `get_semantic_description() -> str` — abstract — `:195`

**`FinancialFactAIWrapper`** (`edgar/ai/core.py:265`) — adapter (not a subclass of AIEnabled)
- `to_llm_context(detail_level, max_tokens)` — delegates to `enhance_financial_fact_llm_context` — `:276`
- `to_agent_tool()` — returns `{data, context, metadata}` dict — `:282`
- `get_semantic_description()` — builds plain-English string from fact attributes — `:303`

**`ToolResponse`** (`edgar/ai/mcp/tools/base.py:27`) — dataclass
- `to_dict() -> dict` — excludes None/empty fields — `:40`
- `to_json() -> str` — `json.dumps(to_dict(), indent=2, default=str)` — `:55`

**`Server` (mcp.server.Server)** — instantiated as `app = Server("edgartools", instructions=SERVER_INSTRUCTIONS)` at `edgar/ai/mcp/server.py:136`; handlers attached via decorators `@app.list_tools()`, `@app.call_tool()`, `@app.list_resources()`, `@app.read_resource()`, `@app.list_prompts()`, `@app.get_prompt()`.

---

### Class Hierarchy

```
ABC
└── AIEnabled  (abstract mixin — edgar/ai/core.py:155)
    [not implemented by FinancialFactAIWrapper — it is a separate adapter]

object
├── TokenOptimizer  (static methods only)
├── SemanticEnricher  (class methods + class-level dicts)
├── FinancialFactAIWrapper  (wraps FinancialFact, delegates to enhance_financial_fact_llm_context)
└── ToolResponse  (dataclass)

mcp.server.Server  (external dep)
└── app  (module-level singleton in server.py)
    ├── @list_tools  → queries TOOLS registry
    ├── @call_tool   → routes via call_tool_handler
    ├── @list_resources / @read_resource → inline docs
    └── @list_prompts / @get_prompt → delegates to prompts.py

Tool registration (functional, not class-based):
TOOLS dict ← populated by @tool decorator at module import time
    Each entry: { name, description, handler (async fn), schema (JSON Schema object) }
```

---

### Configuration & Options

| Option | Type | Default | Effect |
|--------|------|---------|--------|
| `EDGAR_IDENTITY` env var | `str` | None | Set SEC identity; warning logged if missing; `set_identity()` called at startup |
| `--transport` CLI arg | `"stdio"` \| `"streamable-http"` | `"stdio"` | Server transport; HTTP uses uvicorn+Starlette on `/mcp` |
| `--host` CLI arg | `str` | `"0.0.0.0"` | HTTP bind host |
| `--port` CLI arg | `int` | `8000` | HTTP bind port |
| `--test` / `-t` CLI flag | `bool` | `False` | Run `test_server()` pre-flight check and exit |
| `to_markdown_kv(max_tokens)` | `int` | `2000` | Token ceiling; truncates at `max_tokens * 4` chars |
| `to_tsv(max_tokens, limit)` | `int`, `int` | `2000`, `10` | Token ceiling + max rows |
| `edgar_company(include)` | `list[str]` | `["profile", "financials", "filings"]` | Which sections to build |
| `edgar_company(periods)` | `int` | `4` | Periods of financial data |
| `edgar_company(period)` | `"annual"\|"quarterly"\|"ttm"` | `"annual"` | Period type; TTM skips balance sheet |
| `edgar_trends(concepts)` | `list[str]` | `["revenue", "net_income"]` | XBRL concepts to trend |
| `edgar_trends(periods)` | `int` | `8` | Number of periods |
| `edgar_trends(include_growth)` | `bool` | `True` | Compute YoY + CAGR |
| `edgar_screen(limit)` | `int` | `25` (max 100) | Max companies returned |
| `edgar_monitor(limit)` | `int` | `20` (max 100) | Max filings returned |
| `edgar_ownership(days)` | `int` | `90` | Lookback for insider transactions |
| `edgar_notes(detail)` | `"minimal"\|"standard"\|"full"` | `"standard"` | `"full"` includes DataFrame rows |
| `edgar_filing(detail)` | `"minimal"\|"standard"\|"full"` | `"standard"` | Passed into `obj.to_context(detail=detail)` |

---

### Data Flow / Lifecycle

**Server startup:**
1. `main()` parses CLI args → calls `setup_edgar_identity()` (reads `EDGAR_IDENTITY` env, calls `set_identity()`)
2. Chooses transport: `_run_stdio()` uses `mcp.server.stdio.stdio_server`; `_run_http()` uses `StreamableHTTPSessionManager` + Starlette + uvicorn on `/mcp`
3. `asyncio.run(run_server())` starts event loop; `InitializationOptions` carries `server_name="edgartools"`, `server_version`, capabilities

**Tool registration (lazy, import-time):**
- `_import_tools()` is called on first `list_tools` or `call_tool` request (not at startup)
- Each tool module (`company.py`, `filing.py`, etc.) executes `@tool(...)` decorators at import, which write into the module-level `TOOLS: dict`
- `TOOLS` is keyed by tool name string; value has `handler` (async callable) + `schema` (JSON Schema)

**Tool call flow:**
1. MCP client calls `call_tool(name, arguments)`
2. `call_tool_handler(name, arguments)` looks up `TOOLS[name]["handler"]`
3. Handler `await`s, returns `ToolResponse`
4. Server serializes `ToolResponse.to_json()` → `TextContent(type="text", text=...)`
5. On exception: `classify_error(e)` produces structured `{error_code, message, suggestions}` → `error(...)` ToolResponse

**Format helpers (`formats.py`):**
- `to_markdown_kv(data, max_tokens)`: iterates dict keys in insertion order, title-cases key names, builds `**Key:** value` lines, hard-truncates at `max_tokens * 4` chars with `[Truncated for token limit]` indicator
- `to_tsv(rows, headers, max_tokens, limit)`: tab-joins header row + up to `limit` data rows, appends `[Showing N of M rows]` if truncated, hard-truncates by estimated rows that fit

**AI Core helpers (`core.py`):**
- `enhance_financial_fact_llm_context(fact, detail_level, max_tokens)` — calls `fact.to_llm_context()` first (existing implementation), then adds `definition`, `interpretation` (standard+), `related_concepts`, `metadata`, `calculation_context` (detailed only), then optionally calls `TokenOptimizer.optimize_for_tokens()`
- `TokenOptimizer.optimize_for_tokens()` — iterates priority keys `['concept','value','period','context','quality','confidence','source']`; adds `_truncated=True` flag if content was dropped

---

### Design Patterns

- **Decorator-based tool registry**: `@tool(name, description, params, required)` writes into module-level `TOOLS` dict at import time. No class hierarchy needed. Server retrieves from `TOOLS` on demand. Pattern: Service Locator / self-registering plugins.
- **SDK-MCP-API-HYBRID (pattern UUID 1376423d)**: All business logic in edgar SDK layer (`Company`, `Filing`, `get_facts()`, etc.). MCP tools are thin adapters — parse args, call SDK, format response, return `ToolResponse`. Zero business logic in tool handlers.
- **Lazy tool import**: `_import_tools()` is called inside `list_tools` and `call_tool` handlers, not at server startup. Avoids import errors during startup if individual tool modules have issues.
- **Intent-based tools**: Tools named by user intent (`edgar_company`, `edgar_read`) not API method (`get_company_facts`, `get_filing_xbrl`). Each tool accepts multiple identifier formats.
- **`next_steps` guidance**: Every `success(data, next_steps=[...])` response includes suggested follow-up tool calls — drives chained workflows without the LLM needing to know the tool graph.
- **`classify_error` lazy imports**: Each error type is caught with a try/except ImportError guard to avoid circular deps and optional-dep issues. Falls back to ValueError and a generic handler.
- **Adapter pattern (FinancialFactAIWrapper)**: Wraps existing `FinancialFact` objects without modifying the source class, adding AI methods non-invasively.
- **Format research-driven defaults**: `to_markdown_kv` chosen for Markdown-KV format based on 60.7% LLM accuracy benchmark; `to_tsv` chosen for tabular data token efficiency. Explicitly cited in module docstrings (`edgar/ai/formats.py:1–9`).

---

### Tool Surface (All 13 Tools)

| Tool | File | Required params | Key edgar calls |
|------|------|-----------------|-----------------|
| `edgar_company` | `tools/company.py` | `identifier` | `resolve_company`, `company.get_facts()`, `facts.income_statement/balance_sheet/cashflow_statement`, `company.get_filings`, `company.income_statement(period='ttm')` |
| `edgar_filing` | `tools/filing.py` | none (identifier+form OR input) | `resolve_company`, `company.get_filings`, `find(accession)`, `filing.obj()`, `obj.to_context(detail)` |
| `edgar_read` | `tools/reader.py` | none (accession_number OR identifier+form) | `filing.obj()`, `obj[section_key]`, `obj.financials`, `obj.items`, `obj.executive_compensation` |
| `edgar_search` | `tools/search.py` | none | `find_company(query, top_n)`, `company.get_filings(form)`, `get_filings(form)` |
| `edgar_text_search` | `tools/text_search.py` | `query` | `search_filings(query, forms, ticker, cik, start_date, end_date, limit)` (edgar.search.efts EFTS) |
| `edgar_compare` | `tools/compare.py` | none (identifiers OR industry) | `company.get_facts()`, `facts.get_revenue/net_income/...`, `facts.time_series("Revenue")`, `facts.income_statement/balance_sheet` |
| `edgar_ownership` | `tools/ownership.py` | `identifier`, `analysis_type` | `company.get_filings(form="4")`, `filing.obj()`, `company.get_filings(form="13F-HR")`, `obj.compare_holdings()` |
| `edgar_monitor` | `tools/monitor.py` | none | `get_current_filings(form, page_size)` |
| `edgar_trends` | `tools/trends.py` | `identifier` | `company.get_facts()`, `facts.time_series(xbrl_concept, periods)` |
| `edgar_screen` | `tools/screen.py` | at least one of industry/sic/exchange/state | `get_companies_by_industry`, `get_companies_by_exchanges`, `get_companies_by_state` (edgar.reference) — zero SEC API calls |
| `edgar_fund` | `tools/fund.py` | `action` | `Fund(identifier)`, `find_funds(query)`, `fund.get_portfolio()`, `fund.get_latest_report(form)`, `find_bdc`, `get_bdc_list()`, `bdc.portfolio_investments()` |
| `edgar_proxy` | `tools/proxy.py` | `identifier` | `company.get_filings(form="DEF 14A")`, `filing.obj()`, `proxy.peo_total_comp`, `proxy.executive_compensation`, `proxy.summary_compensation_table`, `proxy.beneficial_ownership` |
| `edgar_notes` | `tools/notes.py` | `identifier` | `company.get_filings(form)`, `filing.obj()`, `obj.notes`, `notes.search(topic)`, `note.to_context(detail)` |

**Section maps for `edgar_read`** (`tools/reader.py:28–66`):
- 10-K: `business`, `risk_factors`, `mda`, `financials`, `controls`, `legal`
- 10-Q: `financials`, `mda`, `risk_factors`, `legal`, `controls`, `market_risk`
- 20-F: `business`, `risk_factors`, `mda`, `financials`, `directors`, `shareholders`, `financial_info`, `controls`
- 8-K: `items`, `press_release`, `earnings`
- DEF 14A: `compensation`, `pay_performance`, `governance`
- SC 13D/13G: `ownership`, `purpose`
- 13F-HR: `holdings`, `summary`

**`edgar_company` TTM mode** (`tools/company.py:155–174`): Uses `Company.income_statement(period='ttm')` and `Company.cashflow_statement(period='ttm')`; balance sheet is explicitly skipped with a note since it is point-in-time, not trailing.

**`edgar_trends` CONCEPT_MAP** (`tools/trends.py:24–33`): `revenue→Revenue`, `net_income→NetIncomeLoss`, `total_assets→Assets`, `total_liabilities→Liabilities`, `equity→StockholdersEquity`, `gross_profit→GrossProfit`, `operating_income→OperatingIncomeLoss`, `eps→EarningsPerShareBasic`. Deduplicates by period_end keeping the largest value (consolidation vs segment issue).

**`edgar_compare` derived metrics** (`tools/compare.py:269–304`): `margins` derives net_margin and gross_margin inline from fetched revenue/net_income/gross_profit values. `growth` fetches `time_series("Revenue", periods=(periods+1)*5)`, filters to FY rows, computes YoY from top two values.

---

### MCP Prompts (7 pre-built workflows)

Defined in `edgar/ai/mcp/tools/prompts.py`. Each is a `mcp.types.Prompt` with `PromptArgument` specs + a renderer function that returns a `GetPromptResult` containing a `PromptMessage(role="user", ...)` with a step-by-step multi-tool workflow.

| Prompt | Arguments | Tool chain |
|--------|-----------|------------|
| `due_diligence` | identifier | company → trends → read(10-K risk_factors) → read(8-K) → ownership(insiders) |
| `earnings_analysis` | identifier | read(8-K earnings) → trends(annual+quarterly) → compare(peers) → read(mda) |
| `industry_overview` | industry | screen → compare → trends → monitor |
| `insider_monitor` | identifier | company(profile) → ownership(insiders) → trends → monitor(form=4) |
| `fund_analysis` | identifier | fund(lookup) → fund(portfolio) → fund(money_market) → company(holdings) → fund(search) |
| `filing_comparison` | identifier, form?, compare_to? | company(profile) → read(2 filings) → compare → trends (cross-company or temporal) |
| `activist_tracking` | identifier | company → read(SC 13D) → read(SC 13G) → proxy → text_search(activist) → ownership(insiders) |

`get_prompt(name, arguments)` uses `inspect.signature` to validate required params and pass kwargs to the renderer — `edgar/ai/mcp/tools/prompts.py:365–393`.

---

### Resources

Two MCP resources exposed (`server.py:194–220`):
- `edgartools://docs/quickstart` — inline quickstart markdown with JSON examples for all 13 tools
- `edgartools://docs/tools` — dynamically generated from `TOOLS` registry: iterates tool names + descriptions + parameter schemas

---

### Server Launch Paths

**Entry point 1 — console script** (`pyproject.toml:121`):
```
edgartools-mcp = "edgar.ai.mcp.server:main"
```

**Entry point 2 — module** (`edgar/ai/__main__.py:8–11`):
```
python -m edgar.ai  →  from edgar.ai.mcp import main; main()
```

**Entry point 3 — direct** (`edgar/ai/mcp/server.py:572`):
```
python edgar/ai/mcp/server.py  →  main()
```

**HTTP transport** (`server.py:468–506`): `StreamableHTTPSessionManager(app, json_response=True, stateless=True)` + Starlette `Route("/mcp", _MCPEndpoint())` + uvicorn. Uses `app.version = version` instead of passing via `InitializationOptions` (HTTP mode never calls `app.run()`).

**Test mode**: `--test` flag runs `test_server()` which checks edgar import, mcp import, tool registration count, and EDGAR_IDENTITY; exits 0/1.

---

### Cross-Domain Interactions

**edgar.ai imports from:**
- `edgar` (Company, find_company, get_filings, get_current_filings, find, set_identity)
- `edgar.entity.core` (CompanyNotFoundError)
- `edgar.entity.entity_facts` (NoCompanyFactsFound)
- `edgar.xbrl.xbrl` (XBRLFilingWithNoXbrlData)
- `edgar.httprequests` (TooManyRequestsError, SSLVerificationError, IdentityNotSetException)
- `edgar.sgml.sgml_parser` (SECIdentityError, SECFilingNotFoundError)
- `edgar.search.efts` (search_filings)
- `edgar.reference` (get_companies_by_industry, get_companies_by_exchanges, get_companies_by_state, get_pharmaceutical_companies, etc.)
- `edgar.funds.core` (Fund, FundCompany, FundSeries, FundClass, find_funds)
- `edgar.bdc.search` (find_bdc)
- `edgar.bdc.reference` (get_bdc_list)
- `edgar.paths` (get_claude_skills_directory)
- `edgar.__about__` (__version__)

**edgar.ai consumed by:**
- No other `edgar.*` module imports from `edgar.ai` — it is a pure leaf package
- Consumed by external MCP clients (Claude Desktop, Cline, etc.) via stdio or HTTP transport

---

### Gotchas & Notable Behaviors

- **Optional dependency guard**: `MCP_AVAILABLE` and `TIKTOKEN_AVAILABLE` are checked at import time in `__init__.py`. If `mcp` is absent, the deprecated `MCPServer`/`EdgarToolsServer` classes raise `ImportError` when instantiated (not at import). The server itself cannot be started without `mcp`.
- **Lazy `_import_tools()`**: Tools are NOT registered at server startup — only when the first `list_tools` or `call_tool` arrives. This means a broken tool module won't crash the server on launch, but will fail the first tool call.
- **Deprecated class API**: `MCPServer` and `EdgarToolsServer` both raise `DeprecationWarning` (not `ImportError`) when MCP is available. The real API is `from edgar.ai.mcp import main, test_server`.
- **`resolve_company` tries two variants**: raw identifier + `.upper()` in `dict.fromkeys` order (deduplication), then integer CIK fallback — `base.py:215–229`.
- **`edgar_ownership` analysis_type="institutions"** is explicitly rejected with a helpful error explaining SEC has no reverse-lookup API for institutional holders of a stock — `ownership.py:73–84`.
- **`edgar_company` period=ttm skips balance sheet**: Explicitly returns `{"note": "TTM not applicable for Balance Sheet..."}` — `company.py:166`.
- **`edgar_proxy` XBRL gate**: If `proxy.has_xbrl` is False, returns partial result with a note explaining XBRL is absent for smaller reporting companies, EGCs, SPACs, and registered investment companies — `proxy.py:144–154`.
- **`edgar_trends` deduplication**: When multiple values exist per period_end (segment vs consolidated total), the highest numeric_value is kept — `trends.py:113–117`. This silently resolves the common segment-vs-total reporting issue.
- **`edgar_screen` zero API calls**: All filtering uses local reference DataFrames (`edgar.reference`). First call may be slow (data download), subsequent calls cached.
- **HTTP transport `stateless=True`**: Each HTTP request is an independent session. No server-side session state between calls.
- **`classify_error` lazy imports**: Each exception type is guarded by `try/except ImportError` — this is intentional to avoid circular imports and to allow the error classifier to work even if optional modules aren't installed.
- **`truncate_text` soft-break**: Tries to break at the last `\n` if it's within the last 20% of the max — `base.py:253–257`. Appends `\n\n... (truncated)`.
- **`edgar_filing` skips amendments for structured forms**: Forms in `_PREFER_ORIGINAL` (`{10-K, 10-Q, 20-F, 40-F}`) fetch with `amendments=False` since amendments often have incomplete XBRL data — `filing.py:104–106`.
- **`to_markdown_kv` key naming**: Keys are title-cased via `.replace('_', ' ').title()` — `formats.py:43`. A key like `sic_description` becomes `**Sic Description:**`.
- **`SemanticEnricher.CONCEPT_DEFINITIONS`** contains only 12 common concepts — `core.py:68–80`. Many XBRL concepts will return `None` from `get_concept_definition`.
- **`TokenOptimizer.estimate_tokens`** uses char/4 heuristic (not tiktoken), even when tiktoken is installed — `core.py:24–28`. The `tiktoken` dependency is available but not used in `core.py`.
