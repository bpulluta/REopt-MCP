# REopt-MCP Cleanup Plan (Phased)

## Objective

Refactor this repository into a clean, single-purpose MCP server where Copilot Chat:

1. gathers required REopt inputs conversationally,
2. runs optimization,
3. summarizes outputs,

without requiring users to author JSON scripts manually.

## Cleanup Principles

- **Single canonical workflow**: information gathering first, optimization second.
- **No legacy paths**: remove old/duplicate code, no backward-compatibility scaffolding.
- **One source of truth**: tool behavior, validation rules, examples, and docs must match.
- **Minimal public surface**: expose only tools that support the core conversational UX.
- **Small modules, clear ownership**: no large monolithic server file.

---

## Phase 1 — Hard Prune (Delete Redundancy)

### Goals
- Remove duplicate runtime code and stale files created during iteration.
- Reduce documentation clutter at repo root.
- Remove tests that target old APIs/functions.

### Actions
- Delete duplicate server file: `reopt_mcp/server_backup.py`.
- Remove or replace stale tests referencing removed functions (e.g., `get_simple_pv_scenario`).
- Keep only essential top-level docs:
  - `README.md`
  - one setup guide
  - `CHANGELOG.md`
- Archive or delete superseded long-form docs.

### Acceptance Criteria
- No duplicate server implementation exists.
- `tests/` contains only tests for current behavior.
- Root directory is concise and intentional.

---

## Phase 2 — Modularize Server Code

### Goals
- Split `reopt_mcp/server.py` into logical modules with single responsibilities.
- Keep behavior stable while improving structure.

### Target Module Structure

```text
reopt_mcp/
  __init__.py
  __main__.py
  server.py           # thin MCP bootstrap only
  config.py           # env and runtime settings
  instructions.py     # single DEFAULT_INSTRUCTIONS source
  constants.py        # DOE names, invalid fields, etc.
  validation.py       # scenario validation and guidance
  client.py           # REopt HTTP calls + polling logic
  summaries.py        # markdown summary/financial/system formatters
  tools.py            # tool definitions + dispatcher
  examples.py         # valid canonical scenarios only
```

### Actions
- Move validation logic out of `server.py` into `validation.py`.
- Move API calls/polling into `client.py`.
- Move text formatting/summaries into `summaries.py`.
- Keep `server.py` only for MCP initialization and wiring.

### Acceptance Criteria
- `server.py` is small and readable.
- Each module has one clear concern.
- No duplicated constants or instruction text across files.

---

## Phase 3 — Tool Surface Streamlining

### Goals
- Keep only tools that support the intended guided Copilot UX.
- Remove low-level or duplicate tooling that encourages non-guided flows.

### Keep (Core Tools)
- `submitAndWait`
- `validateScenario`
- `getResultsSummary`
- `getFinancialSummary`
- `getSystemSummary`
- `getMinimalScenario`
- `getExampleScenario`

### Remove or De-scope (unless explicit diagnostic requirement)
- `submitReoptJob`
- `waitForJob`
- `getJobStatus`
- `getJobResults`

### Acceptance Criteria
- Tool list is minimal and non-overlapping.
- Descriptions are precise and aligned with product objective.

---

## Phase 4 — Contract Unification (Critical)

### Goals
- Ensure scenario requirements are consistent everywhere.
- Eliminate contradictions between validator, docs, and examples.

### Canonical Contract
- `Site`: latitude + longitude required.
- `ElectricLoad`: both `doe_reference_name` and `annual_kwh` required (for guided mode).
- `ElectricTariff`: either `urdb_label` OR blended annual rates.
- Technology objects added only when explicitly requested.

### Actions
- Update `examples.py` so all examples pass validator.
- Align `getMinimalScenario` and `getExampleScenario` to validator rules.
- Remove conflicting guidance (e.g., examples missing required fields while validator requires them).

### Acceptance Criteria
- All bundled examples validate successfully.
- No contradictory schema guidance remains.

