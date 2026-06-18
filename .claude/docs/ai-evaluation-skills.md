## AI Evaluation, Exporters & Skills

### Overview

This domain provides a complete harness for measuring the marginal value of EdgarTools AI skill documentation on LLM-generated code and live agent behavior, plus the machinery to export/install those skills into Claude Desktop and the official `~/.claude/skills/` path. The evaluation system runs two-condition (with-skills / without-skills) A/B tests, scores outputs via regex pattern matching and an LLM-as-judge, maps failures to a constitution of quality goals, and produces actionable skill-edit recommendations. The skills themselves are YAML+Markdown content packs that `BaseSkill` subclasses point to.

---

### Public API surface

| Symbol | file:line | Purpose |
|--------|-----------|---------|
| `SECAnalysisTestCase` | `edgar/ai/evaluation/test_cases.py:24` | Single test case definition (dataclass) |
| `SEC_TEST_SUITE` | `edgar/ai/evaluation/test_cases.py:107` | 42-item predefined test list |
| `get_test_by_id` | `edgar/ai/evaluation/test_cases.py:1369` | Lookup test case by ID |
| `get_tests_by_category` | `edgar/ai/evaluation/test_cases.py:1390` | Filter by category string |
| `get_tests_by_difficulty` | `edgar/ai/evaluation/test_cases.py:1407` | Filter by "easy"/"medium"/"hard" |
| `SkillEvaluationHarness` | `edgar/ai/evaluation/harness.py:307` | Core harness; evaluate code and compare conditions |
| `ABComparison` | `edgar/ai/evaluation/harness.py:204` | Dataclass holding two EvaluationReports + improvement deltas |
| `EvaluationReport` | `edgar/ai/evaluation/harness.py:84` | Summary of multiple TestResult objects with stats |
| `TestResult` | `edgar/ai/evaluation/harness.py:35` | Single test evaluation result |
| `evaluate_code_execution` | `edgar/ai/evaluation/evaluators.py:133` | Execute code and capture stdout/err |
| `evaluate_pattern_compliance` | `edgar/ai/evaluation/evaluators.py:221` | Regex-match expected/forbidden patterns |
| `evaluate_token_efficiency` | `edgar/ai/evaluation/evaluators.py:302` | Compare code token count to budget |
| `count_tokens` | `edgar/ai/evaluation/evaluators.py:107` | Character/4 heuristic token estimator |
| `SkillTestRunner` | `edgar/ai/evaluation/runner.py:252` | API-driven runner (Anthropic SDK) — generates + evaluates |
| `load_skill_context` | `edgar/ai/evaluation/runner.py:55` | Concatenate all skill YAML files into one string |
| `extract_code_from_response` | `edgar/ai/evaluation/runner.py:119` | Strip markdown fences from LLM response |
| `GenerationResult` | `edgar/ai/evaluation/runner.py:226` | Single code-generation result from Anthropic call |
| `Constitution` | `edgar/ai/evaluation/constitution.py:50` | Parsed constitution with helper methods |
| `ConstitutionGoal` | `edgar/ai/evaluation/constitution.py:23` | One quality goal (weight, patterns, skill files) |
| `load_constitution` | `edgar/ai/evaluation/constitution.py:84` | Parse `skills/constitution.yaml` |
| `run_constitution_diagnostics` | `edgar/ai/evaluation/diagnostics.py:469` | Map ABComparison failures → constitution goals |
| `generate_skill_edit_suggestions` | `edgar/ai/evaluation/diagnostics.py:518` | Produce ranked actionable suggestions |
| `ConstitutionReport` | `edgar/ai/evaluation/diagnostics.py:121` | Aggregated diagnostics; `print_report()` and `to_dict()` |
| `AgentTestRunner` | `edgar/ai/evaluation/agent.py:700` | Live agent runner via Claude Code SDK + MCP tools |
| `AgentScore` | `edgar/ai/evaluation/agent.py:83` | tool_selection / answer_quality / efficiency scores |
| `AgentTestResult` | `edgar/ai/evaluation/agent.py:99` | One agent run result with full trace |
| `AgentTrace` | `edgar/ai/evaluation/agent.py:64` | tool_calls list, final_answer, total_turns, model |
| `JudgeScore` | `edgar/ai/evaluation/judge.py:37` | LLM judge 1-5 scores across 4 dimensions |
| `JudgeComparison` | `edgar/ai/evaluation/judge.py:63` | A/B comparison from judge scores |
| `build_judge_prompt` | `edgar/ai/evaluation/judge.py:122` | Fill `_JUDGE_PROMPT_TEMPLATE` with task + code |
| `parse_judge_response` | `edgar/ai/evaluation/judge.py:152` | Extract JSON from judge LLM response |
| `build_judge_comparison` | `edgar/ai/evaluation/judge.py:240` | Aggregate per-test JudgeScores into comparison |
| `format_judge_report` | `edgar/ai/evaluation/judge.py:296` | Pretty-print judge A/B table |
| `ClaudeCodeRunner` | `edgar/ai/evaluation/cc_runner.py:45` | Task-subagent prompt generation (no direct API call) |
| `BaseSkill` | `edgar/ai/skills/base.py:16` | ABC for all skill packages |
| `EdgarToolsSkill` | `edgar/ai/skills/core/__init__.py:16` | Built-in skill; points to core/ YAML content |
| `edgartools_skill` | `edgar/ai/skills/core/__init__.py:120` | Singleton EdgarToolsSkill instance |
| `list_skills` | `edgar/ai/skills/__init__.py:20` | Return all registered skills |
| `get_skill` | `edgar/ai/skills/__init__.py:38` | Lookup skill by name string |
| `export_claude_skills` | `edgar/ai/exporters/claude_skills.py:17` | Write skill to `~/.claude/skills/<name>/` |
| `export_claude_desktop` | `edgar/ai/exporters/claude_desktop.py:17` | Write skill ZIP for Claude Desktop upload |
| `export_skill` | `edgar/ai/exporters/__init__.py:13` | Unified dispatch to either exporter |

