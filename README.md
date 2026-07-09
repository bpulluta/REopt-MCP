# REopt MCP Server

MCP server for optimizing distributed energy resources using NLR's REopt API. Works with GitHub Copilot Chat in VS Code to evaluate solar, battery storage, wind, and generator technologies through natural conversation.

## Setup

### Prerequisites

- VS Code with GitHub Copilot Chat
- [Pixi](https://pixi.sh): `curl -fsSL https://pixi.sh/install.sh | bash`
- NLR API key (free): <https://developer.nlr.gov/signup/>

### Install

```bash
git clone https://github.com/bpulluta/REopt-MCP.git
cd REopt-MCP
pixi install
```

### Configure VS Code

1. `Cmd+Shift+P` → **MCP: Open user configuration**
2. Add:

```json
{
  "mcpServers": {
    "reopt-dev": {
      "type": "stdio",
      "command": "pixi",
      "args": ["run", "--manifest-path", "/FULL/PATH/TO/REopt-MCP/pixi.toml", "server"],
      "env": { "NLR_API_KEY": "YOUR_API_KEY" }
    }
  }
}
```

3. Replace the path and API key, then reload the window.
4. Open Copilot Chat → click ⚙️ → confirm `reopt-dev` shows a checkmark.

## Usage

The MCP gathers your inputs before running any optimization. It will ask for:

1. **Location** — city/address or lat/lon coordinates
2. **Electric load** — building type (`doe_reference_name`) and annual consumption (`annual_kwh`)
3. **Utility rate** — blended energy rate ($/kWh) and demand rate ($/kW)

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
- Off-grid: set `"Settings": {"off_grid_flag": true}` and omit `ElectricTariff`.

## Tools

| Tool | Purpose |
|------|---------|
| `submitAndWait` | Validate → preview → submit → poll → return results |
| `validateScenario` | Check a scenario for errors before submission |
| `getScenarioHelp` | Show structure and examples (`minimal`, `solar`, `all`, etc.) |
| `getSummary` | Format results as markdown (`results`, `financial`, `system`, `all`) |

`submitAndWait` uses a two-step gate: the first call (without `confirm`) returns a preview; the second call (with `confirm: true`) submits.

## Development

```bash
pixi run server          # Start MCP server
pixi run test            # Run unit tests
pixi run lint            # Lint with Ruff
pixi run format-check    # Check formatting
pixi run simulate list   # List tools and schemas
```

### Simulate tool calls locally

```bash
pixi run simulate call validateScenario --input tests/fixtures/solar_scenario.json
pixi run simulate call submitAndWait --input tests/fixtures/solar_scenario.json --mock
pixi run simulate call getSummary --args '{"run_uuid":"mock-run-001","kind":"all"}' --mock
```

### Project Structure

```
reopt_mcp/
  tools.py           # MCP tool registration and handlers
  client.py          # REopt API submit / poll / fetch
  validation.py      # Scenario validation and guidance
  summaries.py       # Markdown result formatters
  config.py          # Environment configuration
  constants.py       # Shared constants and valid key sets
  instructions.py    # Canonical MCP instruction text
  examples.py        # Bundled example scenarios
  mock.py            # Fixture-based mock API for testing
  simulate.py        # CLI for offline tool testing
  server.py          # Entry point
tests/
  fixtures/          # Sample scenario and result JSON
  test_tools.py      # Tool dispatch and simulate CLI
  test_validation.py # Validation rules
  test_summaries.py  # Markdown formatting
  test_examples.py   # Example scenario validity
  test_client.py     # Mocked HTTP client
  test_config.py     # Configuration
  test_integration_api.py  # Live API smoke test (opt-in)
```

## Resources

- **REopt API**: <https://github.com/NLR/REopt_API>
- **NLR Developer Portal**: <https://developer.nlr.gov/>
- **Utility Rate Database**: <https://openei.org/apps/USURDB/>
- **MCP Protocol**: <https://modelcontextprotocol.io/>

## License

See [LICENSE](LICENSE).