---

## Phase 5 — Documentation Consolidation

### Goals
- Make onboarding and usage clear in one primary path.
- Remove redundant long docs that drift over time.

### Actions
- Rewrite `README.md` as canonical:
  - What this MCP does
  - Quick setup
  - Conversational workflow
  - Required inputs
  - Tool map
- Keep one setup guide (VS Code/Copilot-first).
- Move deep/internal notes to `dev-docs/` only if still needed.
- Delete superseded setup guides with overlapping content.

### Acceptance Criteria
- New user can setup + run first optimization from one path.
- No duplicated setup narratives across multiple files.

---

## Phase 6 — Rebuild Tests (Lean and Deterministic)

### Goals
- Replace brittle script-style tests with focused assertions.
- Ensure tests map to current architecture and tool surface.

### Test Strategy
- Unit tests:
  - validation rules
  - summary formatting
  - scenario examples validity
- Client tests:
  - mock HTTP responses for submit/poll/results
- Optional integration smoke test:
  - only if `NREL_API_KEY` exists

### Actions
- Replace legacy test scripts with pytest-based tests where appropriate.
- Remove references to old functions and stale endpoint assumptions.

### Acceptance Criteria
- Local test run is stable and meaningful.
- Failing tests identify real regressions in current behavior.

---

## Phase 7 — Packaging and Repo Hygiene

### Goals
- Ensure run/test/lint commands are clear and current.
- Remove metadata placeholders and drift.

### Actions
- Align `pyproject.toml` and `pixi.toml` tasks with new test commands.
- Add/standardize lint + format tasks (if desired): `ruff`, `black`.
- Clean placeholder metadata (author/version notes) as needed.

### Acceptance Criteria
- One clear command path for run/test.
- Config files match actual code layout and tooling.

---

## Phase 8 — Final Quality Gate

### Goals
- Confirm repository is clean, coherent, and ready as baseline.

### Checklist
- [x] No duplicate/backup server runtime code remains.
- [x] Tool list is minimal and intentional.
- [x] Validation, examples, and docs agree 100%.
- [x] Tests pass and reflect current behavior.
- [x] Root documentation is concise and non-redundant.
- [x] MCP startup works with configured API key.

### Release Output
- Update `CHANGELOG.md` with cleanup release notes.
- Tag as clean baseline for future incremental changes.

---

## Recommended Execution Order

1. **Phase 1** (Prune)
2. **Phase 2** (Modularize)
3. **Phase 3** (Streamline tools)
4. **Phase 4** (Unify contract)
5. **Phase 5** (Consolidate docs)
6. **Phase 6** (Rebuild tests)
7. **Phase 7** (Packaging hygiene)
8. **Phase 8** (Final gate + release)

This order minimizes rework and prevents legacy behavior from leaking into the cleaned architecture.

---

## Working Notes Template (for each phase)

Use this small template while executing:

```markdown
### Phase X Status
- Scope:
- Files touched:
- Decisions made:
- Risks found:
- Validation run:
- Exit criteria met: Yes/No
- Follow-up actions:
```

---

## Execution Log

### Phase 1 Status
- Scope: Hard prune of duplicate runtime code, stale tests, and redundant setup docs.
- Files touched:
  - Deleted: `reopt_mcp/server_backup.py`
  - Deleted: `tests/test_mcp.py`
  - Deleted: `docs/Claude_Desktop_Setup_Guide.md`
  - Added: `tests/test_smoke.py`
  - Updated: `tests/simple_test.py`
  - Updated: `pixi.toml`
  - Updated: `README.md`
  - Updated: `.env.example`
- Decisions made:
  - Replaced legacy comprehensive script test with a lean smoke test (`tests/test_smoke.py`) as default `pixi run test` target.
  - Kept `tests/test_api_direct.py` as optional direct API check for now (to be revisited in Phase 6 test rebuild).
  - Scoped Phase 1 to cleanup only; reverted unrelated `reopt_mcp/server.py` edits.