---

### Key classes

**SECAnalysisTestCase** (`test_cases.py:24`) — dataclass defining one evaluation scenario.
- Fields: `id`, `task`, `expected_patterns: List[str]`, `forbidden_patterns: List[str]`, `max_tokens: int = 1000`, `difficulty: str = "medium"`, `category: str = "general"`, `reference_code: Optional[str]`, `network_required: bool = False`, `tags`, `constitution_goals`, `expected_tools`, `expected_in_answer`, `max_tool_calls: int = 10`
- `__post_init__` validates difficulty ∈ {easy,medium,hard} and category ∈ 10 allowed values — raises `ValueError` otherwise
- Used both by code-gen evaluators (pattern/token scoring) and agent evaluators (tool selection / answer quality scoring)

**SkillEvaluationHarness** (`harness.py:307`) — core orchestrator for non-agent evaluation.
- `__init__(test_suite=None, execute_code=False)` — defaults to `SEC_TEST_SUITE`; `execute_code=False` skips actual code execution for safety
- `evaluate_code(test_id, code, condition, metadata) -> TestResult` — runs all three evaluators against one code string
- `run_suite(code_samples: Dict[str,str], condition, test_ids) -> EvaluationReport`
- `compare_conditions(with_skills_samples, without_skills_samples) -> ABComparison`
- `get_test(test_id)`, `list_tests()`

**EvaluationReport** (`harness.py:84`) — `__post_init__` auto-calculates `summary_stats`: total_tests, passed, failed, pass_rate, mean/min/max score, by_category, by_difficulty.
- `summary() -> str`, `to_json()`, `save(path)`

**ABComparison** (`harness.py:204`) — `__post_init__` computes `improvement` dict: score_absolute, score_relative_pct, pass_rate_absolute, pass_rate_relative_pct, skills_better (bool), by_category deltas.
- `summary() -> str`, `to_dict()`. Has optional `metadata` dict attached by runners.

**TestResult** (`harness.py:35`) — `success` property: `execution.success AND pattern.compliant`; `score` property: `evaluation.overall_score`.

**CombinedEvaluation** (`evaluators.py:356`) — wraps ExecutionResult + PatternResult + TokenResult + `overall_score`.
- Default weights without execution: `{execution:0.0, pattern:0.7, efficiency:0.3}`
- Default weights with execution: `{execution:0.4, pattern:0.4, efficiency:0.2}`

**PatternResult** (`evaluators.py:61`) — `score` = (expected_found / expected_count) − (forbidden_violations / forbidden_count * 0.5, max 50% penalty). `compliant` = all expected found AND no forbidden found.

**TokenResult** (`evaluators.py:83`) — efficiency_score: 1.0 at ≤50% of budget; linearly 1.0→0.7 from 50%→100%; linearly 0.7→0.0 from 100%→200%.

