# REopt MCP Server

MCP server for optimizing distributed energy resources using NLR's REopt API. Works with GitHub Copilot Chat in VS Code or Claude Code to evaluate solar, battery storage, wind, and generator technologies through natural conversation.

## Setup

The server is written in TypeScript and run directly with [`tsx`](https://github.com/privatenumber/tsx) — no build step. The steps below are the canonical setup for everyone, including non-developers.

### Prerequisites

- [Node.js](https://nodejs.org) 18+ (uses the global `fetch`)
- NLR API key (free): <https://developer.nlr.gov/signup/>

### Install

```bash
git clone https://github.com/bpulluta/REopt-MCP.git
cd REopt-MCP
npm install
export NLR_API_KEY=your_api_key_here   # or put it in a .env
```

The server reads `NLR_API_KEY` (and optionally `REOPT_API_BASE_URL`, `OPENEI_API_KEY`,
`URDB_API_BASE_URL`) from the environment or a project-root `.env` — see
[.env.example](.env.example).

Do not set `NLR_API_KEY` inside `.vscode/mcp.json` or `.mcp.json` `env` blocks.
Those files should only contain runtime flags (for example `NODE_OPTIONS`).

### Register the server

The server code is identical for both clients; only the config file differs. Both files
are committed in this repo and point at `npx tsx src/index.ts`; adjust the absolute
`cwd` if you cloned elsewhere.

- **Claude Code** — [.mcp.json](.mcp.json) (`mcpServers.reopt`). Enable it in
  [.claude/settings.json](.claude/settings.json) (`enabledMcpjsonServers: ["reopt"]`),
  then run `/mcp` to confirm it is healthy.
- **GitHub Copilot (VS Code 1.99+)** — [.vscode/mcp.json](.vscode/mcp.json)
  (`servers.reopt`). Reload the window, open Copilot Chat in **Agent mode**, and the
  `reopt` tools appear.

### Verify the setup

In Copilot Chat (Agent mode) or Claude Code, ask:

> What REopt tools are available?

You should see `submitAndWait`, `validateScenario`, `getScenarioHelp`, `getSummary`,
and `searchUrdbRates`. Then try a first prompt:

> Evaluate solar and battery for a medium office in Denver with 800000 kWh annual
> usage. Gather any missing information and prepare the scenario.

The assistant should ask for anything missing (rate, technologies), show a preview,
and only run after you approve.

## Usage

The MCP gathers your inputs before running any optimization. It will ask for:

1. **Location** — city/address or lat/lon coordinates
2. **Electric load** — building type (`doe_reference_name`) + annual `annual_kwh` is
   the common case; monthly totals, an hourly `loads_kw` profile, or a CSV also work
   (see `getScenarioHelp('load')`)
3. **Utility rate** — blended, monthly, time-of-use, or a URDB tariff (see
   `getScenarioHelp('tariff')`)

Then you tell it which technologies to evaluate (solar, batteries, wind, generator) and it builds and runs the scenario.

### Example

```
You:  "Analyze solar and batteries for my retail store in Austin, 800k kWh/year"
MCP:  → Asks for utility rate
You:  "$0.12/kWh energy, $18/kW demand"
MCP:  → Builds scenario, submits, returns results with sizing, payback, and NPV
```

### Scenario JSON Structure

```json
{
  "Site": { "latitude": 39.74, "longitude": -104.99 },
  "ElectricLoad": { "doe_reference_name": "MediumOffice", "annual_kwh": 500000 },
  "ElectricTariff": { "blended_annual_energy_rate": 0.12, "blended_annual_demand_rate": 15.0 },
  "PV": {},
  "ElectricStorage": {}
}
```

- Add `"PV": {}`, `"ElectricStorage": {}`, `"Wind": {}`, or `"Generator": {}` for each technology.
- Empty `{}` lets REopt optimize sizing; add constraints only when needed.
- `ElectricLoad` accepts a reference building, a blend, an hourly `loads_kw` array, or a
  `loads_csv` file path (the server reads it into `loads_kw`), plus scalers like
  `annual_kwh` or `monthly_totals_kwh`. See `getScenarioHelp('load')`.
- Off-grid: set `"Settings": {"off_grid_flag": true}` and omit `ElectricTariff`.

## Tools

| Tool | Purpose |
|------|---------|
| `submitAndWait` | Validate → preview → submit → poll → return results |
| `validateScenario` | Check a scenario for errors before submission |
| `getScenarioHelp` | Show structure and examples (`minimal`, `tariff`, `solar`, `all`, etc.) |
| `getSummary` | Format results as markdown (`results`, `financial`, `system`, `all`) |
| `searchUrdbRates` | Search the Utility Rate Database for a utility's published rates |

`submitAndWait` uses a two-step gate: the first call (without `confirm`) returns a preview; the second call (with `confirm: true`) submits.

## Development

```bash
npm run server      # Start the MCP server on stdio
npm test            # Run the vitest suite
npm run typecheck   # Type-check with tsc --noEmit
```

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for the design and data flow, and
**[CONTRIBUTING.md](CONTRIBUTING.md)** for the recipe to add a technology or section
(one module file, not a multi-file edit).

### Project Structure

```
src/
  index.ts           # MCP tool registration + serveStdio entry point
  responses.ts       # Standard tool response envelope (text / errorResult)
  guards.ts          # Shared runtime type guards
  client.ts          # REopt API submit / poll / fetch + array truncation
  http.ts            # Shared fetch wrapper (30s timeout, api_key query param)
  urdb.ts            # URDB (OpenEI) rate search
  validation.ts      # Top-level validation orchestrator + guidance
  summaries.ts       # Markdown result composers (stitch module blocks together)
  format.ts          # Number formatting helpers
  config.ts          # Environment configuration
  constants.ts       # Constants shared across modules
  instructions.ts    # Canonical MCP instruction text
  examples.ts        # Bundled example scenarios (assembled from module fragments)
  modules/           # One module per scenario section/technology (the scalable core)
    types.ts         #   the ScenarioModule contract
    index.ts         #   the registry + normalize/validate/warn helpers
    site.ts electric-load.ts settings.ts electric-tariff.ts
    pv.ts wind.ts electric-storage.ts generator.ts helpers.ts
test/
  fixtures/          # Sample scenario and result JSON
  modules.test.ts    # Registry, example round-trip, summary composition
  tariff.test.ts     # TOU compiler + tariff validators
  validation.test.ts # Validation rules and guidance
  summaries.test.ts  # Markdown formatting
  client.test.ts     # Truncation + polling (mocked fetch)
  urdb.test.ts       # URDB search (mocked fetch)
```

> The original Python implementation lives in `archive/python-server/` for reference.

## Troubleshooting

- **Tools don't appear** — reload the VS Code window; re-check the `cwd` path in
  [.vscode/mcp.json](.vscode/mcp.json) or [.mcp.json](.mcp.json). In Claude Code run
  `/mcp` and confirm `reopt` is healthy.
- **401 / authentication errors** — confirm your `.env` has a valid `NLR_API_KEY`
  (don't put the key in the `mcp.json` `env` blocks).
- **`npx` / `tsx` command errors** — run `npm install` again from the project root.
- **TLS / self-signed certificate errors** (corporate proxy) — launch Node with
  `--use-system-ca` (already set in the committed `mcp.json` via `NODE_OPTIONS`), or
  set `REOPT_TLS_INSECURE=1` on a trusted network. See [.env.example](.env.example).

## Resources

- **REopt API**: <https://github.com/NLR/REopt_API>
- **NLR Developer Portal**: <https://developer.nlr.gov/>
- **Utility Rate Database**: <https://openei.org/apps/USURDB/>
- **MCP Protocol**: <https://modelcontextprotocol.io/>

## License

See [LICENSE](LICENSE).