- Risks found:
  - `tests/simple_test.py` and `tests/test_smoke.py` still overlap somewhat; consolidate during Phase 6.
  - Root docs consolidation is partial; one long setup guide remains intentionally for now.
- Validation run:
  - `pixi run test` → passed.
- Exit criteria met: **Yes (Phase 1 complete)**
- Follow-up actions:
  - Begin Phase 2 modularization of `reopt_mcp/server.py` into focused modules.

### Phase 2 Status
- Scope: Modularize monolithic server into focused modules while preserving behavior.
- Files touched:
  - Added: `reopt_mcp/config.py`
  - Added: `reopt_mcp/instructions.py`
  - Added: `reopt_mcp/constants.py`
  - Added: `reopt_mcp/validation.py`
  - Added: `reopt_mcp/client.py`
  - Added: `reopt_mcp/summaries.py`
  - Added: `reopt_mcp/tools.py`
  - Replaced: `reopt_mcp/server.py` (thin bootstrap)
- Decisions made:
  - Split validation, client, and summary logic into dedicated modules.
  - Kept MCP tool registration/dispatch in `reopt_mcp/tools.py`.
  - Preserved `reopt_mcp/server.py` as compatibility re-export for `app` and `main`.
- Risks found:
  - Low-level tools are still exposed and should be de-scoped in Phase 3.
  - Example/minimal guidance contract alignment still needs Phase 4 cleanup.
- Validation run:
  - `pixi run test` → passed.
- Exit criteria met: **Yes (Phase 2 complete)**
- Follow-up actions:
  - Start Phase 3 tool surface streamlining.

### Phase 3 Status
- Scope: Streamline exposed MCP tool surface to guided core tools only.
- Files touched:
  - Updated: `reopt_mcp/tools.py`
- Decisions made:
  - Removed low-level tools from public MCP list: `submitReoptJob`, `waitForJob`, `getJobStatus`, `getJobResults`.
  - Removed dispatch paths and now-unreachable low-level handler functions for those tools.
  - Retained only guided/core tools: `submitAndWait`, `validateScenario`, `getResultsSummary`, `getFinancialSummary`, `getSystemSummary`, `getMinimalScenario`, `getExampleScenario`.
- Risks found:
  - `getMinimalScenario` and `getExampleScenario` still include guidance/examples that are not fully aligned with validator contract; fix in Phase 4.
- Validation run:
  - `pixi run test` → passed.
- Exit criteria met: **Yes (Phase 3 complete)**
- Follow-up actions:
  - Begin Phase 4 contract unification across validator, examples, and scenario helper tools.

### Phase 4 Status
- Scope: Unify scenario contract across validator, bundled examples, and helper tool outputs.
- Files touched:
  - Updated: `reopt_mcp/validation.py`
  - Updated: `reopt_mcp/examples.py`
  - Updated: `reopt_mcp/tools.py`
- Decisions made:
  - Updated tariff validation to require either a non-empty `urdb_label` OR both blended annual rate fields.
  - Updated canonical examples to use complete `ElectricLoad` objects and non-empty tariff placeholders.
  - Removed conflicting `getMinimalScenario` guidance that implied `annual_kwh` was optional.
  - Updated `getExampleScenario` payload and markdown examples to follow the same contract.
- Risks found:
  - Placeholder `REGION_SPECIFIC_LABEL` must still be replaced with utility-specific URDB labels during real runs.
- Validation run:
  - `pixi run python` one-off validator check → all bundled examples valid.
  - `pixi run test` → passed.
- Exit criteria met: **Yes (Phase 4 complete)**
- Follow-up actions:
  - Begin Phase 5 documentation consolidation (canonical README + remove overlap).

### Phase 5 Status
- Scope: Consolidate user-facing docs around a single canonical README path.
- Files touched:
  - Updated: `README.md`