**SkillTestRunner** (`runner.py:252`) — drives the Anthropic API directly.
- `__init__(api_key=None, model="claude-sonnet-4-20250514", max_tokens=1024, skill_context=None)`; client is lazy-loaded.
- `generate_code(test_id, with_skills) -> GenerationResult`
- `generate_for_suite(test_ids, with_skills) -> Dict[str, GenerationResult]`
- `run_ab_comparison(test_ids, runs_per_condition, diagnose) -> ABComparison` — optional `diagnose=True` triggers constitution diagnostics inline
- `analyze_for_improvements(comparison) -> List[str]` — inspects pattern failures and low-scoring categories
- `save_results(comparison, output_dir) -> Path` — JSON with timestamp + suggestions + optional diagnostics

**ClaudeCodeRunner** (`cc_runner.py:45`) — does NOT call the API; generates prompts for Claude Code Task subagents.
- `format_subagent_prompt(test_id, with_skills) -> str` — combines system+user prompt into a single string
- `get_subagent_prompts(test_ids) -> List[dict]` — 2 dicts per test (with/without conditions)
- `evaluate(with_skills_code, without_skills_code, diagnose) -> ABComparison`
- `get_judge_prompts(with_skills_code, without_skills_code) -> List[dict]`
- `judge(with_scores, without_scores, print_report) -> JudgeComparison`
- `run_full(test_ids, diagnose) -> (prompts, evaluate_callback)` — convenience tuple

**JudgeScore** (`judge.py:37`) — 4 dimensions all 1-5: `correctness`, `api_usage`, `conciseness`, `efficiency`. `overall` property: `(correctness*0.2 + api_usage*0.4 + conciseness*0.2 + efficiency*0.2) / 5.0`. `api_usage` is weighted highest (0.4) because that is what skills should improve most.

**JudgeComparison** (`judge.py:63`) — `per_test_deltas: Dict[str, Dict[str,float]]`, `mean_deltas`, `winner: str`. `build_judge_comparison()` uses intersection of test IDs; winner determined by sign of `mean_deltas["overall"]`.

**Constitution** (`constitution.py:50`) — parsed from `skills/constitution.yaml`.
- `get_goal(goal_id) -> Optional[ConstitutionGoal]`
- `get_weighted_goals() -> List[ConstitutionGoal]` — sorted descending by weight, zero-weight goals excluded
- `goals_for_skill_file(skill_path) -> List[ConstitutionGoal]`

**ConstitutionGoal** (`constitution.py:23`) — fields: `id`, `name`, `weight: float`, `description`, `passing_criteria`, `primary_skill_files`, `indicator_patterns`, `anti_patterns`, `skill_token_budgets: Dict[str,int]` (only on `token_economy` goal).

**ConstitutionReport** (`diagnostics.py:121`) — `__post_init__` auto-aggregates `by_goal`, `by_skill_file`, `by_category`, computes `goal_scores`, builds `priority_fixes` sorted high→medium.
- `print_report()`, `to_dict()`, `skill_budget_status` filled by `check_skill_token_budgets()`

**AgentTestRunner** (`agent.py:700`) — async; drives Claude Code SDK.
- `__init__(model="claude-haiku-4-5-20251001", skill_context=None)`
- `run_single(test_id, with_skills) -> AgentTestResult` — awaitable
- `run_ab_comparison(test_ids, delay_between_tests=1.0) -> ABComparison`
- `run_and_save(test_ids, output_dir, diagnose) -> Path`
- Internally uses `_build_report()` to adapt `AgentScore` into `CombinedEvaluation` so existing `ABComparison` summary logic works
- Stores last raw results in `_last_with_results` / `_last_without_results` for `analyze_skill_gaps()`

**AgentScore** (`agent.py:83`) — tool_selection (35%), answer_quality (45%), efficiency (20%).
- Tool selection: recall of expected tools − 0.1 penalty per extra tool (max 0.3 penalty)
- Answer quality: fraction of `expected_in_answer` strings present (case-insensitive)
- Efficiency: 1.0 if calls ≤ budget; linearly 1.0→0.0 from budget to 2× budget

**BaseSkill** (`skills/base.py:16`) — ABC with 4 abstract members: `name`, `description`, `content_dir`, `get_helpers()`. Concrete optional overrides: `get_object_docs() -> List[Path]` (default `[]`), `get_documents()`, `get_document_content(name)`, `export(format, output_dir, **kwargs)` (delegates to `export_skill()`).

