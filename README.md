# REopt MCP Server

A Model Context Protocol (MCP) server for NREL's REopt API - enabling AI assistants to optimize energy systems for buildings and microgrids through **GitHub Copilot Chat** in VS Code.

> **🎯 Ready to use:** This MCP server integrates seamlessly with GitHub Copilot Chat. Follow the 3-step setup below to start optimizing solar, battery storage, and other distributed energy resources using natural language.

## 🚀 Quick Setup (3 Steps)

### 1️⃣ Install Prerequisites
- **VS Code** with **GitHub Copilot Chat** extension
- **Pixi:** `curl -fsSL https://pixi.sh/install.sh | bash`
- **NREL API Key:** Get free at https://developer.nrel.gov/signup/

### 2️⃣ Clone & Install
```bash
git clone https://github.com/bpulluta/REopt-MCP.git
cd REopt-MCP
pixi install
```

### 3️⃣ Configure in VS Code
1. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Win/Linux)
2. Type **"MCP: Open user configuration"** and select it
3. Add this configuration (update paths and API key):

```json
{
  "mcpServers": {
    "reopt-dev": {
      "type": "stdio",
      "command": "pixi",
      "args": [
        "run",
        "--manifest-path",
        "/FULL/PATH/TO/REopt-MCP/pixi.toml",
        "server"
      ],
      "env": {
        "NREL_API_KEY": "YOUR_NREL_API_KEY_HERE"
      }
    }
  }
}
```

**⚠️ Critical:** 
- Replace `/FULL/PATH/TO/REopt-MCP` with the **absolute path** where you cloned this repo
  - Example (Mac): `/Users/yourname/REopt-MCP/pixi.toml`
  - Example (Windows): `C:/Users/yourname/REopt-MCP/pixi.toml`
- Replace `YOUR_NREL_API_KEY_HERE` with your actual API key from NREL
- Do **not** use `~`, relative paths, or environment variables in the path

<details>
<summary>📝 Optional: Advanced Configuration with Debug Support</summary>

If you're developing or debugging the MCP server, you can add these optional fields:

```json
{
  "mcpServers": {
    "reopt-dev": {
      "type": "stdio",
      "command": "pixi",
      "args": [
        "run",
        "--manifest-path",
        "/FULL/PATH/TO/REopt-MCP/pixi.toml",
        "server"
      ],
      "env": {
        "NREL_API_KEY": "YOUR_NREL_API_KEY_HERE"
      },
      "dev": {
        "watch": "reopt_mcp/**/*.py",
        "debug": {
          "type": "debugpy",
          "options": {
            "host": "127.0.0.1",
            "port": 5678,
            "wait": false
          }
        }
      }
    }
  }
}
```

This enables automatic server restart when Python files change and allows attaching a debugger.

</details>

4. **Save the file** and reload VS Code: `Cmd+Shift+P` → "Developer: Reload Window"

### ✅ Verify It's Working
1. Open **Copilot Chat** (click chat icon or `Cmd+Shift+I`)
2. Click the **⚙️ configure tools** icon in the chat input
3. Look for **`reopt-dev`** with a **checkmark ✓** - you're ready!

**Test it:** Type in chat: *"Help me optimize solar for my building"*

---

## What Can This Do?

The MCP server helps you optimize solar, battery storage, and other energy systems through natural conversation. Just ask questions and Copilot will guide you through:

- **Location setup** - Find coordinates for accurate solar data
- **Utility rates** - Search real tariffs or use custom rates
- **Load profiles** - Use building templates or actual consumption data
- **Run optimizations** - Get system sizes, costs, and payback analysis

## How It Works

**Example:** *"Help me optimize solar for a retail store in Austin, Texas"*

Copilot will automatically:
1. Guide you to find the exact building coordinates
2. Search for Austin Energy utility rates in the database
3. Help select the RetailStore load profile
4. Validate all inputs before running
5. Run optimization (30-120 seconds)
6. Show system sizes, costs, and financial analysis

**You just use natural language** - the MCP tools work behind the scenes.

## Why Accurate Inputs Matter

### Impact of Input Quality

| Input | Low Quality | High Quality | Impact |
|-------|-------------|--------------|--------|
| **Location** | State/city centroid | Exact building coordinates | ±5-10% solar production |
| **Utility Rates** | Generic blended rates | Actual URDB tariff | ±20-50% savings, ±2-5 years payback |
| **Load Data** | DOE profile only | Actual hourly data | ±15-25% system sizing |

### Real-World Example

**Scenario**: 500,000 kWh/year retail store in Austin, TX

**With Generic Inputs:**
- Location: Austin city center (approximation)
- Rate: $0.10/kWh blended (assumed)
- Load: DOE RetailStore profile + annual kWh

