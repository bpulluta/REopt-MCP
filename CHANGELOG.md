# Changelog

All notable changes to the REopt MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-07-13

### Changed
- **Rewritten in TypeScript.** The server is now a Node/TypeScript project run
  directly with [`tsx`](https://github.com/privatenumber/tsx) — no build step and
  no Python/Pixi toolchain. The MCP tool surface and behavior are unchanged.
  - `src/index.ts` — MCP tool registration + stdio entry point
  - `src/client.ts`, `src/http.ts` — REopt/URDB API calls, polling, shared fetch wrapper
  - `src/validation.ts`, `src/sections.ts`, `src/tariff.ts` — scenario validation and the
    modular section-handler framework (blended / monthly / TOU / URDB tariffs)
  - `src/summaries.ts`, `src/format.ts` — markdown result formatters
  - `src/config.ts`, `src/constants.ts`, `src/instructions.ts`, `src/examples.ts`, `src/urdb.ts`
- **Tests**: Ported the pytest suite to [Vitest](https://vitest.dev) under `test/`
  (tariff, validation, summaries, client, urdb) with the same fixtures.
- **Tooling**: `npm run server`, `npm test`, and `npm run typecheck` replace the
  Pixi/pytest/Ruff tasks. TLS-inspecting-proxy support via `--use-system-ca` or
  `REOPT_TLS_INSECURE` (see `.env.example`).
- **Docs**: README rewritten for the TypeScript workflow. Removed the outdated
  Pixi/Python setup guide.

### Removed
- The Python implementation (`reopt_mcp/`, `tests/`, `pyproject.toml`, `pixi.toml`,
  `pytest.ini`). Preserved for reference in `archive/python-server/` (not published).

## Prior history (Python implementation)

Versions 0.1.0 through 0.4.0 were the original Python implementation of the server.
It was retired in 0.5.0 and preserved for reference in `archive/python-server/`
(not published). Summary of that lineage:

- **0.4.0** — 2026-07-09 — Simplified configuration to a single API key and base URL;
  clearer connection errors.
- **0.3.0** — 2026-03-09 — Refactored the monolithic server into focused modules;
  streamlined the tool surface to the guided core set; unified the scenario contract
  (`ElectricLoad` requires `doe_reference_name` + `annual_kwh`; `ElectricTariff` accepts
  `urdb_label` or blended rates); added a deterministic unit-test suite.
- **0.2.0** — 2025-12-17 — Corrected the API base path to `/api/reopt/stable`, polled
  results via the `/results` endpoint, and moved `ElectricLoad` to the top level.
- **0.1.0** — 2025-12-11 — Initial MCP server with example scenarios and VS Code
  Copilot integration.