**EdgarToolsSkill** (`skills/core/__init__.py:16`) — name="EdgarTools"; `content_dir = Path(__file__).parent` (i.e. `edgar/ai/skills/core/`). `get_object_docs()` returns 5 API reference paths: `Company.md`, `EntityFiling.md`, `EntityFilings.md`, `XBRL.md`, `Statement.md`. `get_helpers()` returns 5 functions from `edgar.ai.helpers`: `get_filings_by_period`, `get_today_filings`, `get_revenue_trend`, `get_filing_statement`, `compare_companies_revenue`.

---

### Class hierarchy

```
ABC
└── BaseSkill (edgar/ai/skills/base.py:16)
    └── EdgarToolsSkill (edgar/ai/skills/core/__init__.py:16)
        └── edgartools_skill  [singleton instance]

dataclass: SECAnalysisTestCase
dataclass: TestResult
dataclass: EvaluationReport
dataclass: ABComparison
dataclass: ExecutionResult
dataclass: PatternResult
dataclass: TokenResult
dataclass: CombinedEvaluation
dataclass: GenerationResult
dataclass: ConstitutionGoal
dataclass: Constitution
dataclass: PatternDiagnosis
dataclass: ConstitutionDiagnostic
dataclass: ConstitutionReport
dataclass: ToolCall
dataclass: AgentTrace
dataclass: AgentScore
dataclass: AgentTestResult
dataclass: SkillDiagnostic
dataclass: SkillGapReport
dataclass: JudgeScore
dataclass: JudgeComparison

SkillEvaluationHarness   [plain class]
SkillTestRunner          [plain class, lazy Anthropic client]
ClaudeCodeRunner         [plain class, no API calls]
AgentTestRunner          [plain class, async, Claude Code SDK]
```

Composition:
- `TestResult` contains `CombinedEvaluation`
- `CombinedEvaluation` contains `ExecutionResult` + `PatternResult` + `TokenResult`
- `EvaluationReport` contains `List[TestResult]`
- `ABComparison` contains two `EvaluationReport` instances
- `ConstitutionReport` contains `List[ConstitutionDiagnostic]`; each diagnostic contains `List[PatternDiagnosis]`
- `AgentTestResult` contains `AgentTrace` + `AgentScore`
- `SkillGapReport` contains `List[SkillDiagnostic]`

---

### Configuration & options

| Option | Type | Default | Effect |
|--------|------|---------|--------|
| `SkillEvaluationHarness.execute_code` | bool | `False` | If False, execution weight=0.0; pattern+efficiency only |
| `SkillEvaluationHarness.test_suite` | list | `SEC_TEST_SUITE` | Which test cases to use |
| `SkillTestRunner.model` | str | `"claude-sonnet-4-20250514"` | Anthropic model for code generation |
| `SkillTestRunner.max_tokens` | int | `1024` | Max output tokens for generation |
| `SkillTestRunner.api_key` | str | `ANTHROPIC_API_KEY` env var | Anthropic API key |
| `AgentTestRunner.model` | str | `"claude-haiku-4-5-20251001"` | Claude Code SDK model |
| `AgentTestRunner.delay_between_tests` | float | `1.0` (sec) | Respects SEC rate limits |
| `SECAnalysisTestCase.max_tokens` | int | `1000` | Token budget for efficiency scoring |
| `SECAnalysisTestCase.max_tool_calls` | int | `10` | Tool call budget for agent efficiency |
| `evaluate_code.weights` | dict | None (mode-based) | Override execution/pattern/efficiency weights |
| `run_ab_comparison.diagnose` | bool | `False` | Whether to run constitution diagnostics after comparison |
| `export_claude_skills.install` | bool | `True` | If True, writes to `~/.claude/skills/` via `get_claude_skills_directory()` |
| `export_claude_desktop.create_zip` | bool | `True` | If True, creates a `.zip` archive; if False, leaves directory |
| `load_constitution.path` | str | None | Defaults to `edgar/ai/skills/constitution.yaml` |
| `ClaudeCodeRunner.execute_code` | bool | `False` | Passed through to inner SkillEvaluationHarness |

**Constitution goals and weights** (from `edgar/ai/skills/constitution.yaml`):

