# Changelog

All notable changes to the REopt MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-07-09

### Changed
- **Configuration**: Simplified `config.py` — single `NLR_API_KEY` env var, single
  `REOPT_API_BASE_URL` default (`developer.nlr.gov`). Removed all legacy fallback
  and hostname normalization logic.
- **Client**: Cleaner connection error messages that include the active base URL.
- **Version**: Bumped to 0.4.0 across `pyproject.toml`, `pixi.toml`, and server init.
- **Pixi**: Replaced deprecated `[project]` with `[workspace]` in `pixi.toml`.
- **README**: Rewritten for production use — concise setup, usage, and development
  sections with no redundancy.

### Removed
- Legacy `NREL_API_KEY` env var fallback and `developer.nrel.gov` hostname rewriting.
- `docs/` directory (archived to `archive/docs/`).
- 20+ development-only markdown files from `dev-docs/` (archived to `archive/dev-docs/`).
  Only the REopt.jl reference docs (`dev-docs/reoptjl_docs/`) are retained.

## [0.3.0] - 2026-03-09

### Changed
- **Architecture**: Refactored monolithic server into focused modules:
  - `reopt_mcp/tools.py` (tool registration + dispatch)
  - `reopt_mcp/client.py` (REopt API calls + polling)
  - `reopt_mcp/validation.py` (scenario validation + guidance)
  - `reopt_mcp/summaries.py` (result formatting)
  - `reopt_mcp/config.py`, `reopt_mcp/constants.py`, `reopt_mcp/instructions.py`
- **Bootstrap**: Reduced `reopt_mcp/server.py` to a thin compatibility entry point.
- **Tool Surface**: Streamlined exposed MCP tools to guided core set:
  - `submitAndWait`, `validateScenario`, `getResultsSummary`, `getFinancialSummary`, `getSystemSummary`, `getMinimalScenario`, `getExampleScenario`
- **Contract Unification**:
  - `ElectricLoad` requires both `doe_reference_name` and `annual_kwh`
  - `ElectricTariff` accepts either non-empty `urdb_label` or blended annual energy + demand rates
  - Canonical examples and helper outputs updated to match validator behavior
- **Testing**: Replaced script-style tests with deterministic pytest suite:
  - Added focused unit tests for validation, examples, summaries, and mocked client behavior
  - Added optional integration test path guarded by `NLR_API_KEY` + `RUN_INTEGRATION_TESTS=1`
- **Tooling/Tasks**:
  - Updated pixi tasks to `pytest` workflow
  - Added `lint`, `format`, and `format-check` tasks using Ruff
  - Removed placeholder metadata from pixi project config
- **Documentation**:
  - Consolidated README as canonical quick path
  - Linked detailed setup guide in `docs/REopt_MCP_Setup_Guide.md`

### Removed
- `reopt_mcp/server_backup.py`
- Legacy low-level tool exposure paths and handlers
- Script-style tests:
  - `tests/test_mcp.py`
  - `tests/test_smoke.py`
  - `tests/simple_test.py`
  - `tests/test_api_direct.py`

## [0.2.0] - 2025-12-17

### Fixed
- **API Endpoints**: Changed base URL from `/api/reopt` to `/api/reopt/stable` to match official REopt API
- **Job Status**: Fixed status checking by using `/results` endpoint instead of unavailable `/status` endpoint
- **Scenario Structure**: Corrected scenario format - `ElectricLoad` should be at top level, not nested in `Site.LoadProfile`
- All example scenarios updated to use correct structure

### Changed
- **Repository Organization**: 
  - Moved all development documentation to `dev-docs/` folder (git-ignored)
  - Moved all test files to `tests/` directory
  - Keep only `README.md` and `CHANGELOG.md` in root
  - Removed redundant virtual environments (using pixi exclusively)
- **Configuration**: Updated `.env.example` with correct base URL

### Added
- Comprehensive test scripts in `tests/` directory
- Configuration documentation in `dev-docs/`

## [0.1.0] - 2025-12-11

### Added
- Initial MCP server implementation
- Four main tools: submit_reopt_job, get_job_status, get_job_results, get_example_scenario
- GitHub Copilot integration via VS Code MCP
- Pixi-based environment management
- Example scenarios for PV, storage, resilience, wind, and custom loads