**Result**: 120 kW solar, 9.3 year payback, $44k NPV ❌

**With Accurate Inputs:**
- Location: Exact building coordinates (30.2672, -97.7431)
- Rate: Austin Energy GS-2 (URDB: 5e6d89ac5457a3c4415f3a47)
- Load: Actual hourly interval meter data

**Result**: 145 kW solar + 50kWh battery, 6.2 year payback, $128k NPV ✅

**Difference**: $84,000 NPV, 3.1 years payback - dramatically different investment decision!

## Usage Examples with Copilot Chat

Once you've completed the setup above, you can interact with REopt through natural language in Copilot Chat:

**Getting Started:**
```
Help me analyze solar potential for my building

I want to optimize energy systems for a warehouse in Denver
```

**Guided Setup:**
```
Guide me through location setup for Austin, Texas

Search for utility rates for Pacific Gas & Electric

What reference building types are available?
```

**Running Optimizations:**
```
Optimize solar and battery storage for a medium office building

Validate my scenario before submitting

Submit optimization for my retail store with the inputs we discussed
```

**Analyzing Results:**
```
Show me the financial summary

What's the recommended system size?

Explain the payback period
```

The MCP server will automatically guide you through the three critical inputs (location, utility rates, load data) and help you run accurate optimizations.

## Testing the Installation

You can verify your setup is working correctly by running the test script:

```bash
pixi run python tests/simple_test.py
```

This will test the API connection and validate your NREL API key is configured correctly.

## Usage with Claude Desktop (Alternative)

