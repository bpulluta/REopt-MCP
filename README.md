# REopt MCP Server

An AI-powered guide for optimizing distributed energy resources using NREL's REopt API. Works with GitHub Copilot Chat in VS Code to help you evaluate solar, battery storage, wind, and other energy technologies through natural conversation.

## What This Does

This MCP server acts as your **conversational guide** to help you:

1. **Build** proper REopt optimization scenarios by gathering the 3 essential inputs
2. **Select** which technologies to evaluate (solar, batteries, wind, etc.)
3. **Run** optimizations on NREL's servers
4. **Understand** results in plain language with economic and technical analysis

The MCP guides you through providing your specific location, energy consumption, and utility rate - then helps you choose which technologies to evaluate.

## Quick Setup

### Prerequisites

- VS Code with GitHub Copilot Chat extension
- Pixi: `curl -fsSL https://pixi.sh/install.sh | bash`
- NREL API Key (free): https://developer.nrel.gov/signup/

### Install

```bash
git clone https://github.com/bpulluta/REopt-MCP.git
cd REopt-MCP
pixi install
```

### Configure in VS Code

1. `Cmd+Shift+P` → "MCP: Open user configuration"
2. Add this configuration:

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
        "NREL_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

**Replace:**
- `/FULL/PATH/TO/REopt-MCP` with actual path (e.g., `/Users/yourname/REopt-MCP`)
- `YOUR_API_KEY_HERE` with your NREL API key

3. Save and reload: `Cmd+Shift+P` → "Developer: Reload Window"

### Verify

Open Copilot Chat → Click ⚙️ → Confirm `reopt-dev` has checkmark ✓

## How to Use

**The MCP is an information gatherer FIRST, optimizer second.**

It will NEVER jump straight to running optimizations. Instead, it asks questions to gather the 3 required inputs, then builds YOUR scenario based on YOUR answers.

### The Conversation Pattern

1. **You mention what you want** (e.g., "analyze solar for my Denver office")
2. **MCP asks for missing info** (e.g., "What's your energy consumption?")
3. **You provide specifics** (e.g., "500,000 kWh per year")
4. **MCP builds and runs** the optimization with YOUR inputs
5. **MCP presents results** in plain language

### Example Conversations

**Basic Solar Analysis:**
```
You: "I want to analyze solar for my building in Denver"

MCP: "Great! To set up your solar analysis, I need:
      1. Your annual energy consumption in kWh, OR
      2. Your building type (office, retail, hospital, etc.)
      
      Which would you like to provide?"

You: "It's a medium office, about 500,000 kWh per year"

MCP: [Builds scenario with Denver location, 500k kWh, solar only]
     [Runs optimization, presents results]
     
     "Analysis complete! Here are the key findings..."
```

**Solar + Battery:**
```
You: "Evaluate solar and batteries for my retail store in Austin"

MCP: "Got it - solar and batteries for Austin. Do you have your 
      annual energy consumption in kWh, or should I use the DOE 
      reference profile for a typical retail store?"

You: "Use the DOE retail profile"

MCP: [Builds scenario: Austin location, DOE RetailStore profile, solar + battery]
     [Runs optimization, presents results]
     
     "Results show solar + battery is economically viable for Austin retail...
      - Recommended: 120 kW solar + 50 kW/200 kWh battery
      - Payback: 8.5 years
      - NPV: $78,000"
```

**What Happens if You're Too Vague:**
```
You: "Should I get solar?"

MCP: "I'd be happy to help analyze solar for your building! To get started, I need:
      1. Location: Where is your building? (city/state or address)
      2. Energy use: Annual consumption in kWh OR building type (office, retail, etc.)
      
      What can you tell me about your building?"

You: "It's an office in Denver, about 500,000 kWh/year"

MCP: [NOW has enough info - builds and runs optimization]
     "Analysis complete! Here are the results..."
```

**With Constraints:**
```
You: "Analyze solar for my Denver office, 500k kWh/year, but I can only fit 200 kW on my roof"

MCP: [Has all info including constraint - builds immediately with max_kw: 200]
     "Running optimization with 200 kW solar limit...
      Results: Optimal is 200 kW (at your roof capacity limit)..."
```

### The 3 Essential Inputs

The MCP will help you provide:

1. **Location** - City/address or coordinates
   - MCP can convert "Denver" to coordinates
   - More precise = better results

2. **Energy Consumption** - Either:
   - Annual kWh (e.g., "500,000 kWh/year")
   - Building type (e.g., "medium office", "retail store", "hospital")

3. **Utility Rate** - MCP will:
   - Use appropriate rate for your region
   - Help you find your specific utility's rate if needed
   - Explain rate options

### Technologies You Can Evaluate

Tell the MCP what you want to evaluate:

- **Solar** - "analyze solar", "PV potential"
- **Battery** - "add battery storage", "include batteries"  
- **Wind** - "evaluate wind turbines"
- **Generator** - "backup power", "generator"
- **Multiple** - "solar and batteries", "all renewable options"

The MCP adds empty technology objects like `"PV": {}` based on what you ask for - letting REopt optimize sizing unless you specify constraints.

## What Makes This Different

### ❌ What the MCP Will NEVER Do

- Jump straight to running optimizations without your input
- Use "typical parameters" or "standard building" assumptions
- Add technologies you didn't ask for
- Make up values for missing information

### ✅ What the MCP WILL Do

- Ask questions to gather the 3 required inputs
- Help convert city names to coordinates
- Explain building type options (DOE reference profiles)
- Add only the technologies YOU want to evaluate
- Use YOUR specific values, not assumptions
- Present results in plain language

### The Key Principle

**The MCP is an information gatherer first, optimizer second.**

It won't run until it has YOUR location, YOUR energy consumption, and knows which technologies YOU want to evaluate.

No templates. No assumptions. No fabricated data.

Just conversational guidance to help you set up the optimization correctly.

❌ **Not adding fake constraints** - Only adds limits you specify  
✅ **Let REopt optimize** - Uses empty `{}` to find optimal sizes

## Understanding Results

After optimization completes, the MCP presents:

- **System Recommendations** - Optimal sizes for each technology
- **Economics** - Payback period, NPV, savings, costs
- **Technical Details** - Energy production, capacity factors
- **Next Steps** - Options to refine or explore alternatives

Ask follow-up questions like:
- "Explain the payback period"
- "Show financial details"
- "What if I add batteries?"
- "How does this compare to doing nothing?"

## Testing

Verify setup works:

```bash
pixi run simple-test
```

## Development

Run the MCP server directly:

```bash
pixi run server
```

Test with example scenarios:

```python
from reopt_mcp.examples import *

# Base inputs (just the 3 required)
base = get_base_inputs()

# Add solar evaluation
solar = get_solar_scenario()

# Add solar + battery
solar_battery = get_solar_battery_scenario()
```

## Project Structure

```
reopt_mcp/
  server.py          # Main MCP server with conversational instructions
  examples.py        # Helper functions for building scenarios
tests/
  simple_test.py     # Basic API test
  test_mcp.py        # MCP functionality tests
```

## Resources

- **REopt API**: https://github.com/NREL/REopt_API
- **NREL Developer**: https://developer.nrel.gov/
- **Utility Rates**: https://openei.org/apps/USURDB/
- **MCP Protocol**: https://modelcontextprotocol.io/

## License

See LICENSE file for details.

## Support

For issues or questions:
- Open an issue on GitHub
- Check NREL's REopt documentation
- Review example conversations above

---

**Remember**: This MCP is a guide to help you build accurate, customized energy optimizations - not a one-size-fits-all template system. It works with you conversationally to understand your specific needs and create the right scenario.
