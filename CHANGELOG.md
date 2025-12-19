# Changelog

All notable changes to the REopt MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