If you prefer to use Claude Desktop instead of VS Code, add this configuration to:
`~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or  
`%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "reopt": {
      "command": "pixi",
      "args": ["run", "--manifest-path", "/FULL/PATH/TO/REopt-MCP/pixi.toml", "server"],
      "env": {
        "NREL_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

Replace `/FULL/PATH/TO/REopt-MCP` with the absolute path to this repository and `YOUR_API_KEY_HERE` with your NREL API key.

## MCP Tools

The following tools are available through the MCP server. You don't need to call these directly - just use natural language in Copilot Chat and it will use the appropriate tools automatically.

### 🚀 Core Tools

| Tool | Purpose |
|------|---------|
| `submitAndWait` | Submit optimization and wait for results (recommended) |
| `getResultsSummary` | Get concise summary of system recommendations |
| `getFinancialSummary` | Detailed financial analysis (NPV, payback, IRR) |
| `getSystemSummary` | Technology performance specifications |
| `validateScenarioInputs` | Validate inputs before submission |

### 📚 Setup & Discovery Tools

| Tool | Purpose |
|------|---------|
| `guideLocationSetup` | Help find precise coordinates |
| `guideUtilityRateSetup` | Explain utility rate options |
| `guideLoadDataSetup` | Guide through load data setup |
| `searchUtilityRates` | Search URDB for utility tariffs |
| `listDOEReferenceBuildings` | List available building profiles |
| `getExampleScenario` | Get template scenario structure |

### 🔧 Advanced Tools

| Tool | Purpose |
|------|---------|
| `submitReoptJob` | Submit job, returns UUID (manual polling) |
| `waitForJob` | Wait for existing job to complete |
| `getJobStatus` | Check status of running job |
| `getJobResults` | Get full results (large output) |

## Example Scenario Structure
```json
{
  "Site": {
    "latitude": 39.7407,
    "longitude": -104.9890
  },
  "ElectricLoad": {
    "doe_reference_name": "MediumOffice",
    "annual_kwh": 1000000
  },
  "ElectricTariff": {
    "urdb_label": "5ca4d1175457a39b23b3d45e"
  },
  "PV": {
    "max_kw": 1000
  },
  "ElectricStorage": {
    "max_kw": 500,
    "max_kwh": 1000
  }
## Example Scenario Structure

```json
{
  "Site": {
    "latitude": 39.7407,
    "longitude": -104.9890
  },
  "ElectricLoad": {
    "doe_reference_name": "MediumOffice",
    "annual_kwh": 1000000
  },
  "ElectricTariff": {
    "urdb_label": "5ca4d1175457a39b23b3d45e"
  },
  "PV": {
    "max_kw": 1000
  },
  "ElectricStorage": {
    "max_kw": 500,
    "max_kwh": 1000
  }
}
```

**Available DOE reference buildings:** `Hospital`, `LargeOffice`, `MediumOffice`, `SmallOffice`, `RetailStore`, `RetailStripmall`, `PrimarySchool`, `SecondarySchool`, `Warehouse`, `FastFoodRest`, `FullServiceRest`, `LargeHotel`, `SmallHotel`

**Technologies:** `PV`, `ElectricStorage`, `Wind`, `Generator`, `CHP`, and more

## Project Structure

```
REopt-MCP/
├── reopt_mcp/          # Main package
│   ├── server.py       # MCP server implementation
│   └── examples.py     # Example scenarios
├── tests/              # Test scripts
├── dev-docs/           # Development documentation (git-ignored)
├── .vscode/            # VS Code MCP configuration
├── pixi.toml           # Pixi dependencies & tasks
├── pyproject.toml      # Python package metadata
├── .env.example        # Environment template
├── README.md           # This file
└── CHANGELOG.md        # Version history
```

## Development

```bash
# Run tests
pixi run python tests/simple_test.py
pixi run python tests/test_api_direct.py

# View examples
pixi run python -m reopt_mcp.examples

# Start server manually
pixi run server
```

## Resources

- [REopt API Documentation](https://developer.nrel.gov/docs/energy-optimization/reopt/v3/)
- [REopt.jl Technical Docs](https://nrel.github.io/REopt.jl/dev/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Get NREL API Key](https://developer.nrel.gov/signup/)

## Important Notes

### About MCP Configuration

- **Use absolute paths:** The `manifest-path` must be a full absolute path (e.g., `/Users/yourname/REopt-MCP/pixi.toml`). Do not use `~`, relative paths, or environment variables.
- **API key location:** Your NREL API key should be in the MCP configuration file, not in a `.env` file.
- **Server name:** The server name `reopt-dev` must match exactly in the configuration and when checking the tools menu.
- **Reload required:** After any configuration changes, always reload VS Code for changes to take effect.

### Optimization Timing

- **Normal duration:** Most optimizations complete in 30-120 seconds
- **Complex scenarios:** May take up to 2 minutes for large systems or multiple technologies
- **Automatic waiting:** The `submitAndWait` tool handles all polling automatically

### Best Practices

- **Always validate first:** Use `validateScenarioInputs` before submitting to catch errors early
- **Use real data:** Accurate location, utility rates, and load data make a huge difference (see "Why Accurate Inputs Matter")
- **Start simple:** Begin with just solar (PV) before adding battery storage or other technologies
- **Check results:** Review the financial summary to ensure the recommendations make sense for your site

## Troubleshooting

### MCP Server Not Appearing in Copilot Chat

**Problem:** Don't see `reopt-dev` with a checkmark in the configure tools menu.

**Solutions:**
1. Verify the configuration path is absolute (no `~` or relative paths)
2. Check that `pixi.toml` exists at the specified path
3. Ensure your NREL API key is valid
4. Reload VS Code: `Cmd+Shift+P` → "Developer: Reload Window"
5. Check VS Code Output panel → "MCP" for error messages

### API Key Issues

**Problem:** Getting authentication errors.

**Solutions:**
1. Verify your API key is correct (no extra spaces)
2. Get a new key at https://developer.nrel.gov/signup/
3. Make sure the key is set in the MCP configuration (not .env file)

### Pixi Not Found

**Problem:** VS Code can't find the `pixi` command.

**Solutions:**
1. Install Pixi: `curl -fsSL https://pixi.sh/install.sh | bash`
2. Restart your terminal and VS Code
3. Use full path to pixi in configuration: `/Users/YOUR_USERNAME/.pixi/bin/pixi`

### Optimization Takes Too Long

**Problem:** Job seems stuck or taking over 2 minutes.

**Solutions:**
1. This is normal for complex scenarios (up to 2 minutes)
2. Check job status to confirm it's processing
3. Simplify scenario (reduce `max_kw` values)
4. Check NREL API status at https://developer.nrel.gov/

### Results Don't Make Sense

**Problem:** Getting unexpected recommendations (e.g., very large systems, odd payback periods).

**Solutions:**
1. **Use `validateScenarioInputs` first** - catches common errors
2. **Verify location** - coordinates should be near your actual site
3. **Check utility rates** - use URDB labels instead of generic rates
4. **Validate load data** - ensure annual_kwh matches your actual consumption
5. See "Why Accurate Inputs Matter" section above

### Getting Help

**Still having issues?**
1. Check the [dev-docs](dev-docs/) folder for detailed guides
2. Run diagnostic test: `pixi run python tests/simple_test.py`
3. Open an issue on GitHub with:
   - Your VS Code version
   - MCP configuration (redact API key)
   - Error messages from Output panel

## Contributing

See `dev-docs/` for development documentation. Issues and PRs welcome!

## Advanced: Local Development with .env

If you're developing the MCP server itself (not just using it), you can optionally use a `.env` file:

```bash
cp .env.example .env
# Edit .env and add your NREL_API_KEY
```

This is only needed for running tests directly with `pixi run python tests/`. For normal Copilot Chat usage, configure the API key in the MCP user configuration as shown above.

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

*Built with [Pixi](https://pixi.sh) and [MCP](https://modelcontextprotocol.io/)*