| Goal ID | Weight | Primary Skill Files |
|---------|--------|---------------------|
| `correctness` | 0.30 | core/skill.yaml, core/sharp-edges.yaml |
| `routing` | 0.25 | core/skill.yaml, core/collaboration.yaml |
| `efficiency` | 0.20 | core/skill.yaml, financials/skill.yaml |
| `sharp_edges` | 0.15 | all `*/sharp-edges.yaml` files |
| `token_economy` | 0.10 | core/skill.yaml; has per-file token budgets |
| `completeness` | 0.00 | core/collaboration.yaml (inactive) |

**Token budgets** (from `constitution.yaml` token_economy goal):

| Skill file | Budget (tokens) |
|------------|-----------------|
| core/skill.yaml | 4500 |
| financials/skill.yaml | 1000 |
| holdings/skill.yaml | 800 |
| ownership/skill.yaml | 1100 |
| reports/skill.yaml | 900 |
| xbrl/skill.yaml | 1000 |

---

### Data flow / lifecycle

**Code-gen evaluation flow (SkillTestRunner / ClaudeCodeRunner):**
1. `load_skill_context()` reads `edgar/ai/skills/core/skill.yaml` first, then all other `*/skill.yaml` files in sorted directory order, concatenating them.
2. `build_prompt()` constructs system+user prompts — with-skills includes full concatenated YAML; without-skills uses `get_minimal_context()` (a short hardcoded description).
3. For `SkillTestRunner`: Anthropic API called, response extracted via `extract_code_from_response()` (tries `python` fences → generic fences → heuristic line detection).
4. For `ClaudeCodeRunner`: prompts returned for Claude Code Task subagents to execute; code collected externally.
5. `SkillEvaluationHarness.evaluate_code()` runs `evaluate_code()` which calls: `evaluate_pattern_compliance()` always; `evaluate_token_efficiency()` always; `evaluate_code_execution()` only if `execute_code=True`.
6. `ABComparison.__post_init__()` immediately calculates improvement metrics.
7. Optional: `run_constitution_diagnostics()` maps pattern failures onto constitution goals via `PATTERN_GOAL_MAP` / `FORBIDDEN_GOAL_MAP` tables, then calls `check_skill_token_budgets()`, then `generate_skill_edit_suggestions()`.

**LLM-judge flow (separate path):**
1. `ClaudeCodeRunner.get_judge_prompts()` calls `build_judge_prompt()` per code sample, filling `_JUDGE_PROMPT_TEMPLATE` with task + reference_code + generated_code.
2. Prompts sent to judge subagents externally; responses collected.
3. `parse_judge_response()` extracts JSON (`{"correctness":N,"api_usage":N,"conciseness":N,"efficiency":N,"rationale":...}`) from markdown or raw JSON.
4. `build_judge_comparison()` computes per-test deltas and mean deltas; winner = sign of `mean_deltas["overall"]`.

**Agent evaluation flow (AgentTestRunner):**
1. `_get_mcp_server_config()` returns stdio config pointing to `edgar.ai.evaluation.mcp_server` subprocess.
2. Claude Code SDK `query()` drives the tool-call loop; MCP tools served by `mcp_server.py` (wraps `edgar.ai.mcp.tools` — company, search, filing, compare, ownership).
3. Tool calls captured into `AgentTrace`; tool names normalized by stripping `mcp__edgar__` prefix.
4. `evaluate_agent()` scores tool_selection, answer_quality, efficiency → `AgentScore`.
5. `_build_report()` adapts `AgentScore` into `CombinedEvaluation` so `ABComparison.summary()` works unchanged.
6. Optional: `analyze_skill_gaps()` calls `diagnose_trace()` per pair → `SkillGapReport`.

**Skill export flow:**
1. `BaseSkill.export(format, output_dir)` dispatches to `export_skill()` → either `export_claude_skills` or `export_claude_desktop`.
2. Both exporters: read `skill.content_dir` for `*.md` and `*.yaml`; copy domain subdirs `financials/`, `holdings/`, `ownership/`, `reports/`, `xbrl/`; copy `forms.yaml`; call `skill.get_object_docs()` and copy those to `api-reference/`.
3. `export_claude_skills`: SKILL.md validated (frontmatter must have `name` and `description`); if `install=True`, destination is `~/.claude/skills/<skill-name>/` via `edgar.paths.get_claude_skills_directory()`.
4. `export_claude_desktop`: additionally wraps everything in a ZIP file (default). ZIP uses `source_dir.parent`-relative arcnames so the skill directory name is preserved inside the archive.
5. Frontmatter validation: regex check for `^name:` and `^description:` in frontmatter; ValueError raised if absent.