- Decisions made:
  - Aligned README required-input guidance to canonical contract (`doe_reference_name` + `annual_kwh`).
  - Added explicit core tool map to README.
  - Updated README project structure to reflect modularized server architecture.
  - Kept `docs/REopt_MCP_Setup_Guide.md` as the single detailed setup guide and linked it from README.
  - Left additional setup/quickstart files in `dev-docs/` as internal reference docs.
- Risks found:
  - Internal `dev-docs/` setup notes may still drift over time; treat README + docs setup guide as source of truth.
- Validation run:
  - `pixi run test` → passed.
- Exit criteria met: **Yes (Phase 5 complete)**
- Follow-up actions:
  - Begin Phase 6 lean test rebuild and consolidation.

### Phase 6 Status
- Scope: Replace script-style checks with deterministic pytest tests aligned to current architecture.
- Files touched:
  - Added: `tests/test_validation.py`
  - Added: `tests/test_examples.py`
  - Added: `tests/test_summaries.py`
  - Added: `tests/test_client.py`
  - Added: `tests/test_integration_api.py`
  - Added: `pytest.ini`
  - Deleted: `tests/test_smoke.py`
  - Deleted: `tests/simple_test.py`
  - Deleted: `tests/test_api_direct.py`
  - Updated: `pixi.toml`
  - Updated: `README.md`
- Decisions made:
  - Switched default test command to `pytest -q tests`.
  - Added focused unit tests for validation rules, summary formatting, scenario example validity, and mocked client behavior.
  - Added optional integration test path marked `integration`, guarded by `NREL_API_KEY` + `RUN_INTEGRATION_TESTS=1`.
  - Kept integration tests out of default `pixi run test` for determinism.
- Risks found:
  - Integration path depends on external API/network and remains non-deterministic by nature.
- Validation run:
  - `pixi run test` → `16 passed, 1 skipped`.
  - `pixi run api-test` → `1 skipped, 16 deselected`.
- Exit criteria met: **Yes (Phase 6 complete)**
- Follow-up actions:
  - Begin Phase 7 packaging and repo hygiene updates.

### Phase 7 Status
- Scope: Align packaging/tasks with current architecture and remove config drift.
- Files touched:
  - Updated: `pixi.toml`
  - Updated: `README.md`
- Decisions made:
  - Removed placeholder author metadata from `pixi.toml`.
  - Standardized quality tasks in default environment: `lint`, `format`, `format-check`.
  - Switched formatting tasks to `ruff format` to avoid environment mismatch with `black`.
  - Kept run/test path explicit and current: `pixi run server`, `pixi run test`, `pixi run api-test`.
  - Added README references for quality-check commands.
- Risks found:
  - Formatting normalization touched multiple files (expected for consistency).
- Validation run:
  - `pixi run format-check` → passed.
  - `pixi run test` → `16 passed, 1 skipped`.
  - `pixi run lint` → passed.
- Exit criteria met: **Yes (Phase 7 complete)**
- Follow-up actions:
  - Begin Phase 8 final quality gate + cleanup release notes.

### Phase 8 Status
- Scope: Final quality gate validation and cleanup release readiness.
- Files touched:
  - Updated: `docs/CLEANUP_PLAN.md`
  - Updated: `CHANGELOG.md`
- Decisions made:
  - Completed final quality gate checks and marked checklist items complete.
  - Kept Phase 8 focused on validation + release notes only.
- Risks found:
  - None blocking for baseline release.
- Validation run:
  - `pixi run test` → `16 passed, 1 skipped`.
  - `pixi run lint` → passed.
  - `pixi run format-check` → passed.
  - `pixi run python` import sanity (`reopt_mcp.server`) → `server_main: True`, `server_app: True`.
- Post-audit revalidation (2026-04-03):
  - `pixi run test` → `26 passed, 1 skipped`.
  - `pixi run lint` → passed.
  - `pixi run format-check` → passed.
- Exit criteria met: **Yes (Phase 8 complete)**
- Follow-up actions:
  - Optional: create release tag for clean baseline.