---

### Design patterns

- **A/B testing pattern** — the entire evaluation system is built around a with-skills / without-skills two-condition comparison. All runners produce paired `ABComparison` objects.
- **Strategy pattern** — three interchangeable runner implementations (`SkillTestRunner` for direct API, `ClaudeCodeRunner` for Task subagent prompts, `AgentTestRunner` for live agent loops) all produce `ABComparison`; callers are interchangeable.
- **Constitution-driven quality** — a YAML-encoded constitution externalizes quality goals, weights, pattern indicators, and per-file token budgets. The diagnostics engine maps evaluation failures back to constitution goals without hardcoding.
- **Lazy loading** — `SkillTestRunner.client` property lazy-initializes the Anthropic client; `EdgarToolsSkill.get_helpers()` imports `edgar.ai.helpers` lazily to avoid circular dependencies.
- **Singleton skill instance** — `edgartools_skill = EdgarToolsSkill()` at module level for convenient import.
- **Dataclass serialization** — all result types implement `.to_dict()` / `.to_json()` for JSON persistence; ABComparison can be saved to timestamped files.
- **Fallback-chain JSON parsing** — `parse_judge_response()` tries markdown fences → raw brace match → defaults to all-3s score. `extract_code_from_response()` tries `python` fences → generic fences → heuristic line detection.
- **Pattern → goal mapping tables** — `diagnostics.py` has static `PATTERN_GOAL_MAP` and `FORBIDDEN_GOAL_MAP` dicts that classify regex patterns into constitution goal IDs, with fallback to scanning `constitution.indicator_patterns` and `anti_patterns`.

---

### Cross-domain interactions

**Imports from other edgar.* modules:**
- `edgar.ai.mcp.tools` (company, search, filing, compare, ownership, base) — used by `mcp_server.py` to serve MCP tools during agent evaluation
- `edgar.ai.helpers` — imported lazily by `EdgarToolsSkill.get_helpers()`
- `edgar.paths.get_claude_skills_directory` — used by `export_claude_skills` to resolve `~/.claude/skills/`
- `edgar` (Company, Fund, etc.) — used only in reference_code strings and basic_usage.py examples, not in evaluation machinery

**Consumed by:**
- Nothing in the core edgar domain imports from `edgar.ai.evaluation` or `edgar.ai.exporters`; these are developer/tooling modules only.
- `edgar.ai.__main__` likely wires CLI entry points (not read, but `harness.py:main()` and `runner.py:main()` and `agent.py:main()` all define CLI entry points).

---

### Skill content packs (YAML/Markdown under `edgar/ai/skills/`)

The actual LLM-facing knowledge lives in these files — they are what `load_skill_context()` concatenates and what the exporters copy:

| Path | `id` | Purpose |
|------|------|---------|
| `skills/core/skill.yaml` | `edgartools-core` v1.1 | Universal lookup, filings, 4-file architecture index |
| `skills/core/SKILL.md` | — | Claude Skills entry point (name: EdgarTools, skill table) |
| `skills/core/sharp-edges.yaml` | — | Production gotchas and anti-patterns |
| `skills/core/validations.yaml` | — | Automated code quality checks |
| `skills/core/collaboration.yaml` | — | Handoffs between skill domains |
| `skills/financials/skill.yaml` | `edgartools-financials` v1.1 | Financial statements and metrics |
| `skills/financials/sharp-edges.yaml` | — | Financials-specific anti-patterns |
| `skills/holdings/skill.yaml` | `edgartools-holdings` v1.1 | 13F institutional holdings |
| `skills/holdings/sharp-edges.yaml` | — | Holdings anti-patterns |
| `skills/ownership/skill.yaml` | `edgartools-ownership` v1.1 | Form 3/4/5 insider transactions |
| `skills/ownership/sharp-edges.yaml` | — | Ownership anti-patterns |
| `skills/reports/skill.yaml` | `edgartools-reports` v1.1 | 10-K/10-Q/8-K section extraction |
| `skills/reports/sharp-edges.yaml` | — | Reports anti-patterns |
| `skills/xbrl/skill.yaml` | `edgartools-xbrl` v1.1 | Low-level XBRL facts and concepts |
| `skills/xbrl/sharp-edges.yaml` | — | XBRL anti-patterns |
| `skills/funds/skill.yaml` | `edgartools-funds` v1.0 | Mutual funds, ETFs, NPORT/N-MFP/N-CEN |
| `skills/forms.yaml` | — | SEC form type reference |
| `skills/constitution.yaml` | version "1.0" | Quality goals with weights and budgets |
| `skills/content/skill.yaml` | — | Additional content (read but not examined) |

API reference docs included on export (from `EdgarToolsSkill.get_object_docs()`):
- `edgar/entity/docs/Company.md`
- `edgar/entity/docs/EntityFiling.md`
- `edgar/entity/docs/EntityFilings.md`
- `edgar/xbrl/docs/XBRL.md`
- `edgar/xbrl/docs/Statement.md`

---

### Test suite coverage

**SEC_TEST_SUITE** contains 42 test cases (TC001–TC042):

| Range | Difficulty | Categories |
|-------|-----------|------------|
| TC001–TC003 | easy | lookup, filing, counting |
| TC004–TC008 | medium | financial (2), ownership, holdings, reports |
| TC009–TC010 | hard | comparison, multi-step |
| TC011–TC013 | easy | lookup (2), filing |
| TC014–TC020 | medium | financial (3), comparison, filing (2), reports |
| TC021–TC025 | hard | ownership, comparison, multi-step (2), financial |
| TC026–TC030 | mixed | Fund cases (lookup, holdings, multi-step) |
| TC031–TC035 | mixed | Report sections (10-Q/8-K/10-K items) |
| TC036–TC040 | mixed | Error/edge-case patterns (safety, guarding) |
| TC041–TC042 | medium/hard | XBRL low-level, Schedule 13D |

Helper functions: `get_test_by_id()`, `get_tests_by_category()`, `get_tests_by_difficulty()`, `get_tests_by_tag()`, `get_tests_not_requiring_network()` (all network_required=False by default).

---

### Gotchas & notable behaviors

- `evaluate_code_execution()` uses `exec()` in a bare namespace — it is explicitly marked "only use with trusted inputs." No timeout enforcement exists yet (`timeout_seconds` parameter is accepted but not enforced).
- `count_tokens()` uses `len(text) // 4` (character heuristic), intentionally avoiding tiktoken dependencies. This means token counts are approximate and favor short-length code.
- When `execute=False` (default), execution weight is redistributed: pattern gets 0.7, efficiency 0.3. This is deliberate — running 42 tests live against SEC EDGAR would be slow and rate-limited.
- `load_skill_context()` loads `core/skill.yaml` first, then all other non-core directories in `sorted()` order. The `content/` subdirectory has its own `skill.yaml` that will also be included if present.
- `export_claude_skills` raises `ValueError` if `SKILL.md` is missing from `content_dir`. `export_claude_desktop` does not raise — it will just produce a ZIP with no SKILL.md if the file is absent from the content directory.
- Both exporters silently skip missing API reference docs (`get_object_docs()` paths that don't exist on disk).
- `AgentTestRunner._build_report()` maps `AgentScore.tool_selection` into `PatternResult.score` and `AgentScore.efficiency` into `TokenResult.efficiency_score` — this is a structural adaptation so `ABComparison.summary()` reuses the same display logic, but the field semantics differ from the code-gen path.
- `SkillGapReport` in `agent.py` and `ConstitutionReport` in `diagnostics.py` are parallel but independent diagnostic structures. `SkillGapReport` is for agent (tool/answer/efficiency failures); `ConstitutionReport` is for code-gen (pattern/constitution failures). Both can be triggered from their respective runners.
- The `completeness` constitution goal has `weight: 0.0` — it exists for definition purposes but is excluded from `get_weighted_goals()` and does not contribute to scoring.
- `parse_judge_response()` defaults all dimensions to 3 (not 0) on parse failure, producing a neutral 0.600 overall score rather than a zero penalty.
- The `TOOL_SKILL_MAP` and `CATEGORY_SKILL_MAP` tables appear in BOTH `agent.py` and `diagnostics.py` with slightly different values — not consolidated. Updates to skill file names must be made in both places.
- `export_skill(format="claude-skills")` default-installs to `~/.claude/skills/` using `edgar.paths.get_claude_skills_directory(create=False)`. The `create=False` means the directory must already exist or the copy will fail.
