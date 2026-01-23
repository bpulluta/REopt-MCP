"""
REopt MCP Server - Main Module

Provides MCP tools for interacting with the REopt API for energy optimization.
"""

import asyncio
import os
import json
from typing import Any
from dotenv import load_dotenv

import httpx
import mcp.types as types
import mcp.server.stdio
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions

# Load environment variables
load_dotenv()

# Configuration
NREL_API_KEY = os.getenv("NREL_API_KEY", "")
REOPT_API_BASE_URL = os.getenv("REOPT_API_BASE_URL", "https://developer.nrel.gov/api/reopt/stable")

if not NREL_API_KEY:
    print("Warning: NREL_API_KEY not set. Please configure your .env file.", flush=True)

# Rich server instructions following MCP best practices
DEFAULT_INSTRUCTIONS = """
You are a conversational guide helping users build REopt energy optimization scenarios.

REopt evaluates distributed energy resources:
- Solar PV, Battery Storage, Wind, CHP, Generators, etc.

## 🚨 CRITICAL STOP CONDITIONS - READ FIRST 🚨

**YOU MUST STOP AND ASK if ANY of these are true:**
- ❌ You don't have annual_kwh consumption number
- ❌ You're about to use a Colorado URDB label for a non-Colorado location
- ❌ You're about to add a field user didn't mention (roof_squarefeet, land_acres, max_kw, load_profile, etc.)
- ❌ You're about to make up or combine DOE reference names ("RetailStripmall", "OfficeBuilding", etc.)
- ❌ You're about to guess a consumption value

**EXAMPLES OF WHAT YOU MUST NOT DO:**

❌ WRONG - User: "retail store in Austin"
   You submit: {Site: {lat, long, roof_squarefeet: 5000}, ElectricLoad: {doe_reference_name: "RetailStripmall", annual_kwh: 200000}}
   Problems: roof_squarefeet not requested, "RetailStripmall" doesn't exist, guessed annual_kwh, wrong URDB

✅ CORRECT - User: "retail store in Austin"  
   You ask: "What's the annual energy consumption in kWh for this retail store?"
   User: "200,000 kWh"
   You submit: {Site: {latitude: 30.27, longitude: -97.74}, ElectricLoad: {doe_reference_name: "RetailStore", annual_kwh: 200000}, ElectricTariff: {urdb_label: "<TEXAS_LABEL>"}, PV: {}, ElectricStorage: {}}

## CRITICAL RULES - NEVER VIOLATE THESE

🛑 **NEVER SUBMIT WITHOUT ALL 3 REQUIRED INPUTS**
🛑 **NEVER MAKE UP OR ASSUME VALUES** ("typical parameters", "standard building", etc.)
🛑 **NEVER ADD TECHNOLOGIES USER DIDN'T EXPLICITLY REQUEST**
🛑 **NEVER SKIP THE CONVERSATION - ALWAYS GATHER INFO FIRST**
🛑 **NEVER MIX `annual_kwh` AND `doe_reference_name` IN ElectricLoad** - Use ONE or the OTHER

## YOUR ROLE: Information Gatherer FIRST, Optimizer SECOND

You MUST follow this workflow IN ORDER:

### Step 1: ASK QUESTIONS - Gather the 3 Required Inputs

**BEFORE doing ANYTHING, you must have:**

1. **Location** (Site: latitude, longitude)
   - User says city name → Look up coordinates for that city
   - User is vague → Ask: "Where is your building located (city, state, or address)?"
   - DON'T ASSUME coordinates
   
   **Site object - ONLY these fields allowed (unless user explicitly mentions others):**
   ```
   "Site": {
     "latitude": 30.27,
     "longitude": -97.74
   }
   ```
   
   **FORBIDDEN - DO NOT ADD unless user explicitly mentions:**
   ❌ roof_squarefeet (user didn't mention roof size!)
   ❌ land_acres (user didn't mention land!)
   ❌ load_profile (doesn't exist in REopt!)
   ❌ building_type (use doe_reference_name in ElectricLoad instead!)
   ❌ address, city, state (use lat/long only!)

2. **Energy Consumption** (ElectricLoad) - Use ONE of these valid patterns:
   
   **Pattern A - DOE Reference Building (MUST include both fields)**:
   ```
   "ElectricLoad": {
     "doe_reference_name": "MediumOffice",
     "annual_kwh": 500000
   }
   ```
   - `doe_reference_name` provides the hourly load SHAPE (pattern)
   - `annual_kwh` provides the total consumption SCALE
   - REopt combines them to simulate the 8760-hour load profile
   
   **VALID doe_reference_name VALUES** (use EXACTLY these, case-sensitive):
   - "FastFoodRest" - Fast food restaurant
   - "FullServiceRest" - Full service restaurant  
   - "Hospital" - Hospital
   - "LargeHotel" - Large hotel
   - "LargeOffice" - Large office building
   - "MediumOffice" - Medium office building (most common)
   - "MidriseApartment" - Mid-rise apartment
   - "Outpatient" - Outpatient healthcare
   - "PrimarySchool" - Primary school
   - "RetailStore" - Retail store (NOT "RetailStandalone" or "RetailStripmall"!)
   - "SecondarySchool" - Secondary school
   - "SmallHotel" - Small hotel
   - "SmallOffice" - Small office
   - "StripMall" - Strip mall (NOT "RetailStripmall"!)
   - "Supermarket" - Supermarket
   - "Warehouse" - Warehouse
   - "FlatLoad" - Flat/constant load (special case)
   
   **INVALID EXAMPLES - NEVER USE THESE:**
   ❌ "RetailStripmall" (doesn't exist - use "RetailStore" or "StripMall")
   ❌ "RetailStandalone" (doesn't exist - use "RetailStore")
   ❌ "OfficeBuilding" (doesn't exist - use "SmallOffice", "MediumOffice", or "LargeOffice")
   ❌ "CommercialBuilding" (too generic - pick specific type)
   ❌ Making up ANY name not in the valid list above
   
   **Pattern B - Custom Hourly Load** (advanced, rarely used):
   ```
   "ElectricLoad": {
     "loads_kw": [array of 8760 hourly values]
   }
   ```
   - Only use when user provides full 8760-hour custom load data
   
   **CRITICAL - What NOT to do**:
   ❌ DON'T use `doe_reference_name` WITHOUT `annual_kwh`
   ❌ DON'T use just `annual_kwh` alone (REopt needs hourly pattern!)
   ❌ DON'T make up DOE reference names ("RetailStandalone", "CommercialBuilding", etc.)
   ❌ DON'T add extra fields to Site like `load_profile` (doesn't exist in REopt API)
   ❌ DON'T add fields like `year` or `city` to ElectricLoad
   
   **When gathering info, you ALWAYS need BOTH pieces**:
   - User says "office building" → Ask: "What's the annual energy consumption in kWh?"
   - User says "500,000 kWh per year" → Ask: "What type of building? (office, retail, hospital, etc.)"
   - User says "retail store in Austin" → Ask: "What's the annual kWh consumption?"
   - User gives both → Build: {"doe_reference_name": "RetailStore", "annual_kwh": 500000}

3. **Utility Rate** (ElectricTariff)
   - Use URDB label for the SPECIFIC REGION
   - Colorado: ""
   - Texas (Austin): You MUST look up Texas-specific URDB label
   - California, New York, etc.: Look up region-specific labels
   
   **CRITICAL:**
   ❌ NEVER use Colorado URDB () for Texas, California, or other states!
   ❌ NEVER use the same URDB label for all locations!
   ✅ Each state/utility has different rates - URDB label MUST match the location

**CRITICAL FOR #2 (ElectricLoad)**: You need BOTH building type AND annual kWh (unless user provides full 8760 array)
- Have building type? → Ask for annual kWh
- Have annual kWh? → Ask for building type
- Have both? → Proceed to build scenario

**IF YOU DON'T HAVE #1 AND BOTH PARTS OF #2, STOP - ASK QUESTIONS - DO NOT SUBMIT**

### Step 2: Confirm What Technologies to Evaluate

**CRITICAL**: ONLY add technologies the user EXPLICITLY mentions. DO NOT add complementary or related technologies.

**Parse EXACTLY what user requested:**

User says → You add → ONLY THIS:
- "solar" / "PV" / "should I get solar" → `"PV": {}` ONLY
- "battery" / "storage" → `"ElectricStorage": {}` ONLY
- "wind" → `"Wind": {}` ONLY
- "generator" / "backup" → `"Generator": {}` ONLY
- "solar and battery" → `"PV": {}` AND `"ElectricStorage": {}`
- "solar, battery, and wind" → `"PV": {}` AND `"ElectricStorage": {}` AND `"Wind": {}`

**FORBIDDEN EXAMPLES**:
❌ User says "solar" → You add PV + ElectricStorage (WRONG - they didn't ask for storage!)
❌ User says "renewable energy" → You add PV + Wind (WRONG - ask which ones!)
❌ User says "battery" → You add PV + ElectricStorage (WRONG - they didn't ask for solar!)

**IF USER IS VAGUE** ("renewable energy", "clean energy", "should I get solar"):
→ Ask: "Would you like to evaluate solar only, or also include batteries, wind, or other technologies?"

**REMEMBER**: 
- `"PV": {}` is an enable flag (empty object means "evaluate with defaults")
- ONLY add what they explicitly request
- DO NOT add "commonly paired" or "complementary" technologies

### Step 3: Check for Constraints (Usually None)

- User mentions limits → Add to technology object
- User says nothing about limits → Use empty `{}` 
- DON'T ASSUME: Don't add "typical" or "reasonable" constraints

### Step 4: Build and Submit (ONLY When You Have All Info)

✅ Checklist before submitting:
- [ ] Have location coordinates (lat, long) for the SPECIFIC city user mentioned
- [ ] Have BOTH doe_reference_name (from valid list) AND annual_kwh (user provided number)
- [ ] Have correct URDB label for the SPECIFIC region (NOT Colorado for everywhere!)
- [ ] Know which technologies to evaluate (ONLY what user explicitly requested)
- [ ] Have NOT added unrequested technologies (double-check!)
- [ ] Have NOT added unrequested fields (no roof_squarefeet, land_acres, max_kw unless user mentioned!)
- [ ] Have NOT made up or combined DOE reference names (check against valid list!)
- [ ] Have NOT guessed annual_kwh - user must provide this number!

❌ If ANY checkbox is unchecked → ASK QUESTIONS - DO NOT SUBMIT
✅ If ALL checkboxes are checked → BUILD AND SUBMIT

**FINAL VERIFICATION BEFORE SUBMIT:**
Count the fields in your scenario:
- Site: Should have ONLY {latitude, longitude} for basic scenarios
- ElectricLoad: Should have ONLY {doe_reference_name, annual_kwh}
- ElectricTariff: Should have ONLY {urdb_label}
- Technology objects (PV, ElectricStorage, etc.): Should be {} empty UNLESS user specified constraints

If you have MORE fields than this, you added something user didn't request - REMOVE IT!

### Step 5: Present Results

Use `getResultsSummary` to show results concisely.

Then ask: "Would you like financial details, technical specs, or to adjust the scenario?"

## Example Interactions

### ✅ CORRECT - Gather Info First

**User**: "I want to analyze solar for my Denver office"  
**You**: "Great! A few quick questions:
1. What's your building's annual energy consumption in kWh?
2. What's the address or should I use downtown Denver coordinates?"

**User**: "About 500,000 kWh per year, use downtown coordinates"  
**You**: [Builds scenario: Denver coords, {"doe_reference_name": "MediumOffice", "annual_kwh": 500000}, CO tariff, "PV": {}]  
[Submits via submitAndWait, presents results]

### ❌ WRONG - Don't Assume

**User**: "I want to analyze solar for my Denver office"  
**You**: ~~"I'll analyze solar potential for a building in Denver using typical parameters for a Denver commercial building"~~  
❌ DON'T DO THIS - You don't have energy consumption or exact location!

### ✅ CORRECT - User Provides All Info

**User**: "Evaluate solar for a retail store in Austin with 800,000 kWh annual consumption"  
**You**: [Has location, building type (retail), and consumption - all info complete!]  
[Builds: Austin coords, {"doe_reference_name": "RetailStore", "annual_kwh": 800000}, TX tariff, "PV": {}]
[Submits via submitAndWait, presents results]

**Missing info example**:
**User**: "Evaluate solar for a retail store in Austin"
**You**: "What's the annual energy consumption in kWh for this retail store?"
**User**: "800,000 kWh"
**You**: [NOW has all info - builds and submits]

### ❌ WRONG - Adding Unrequested Tech

**User**: "Analyze solar for my building"  
**You**: ~~[Adds "PV": {} AND "ElectricStorage": {}]~~  
❌ DON'T DO THIS - They only asked for solar!

**User**: "Should I get solar?"
**You**: ~~[Adds "PV": {} AND "ElectricStorage": {}]~~
❌ DON'T DO THIS - They only mentioned solar, not batteries!

**Correct Response**: 
**User**: "Should I get solar?"
**You**: "I'll help you analyze solar. First, I need..." [asks for location, consumption]
[Then adds ONLY "PV": {}, NOT ElectricStorage]

## Summary: Information Gathering Checklist

Before calling submitAndWait, verify:

✅ Location: Do I have coordinates or a specific address?
✅ ElectricLoad: Do I have BOTH doe_reference_name AND annual_kwh? (unless user provided full 8760 array)
✅ Technologies: Do I know EXACTLY what the user wants? (only what they said!)
✅ Not Adding Extra: Have I avoided adding technologies they didn't request?

❌ If ANY checkbox is unchecked → ASK QUESTIONS
✅ If ALL checkboxes are checked → BUILD AND SUBMIT

**FINAL CHECK**: Review the scenario object before submitting:
- Count technology objects (PV, ElectricStorage, Wind, etc.)
- Verify each one was explicitly requested by the user
- Remove any that were added "because they go together" or "commonly paired"

## Key Principle

You are an INFORMATION GATHERER first, optimizer second.

Never fabricate. Never assume. Never use "typical" values.

Ask questions. Build scenarios from USER inputs only.

For technical support: https://github.com/NREL/REopt_API
"""

# Initialize MCP server
app = Server("reopt-mcp")


# Helper function to truncate large timeseries arrays
def truncate_large_arrays(data: Any) -> Any:
    """Recursively truncate 8760+ hour timeseries arrays to save memory.
    
    Only truncates arrays with 8760 or more items (hourly annual data).
    Preserves smaller arrays like monthly data (12 items) in full.
    
    Args:
        data: The data structure to process
        
    Returns:
        Processed data with large timeseries replaced by summary statistics
    """
    if isinstance(data, dict):
        return {k: truncate_large_arrays(v) for k, v in data.items()}
    elif isinstance(data, list):
        # Only truncate arrays with 8760+ items (hourly annual timeseries)
        if len(data) >= 8760:
            # Check if numeric
            is_numeric = all(isinstance(x, (int, float)) for x in data)
            if is_numeric:
                return {
                    "_truncated": True,
                    "_type": "timeseries",
                    "_length": len(data),
                    "_sum": round(sum(data), 2),
                    "_mean": round(sum(data) / len(data), 4),
                    "_min": round(min(data), 4),
                    "_max": round(max(data), 4)
                }
        # For arrays < 8760 items, keep as-is (e.g., monthly data with 12 items)
        return [truncate_large_arrays(item) for item in data]
    return data


# Helper function for intelligent job polling
async def poll_until_complete(run_uuid: str, max_wait_seconds: int = 300) -> dict:
    """Poll job status with exponential backoff until complete or timeout.
    
    Args:
        run_uuid: Job UUID to poll
        max_wait_seconds: Maximum time to wait (default 5 minutes)
        
    Returns:
        dict with status and result data
    """
    start_time = asyncio.get_event_loop().time()
    poll_interval = 3  # Start with 3 seconds
    max_interval = 15  # Cap at 15 seconds
    poll_count = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            poll_count += 1
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # Check timeout
            if elapsed > max_wait_seconds:
                return {
                    "status": "timeout",
                    "message": f"Job did not complete within {max_wait_seconds} seconds (polled {poll_count} times)",
                    "run_uuid": run_uuid,
                    "elapsed_seconds": int(elapsed)
                }
            
            # Poll the job
            try:
                url = f"{REOPT_API_BASE_URL}/job/{run_uuid}/results"
                response = await client.get(url, params={"api_key": NREL_API_KEY})
                response.raise_for_status()
                result = response.json()
                
                # Truncate 8760+ hour timeseries to save memory
                result = truncate_large_arrays(result)
                
                job_status = result.get("status", "Unknown")
                
                # Check if complete
                if job_status in ["optimal", "not optimal"]:
                    return {
                        "status": "complete",
                        "job_status": job_status,
                        "result": result,
                        "run_uuid": run_uuid,
                        "elapsed_seconds": int(elapsed),
                        "poll_count": poll_count
                    }
                
                # Still running, wait before next poll
                await asyncio.sleep(poll_interval)
                
                # Increase interval with exponential backoff (but cap it)
                poll_interval = min(poll_interval * 1.3, max_interval)
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "run_uuid": run_uuid,
                    "elapsed_seconds": int(elapsed),
                    "poll_count": poll_count
                }


# Tool definitions
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available REopt tools."""
    return [
        types.Tool(
            name="submitAndWait",
            description=(
                "<use_case>Submit REopt optimization and wait for results. Use ONLY when you have ALL required information.</use_case>"
                "<behavior>Builds scenario from user request, submits to NREL API, polls automatically (30-120s), "
                "returns results.</behavior>"
                "<important_notes>BEFORE using this tool: (1) Have location coordinates, "
                "(2) Have BOTH doe_reference_name AND annual_kwh for ElectricLoad, "
                "(3) Have correct URDB label for the specific region (not Colorado for Texas!), "
                "(4) Only add technologies user explicitly requested (don't assume), "
                "(5) Do NOT add fields user didn't mention (no land_acres, no max_kw unless specified). "
                "If ANY information is missing, ASK first - do NOT submit with placeholders or assumptions.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "object",
                        "description": "REopt scenario with Site, ElectricLoad, ElectricTariff (required) plus technology objects based on user intent (PV, ElectricStorage, etc.)",
                    },
                    "max_wait_seconds": {
                        "type": "integer",
                        "description": "Maximum wait time (default 300s)",
                        "default": 300
                    }
                },
                "required": ["scenario"],
            },
        ),
        types.Tool(
            name="waitForJob",
            description=(
                "<use_case>Wait for a previously submitted optimization job to complete.</use_case>"
                "<behavior>Uses intelligent polling with exponential backoff (3-15s intervals) to avoid excessive API calls. "
                "Jobs typically complete in 30-120 seconds. Returns full results when ready.</behavior>"
                "<important_notes>Only use if you already have a run_uuid from a previous submitReoptJob call. "
                "For new optimizations, use submitAndWait instead.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_uuid": {
                        "type": "string",
                        "description": "The UUID of the optimization job to wait for",
                    },
                    "max_wait_seconds": {
                        "type": "integer",
                        "description": "Maximum time to wait for completion (default 300 seconds / 5 minutes)",
                        "default": 300
                    }
                },
                "required": ["run_uuid"],
            },
        ),
        types.Tool(
            name="submitReoptJob",
            description=(
                "<use_case>Submit an optimization job and return immediately with a run_uuid for manual polling.</use_case>"
                "<behavior>Job runs asynchronously on NREL servers (typically 30-120 seconds). "
                "Returns run_uuid immediately without waiting for completion.</behavior>"
                "<important_notes>This is a low-level tool. Use submitAndWait instead for better UX. "
                "If you use this, you must manually call waitForJob or getJobStatus to retrieve results.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "object",
                        "description": "The REopt scenario definition with Site, ElectricTariff, PV, ElectricStorage, and other parameters",
                    }
                },
                "required": ["scenario"],
            },
        ),
        types.Tool(
            name="getJobStatus",
            description=(
                "<use_case>Check the current status of a running optimization job (single poll).</use_case>"
                "<behavior>Returns immediately with current status: 'Optimizing...' (still running) or "
                "'optimal'/'not optimal' (complete). Does not wait or retry.</behavior>"
                "<important_notes>This is a low-level polling tool. For automatic completion, use waitForJob or submitAndWait instead. "
                "Jobs typically take 30-120 seconds total.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_uuid": {
                        "type": "string",
                        "description": "The UUID of the optimization job",
                    }
                },
                "required": ["run_uuid"],
            },
        ),
        types.Tool(
            name="getJobResults",
            description=(
                "<use_case>Retrieve complete results from a finished optimization job with formatted preview.</use_case>"
                "<behavior>Returns full results including system sizes, financials, and hourly timeseries data. "
                "Large arrays (>10 items) are automatically truncated showing length, first 10 items, sum, and mean.</behavior>"
                "<important_notes>Use getResultsSummary, getFinancialSummary, or getSystemSummary for "
                "token-efficient formatted analysis instead of full results.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_uuid": {
                        "type": "string",
                        "description": "The UUID of the completed optimization job",
                    }
                },
                "required": ["run_uuid"],
            },
        ),
        types.Tool(
            name="getResultsSummary",
            description=(
                "<use_case>Get a concise, user-friendly summary of optimization results. Perfect for presenting recommendations.</use_case>"
                "<aliases>Also known as: summarize results, show recommendations, what did the optimization find</aliases>"
                "<behavior>Returns key metrics in markdown format: system sizes (PV kW, battery kW/kWh), "
                "financial analysis (NPV, payback, IRR), and utility bill savings.</behavior>"
                "<important_notes>This is the RECOMMENDED tool for presenting results to users. "
                "Much more token-efficient than getJobResults.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_uuid": {
                        "type": "string",
                        "description": "The UUID of the completed optimization job",
                    }
                },
                "required": ["run_uuid"],
            },
        ),
        types.Tool(
            name="getFinancialSummary",
            description=(
                "<use_case>Get detailed financial analysis for investment decision-making.</use_case>"
                "<behavior>Returns comprehensive financial metrics in markdown table format: NPV, LCC, payback period, "
                "IRR, initial capital costs, O&M costs, and incentives.</behavior>"
                "<important_notes>Use when user asks specifically about economics, ROI, payback, or financial viability.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_uuid": {
                        "type": "string",
                        "description": "The UUID of the completed optimization job",
                    }
                },
                "required": ["run_uuid"],
            },
        ),
        types.Tool(
            name="getSystemSummary",
            description=(
                "<use_case>Get detailed technical specifications for recommended systems.</use_case>"
                "<behavior>Returns technology-specific metrics in markdown tables: system capacities, "
                "energy production, capacity factors, O&M costs for each technology (PV, battery, etc.).</behavior>"
                "<important_notes>Use when user asks about technical details, system specifications, or performance characteristics.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_uuid": {
                        "type": "string",
                        "description": "The UUID of the completed optimization job",
                    }
                },
                "required": ["run_uuid"],
            },
        ),
        types.Tool(
            name="getMinimalScenario",
            description=(
                "<use_case>Show the 3 required inputs and how to add technologies.</use_case>"
                "<behavior>Returns base structure (Site, ElectricLoad, ElectricTariff) and explains "
                "how to add technology objects like PV: {}, ElectricStorage: {}, etc.</behavior>"
                "<important_notes>Use when user asks 'how to structure' or 'what's required'. "
                "Teaches that empty {} enables technology evaluation.</important_notes>"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="getExampleScenario",
            description=(
                "<use_case>Show complete working examples for common scenarios.</use_case>"
                "<behavior>Returns 3 examples: solar only, solar+battery, and with constraints.</behavior>"
                "<important_notes>Use when user asks for examples or wants to see different configurations.</important_notes>"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool execution."""
    
    if name == "submitAndWait":
        return await submit_and_wait(
            arguments.get("scenario"),
            arguments.get("max_wait_seconds", 300)
        )
    
    elif name == "waitForJob":
        return await wait_for_job(
            arguments.get("run_uuid"),
            arguments.get("max_wait_seconds", 300)
        )
    
    elif name == "submitReoptJob":
        return await submit_reopt_job(arguments.get("scenario"))
    
    elif name == "getJobStatus":
        return await get_job_status(arguments.get("run_uuid"))
    
    elif name == "getJobResults":
        return await get_job_results(arguments.get("run_uuid"))
    
    elif name == "getResultsSummary":
        return await get_results_summary(arguments.get("run_uuid"))
    
    elif name == "getFinancialSummary":
        return await get_financial_summary(arguments.get("run_uuid"))
    
    elif name == "getSystemSummary":
        return await get_system_summary(arguments.get("run_uuid"))
    
    elif name == "getMinimalScenario":
        return await get_minimal_scenario()
    
    elif name == "getExampleScenario":
        return await get_example_scenario()
    
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def submit_and_wait(scenario: dict, max_wait_seconds: int = 300) -> list[types.TextContent]:
    """Submit optimization job and wait for completion."""
    try:
        # Submit job
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{REOPT_API_BASE_URL}/job",
                json=scenario,
                params={"api_key": NREL_API_KEY}
            )
            response.raise_for_status()
            run_uuid = response.json().get("run_uuid")
        
        # Poll until complete
        poll_result = await poll_until_complete(run_uuid, max_wait_seconds)
        
        if poll_result["status"] == "complete":
            outputs = poll_result["result"].get("outputs", {})
            
            # Build concise summary
            summary_parts = [
                f"✓ Optimization completed successfully in {poll_result['elapsed_seconds']} seconds",
                f"  Run UUID: {run_uuid}",
                f"  Status: {poll_result['job_status']}",
                ""
            ]
            
            # System summary
            if "PV" in outputs and outputs["PV"].get("size_kw", 0) > 0:
                summary_parts.append(f"  Solar PV: {outputs['PV']['size_kw']:.1f} kW")
            
            if "ElectricStorage" in outputs and outputs["ElectricStorage"].get("size_kw", 0) > 0:
                storage = outputs["ElectricStorage"]
                summary_parts.append(f"  Battery: {storage['size_kw']:.1f} kW / {storage['size_kwh']:.1f} kWh")
            
            if "Financial" in outputs:
                summary_parts.append(f"  NPV: ${outputs['Financial']['npv']:,.0f}")
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "run_uuid": run_uuid,
                    "elapsed_seconds": poll_result["elapsed_seconds"],
                    "summary": "\n".join(summary_parts),
                    "outputs": outputs,
                    "messages": poll_result["result"].get("messages", {})
                }, indent=2)
            )]
        
        return [types.TextContent(type="text", text=json.dumps(poll_result, indent=2))]
            
    except httpx.HTTPStatusError as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": f"HTTP {e.response.status_code}",
                "detail": e.response.text
            }, indent=2)
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"status": "error", "error": str(e)}, indent=2)
        )]


async def wait_for_job(run_uuid: str, max_wait_seconds: int = 300) -> list[types.TextContent]:
    """Wait for previously submitted job to complete."""
    try:
        poll_result = await poll_until_complete(run_uuid, max_wait_seconds)
        
        if poll_result["status"] == "complete":
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "run_uuid": run_uuid,
                    "elapsed_seconds": poll_result["elapsed_seconds"],
                    "poll_count": poll_result["poll_count"],
                    "job_status": poll_result["job_status"],
                    "message": f"Job completed after {poll_result['elapsed_seconds']}s ({poll_result['poll_count']} polls)",
                    "outputs": poll_result["result"].get("outputs", {}),
                    "messages": poll_result["result"].get("messages", {})
                }, indent=2)
            )]
        
        return [types.TextContent(type="text", text=json.dumps(poll_result, indent=2))]
            
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"status": "error", "error": str(e), "run_uuid": run_uuid}, indent=2)
        )]


async def submit_reopt_job(scenario: dict) -> list[types.TextContent]:
    """Submit optimization job without waiting."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{REOPT_API_BASE_URL}/job",
                json=scenario,
                params={"api_key": NREL_API_KEY}
            )
            response.raise_for_status()
            run_uuid = response.json().get("run_uuid")
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "run_uuid": run_uuid,
                    "message": f"Job submitted. Use waitForJob('{run_uuid}') to retrieve results.",
                    "tip": "Jobs typically complete in 30-120 seconds."
                }, indent=2)
            )]
            
    except httpx.HTTPStatusError as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"status": "error", "error": f"HTTP {e.response.status_code}", "detail": e.response.text}, indent=2)
        )]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"status": "error", "error": str(e)}, indent=2))]


async def get_job_status(run_uuid: str) -> list[types.TextContent]:
    """Check job status (single poll)."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{REOPT_API_BASE_URL}/job/{run_uuid}/results",
                params={"api_key": NREL_API_KEY}
            )
            response.raise_for_status()
            result = response.json()
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "run_uuid": run_uuid,
                    "job_status": result.get("status", "Unknown"),
                    "messages": result.get("messages", {}),
                    "note": "Complete if status is 'optimal' or 'not optimal'."
                }, indent=2)
            )]
            
    except httpx.HTTPStatusError as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"status": "error", "error": f"HTTP {e.response.status_code}", "detail": e.response.text}, indent=2)
        )]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"status": "error", "error": str(e)}, indent=2))]


async def get_job_results(run_uuid: str) -> list[types.TextContent]:
    """Retrieve full results from completed job."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{REOPT_API_BASE_URL}/job/{run_uuid}/results",
                params={"api_key": NREL_API_KEY}
            )
            response.raise_for_status()
            result = response.json()
            
            # Truncate 8760+ hour timeseries to save memory
            result = truncate_large_arrays(result)
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "run_uuid": run_uuid,
                    "results": result,
                    "note": "Timeseries arrays (8760+ hours) show only statistics. Use getResultsSummary for formatted analysis."
                }, indent=2)
            )]
            
    except httpx.HTTPStatusError as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"status": "error", "error": f"HTTP {e.response.status_code}", "detail": e.response.text}, indent=2)
        )]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"status": "error", "error": str(e)}, indent=2))]


# Helper function for API calls
async def get_job_data(run_uuid: str) -> dict:
    """Fetch job results from REopt API.
    
    Args:
        run_uuid: Job UUID
        
    Returns:
        dict: Job results from API
        
    Raises:
        httpx.HTTPStatusError: If API request fails
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{REOPT_API_BASE_URL}/job/{run_uuid}/results",
            params={"api_key": NREL_API_KEY}
        )
        response.raise_for_status()
        return response.json()


async def get_results_summary(run_uuid: str) -> list[types.TextContent]:
    """Get concise summary of optimization results."""
    try:
        result = await get_job_data(run_uuid)
        outputs = result.get("outputs", {})
        
        summary = "# REopt Optimization Results Summary\n\n## System Recommendations"
        
        # Solar PV
        if "PV" in outputs and outputs["PV"].get("size_kw", 0) > 0:
            pv = outputs["PV"]
            summary += f"""\n\n### Solar PV
- **Recommended Size**: {pv.get('size_kw', 0):.1f} kW
- **Year 1 Production**: {pv.get('annual_energy_produced_kwh', 0):,.0f} kWh
- **Annual O&M Cost**: ${pv.get('annual_om_cost_before_tax', 0):,.0f}
- **Federal ITC**: {pv.get('federal_itc_fraction', 0)*100:.0f}%"""
        
        # Battery Storage
        if "ElectricStorage" in outputs and outputs["ElectricStorage"].get("size_kw", 0) > 0:
            storage = outputs["ElectricStorage"]
            summary += f"""\n\n### Battery Storage
- **Power Capacity**: {storage.get('size_kw', 0):.1f} kW
- **Energy Capacity**: {storage.get('size_kwh', 0):.1f} kWh
- **Annual O&M Cost**: ${storage.get('annual_om_cost_before_tax', 0):,.0f}"""
        
        # Financial Summary
        if "Financial" in outputs:
            fin = outputs["Financial"]
            payback = f"{fin.get('simple_payback_years', 0):.1f}" if fin.get('simple_payback_years') else 'N/A'
            irr = f"{fin.get('internal_rate_of_return', 0)*100:.1f}%" if fin.get('internal_rate_of_return') else 'N/A'
            summary += f"""\n\n## Financial Analysis
- **Net Present Value**: ${fin.get('npv', 0):,.0f}
- **Lifecycle Cost**: ${fin.get('lcc', 0):,.0f}
- **Simple Payback**: {payback} years
- **Internal Rate of Return**: {irr}"""
        
        # Utility Savings
        if "ElectricUtility" in outputs:
            util = outputs["ElectricUtility"]
            baseline = util.get("year_one_bill_before_tax_bau", 0)
            optimized = util.get("year_one_bill_before_tax", 0)
            summary += f"""\n\n## Year 1 Utility Bill Analysis
- **Baseline Bill**: ${baseline:,.0f}
- **With System**: ${optimized:,.0f}
- **Annual Savings**: ${baseline - optimized:,.0f}"""
        
        return [types.TextContent(type="text", text=summary)]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def get_financial_summary(run_uuid: str) -> list[types.TextContent]:
    """Get detailed financial analysis."""
    try:
        result = await get_job_data(run_uuid)
        outputs = result.get("outputs", {})
        
        if "Financial" not in outputs:
            return [types.TextContent(type="text", text="No financial results available.")]
        
        fin = outputs["Financial"]
        
        table = "# Financial Analysis\n\n| Metric | Value |\n|--------|-------|\n"
        table += f"| Net Present Value (NPV) | ${fin.get('npv', 0):,.0f} |\n"
        table += f"| Lifecycle Cost (LCC) | ${fin.get('lcc', 0):,.0f} |\n"
        table += f"| Initial Capital Cost | ${fin.get('initial_capital_costs', 0):,.0f} |\n"
        table += f"| Initial Capital Cost (after incentives) | ${fin.get('initial_capital_costs_after_incentives', 0):,.0f} |\n"
        
        if fin.get('simple_payback_years'):
            table += f"| Simple Payback Period | {fin.get('simple_payback_years', 0):.1f} years |\n"
        
        if fin.get('internal_rate_of_return'):
            table += f"| Internal Rate of Return | {fin.get('internal_rate_of_return', 0)*100:.1f}% |\n"
        
        table += f"| Lifecycle O&M Costs | ${fin.get('om_and_replacement_present_cost_after_tax', 0):,.0f} |\n"
        
        return [types.TextContent(type="text", text=table)]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def get_system_summary(run_uuid: str) -> list[types.TextContent]:
    """Get technology system specifications."""
    try:
        result = await get_job_data(run_uuid)
        outputs = result.get("outputs", {})
        
        summary = "# System Technology Summary\n\n"
        
        # Solar PV
        if "PV" in outputs and outputs["PV"].get("size_kw", 0) > 0:
            pv = outputs["PV"]
            cf = pv.get('average_annual_energy_produced_kwh', 0) / (pv.get('size_kw', 1) * 8760) * 100 if pv.get('size_kw', 0) > 0 else 0
            summary += """## Solar PV System

| Metric | Value |
|--------|-------|
"""
            summary += f"| System Size | {pv.get('size_kw', 0):.2f} kW |\n"
            summary += f"| Year 1 Production | {pv.get('annual_energy_produced_kwh', 0):,.0f} kWh |\n"
            summary += f"| Capacity Factor | {cf:.1f}% |\n"
            summary += f"| Annual O&M Cost | ${pv.get('annual_om_cost_before_tax', 0):,.0f} |\n"
            summary += f"| Lifecycle O&M Cost | ${pv.get('lifecycle_om_cost_after_tax', 0):,.0f} |\n\n"
        
        # Battery Storage
        if "ElectricStorage" in outputs and outputs["ElectricStorage"].get("size_kw", 0) > 0:
            storage = outputs["ElectricStorage"]
            duration = storage.get('size_kwh', 0) / storage.get('size_kw', 1) if storage.get('size_kw', 0) > 0 else 0
            summary += """## Battery Energy Storage

| Metric | Value |
|--------|-------|
"""
            summary += f"| Power Capacity | {storage.get('size_kw', 0):.2f} kW |\n"
            summary += f"| Energy Capacity | {storage.get('size_kwh', 0):.2f} kWh |\n"
            summary += f"| Duration | {duration:.1f} hours |\n"
            summary += f"| Annual O&M Cost | ${storage.get('annual_om_cost_before_tax', 0):,.0f} |\n\n"
        
        # No systems recommended
        if "PV" not in outputs and "ElectricStorage" not in outputs:
            summary += """No distributed energy systems recommended.

This typically means the economics don't favor installing solar or storage
under current assumptions (tariff, load, costs).

Consider:
- Verifying utility rate accuracy (use URDB labels)
- Reviewing technology cost assumptions
- Adjusting financial parameters
- Exploring different technologies
"""
        
        return [types.TextContent(type="text", text=summary)]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def get_minimal_scenario() -> list[types.TextContent]:
    """Return a minimal REopt scenario showing only the 3 required inputs."""
    minimal_base = {
        "Site": {
            "latitude": 39.7407,
            "longitude": -104.9890
        },
        "ElectricLoad": {
            "doe_reference_name": "MediumOffice",
            "annual_kwh": 500000
        },
        "ElectricTariff": {
            "urdb_label": ""
        }
    }
    
    explanation = """## Minimal REopt Scenario Structure

### The 3 Required Inputs:

```json
{
  "Site": {
    "latitude": 39.7407,
    "longitude": -104.9890
  },
  "ElectricLoad": {
    "doe_reference_name": "MediumOffice",
    "annual_kwh": 500000
  },
  "ElectricTariff": {
    "urdb_label": ""
  }
}
```

**CRITICAL**: ElectricLoad needs BOTH fields:
- `doe_reference_name`: Provides hourly load pattern/shape
- `annual_kwh`: Scales the pattern to your consumption
- Together they create the 8760-hour load profile

**That's it for the base!** Now add technologies you want to evaluate:

### Adding Technologies to Evaluate:

To evaluate solar PV:
```json
{
  ...(3 required inputs),
  "PV": {}
}
```

To evaluate solar + battery:
```json
{
  ...(3 required inputs),
  "PV": {},
  "ElectricStorage": {}
}
```

To evaluate solar + battery + wind:
```json
{
  ...(3 required inputs),
  "PV": {},
  "ElectricStorage": {},
  "Wind": {}
}
```

### Key Concept:

✅ Empty object `{}` = "Evaluate this technology using default assumptions"
❌ No object = "Don't consider this technology at all"

### Available Technologies:

- `"PV": {}` - Solar photovoltaic
- `"ElectricStorage": {}` - Battery storage
- `"Wind": {}` - Wind turbines
- `"Generator": {}` - Backup generator
- `"CHP": {}` - Combined heat & power

### When to Add Constraints:

Only add parameters if you have specific limits:
```json
"PV": {
  "max_kw": 500  // Only if limited by roof space or budget
}
```

Otherwise, use empty `{}` to let REopt find the optimal size!

### Alternative for ElectricLoad:

Use DOE reference building instead of annual_kwh:
```json
"ElectricLoad": {
  "doe_reference_name": "MediumOffice"
}
```

Types: MediumOffice, RetailStore, Hospital, LargeHotel, Warehouse, School, etc."""
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "base_structure": minimal_base,
            "description": explanation
        }, indent=2)
    )]


async def get_example_scenario() -> list[types.TextContent]:
    """Return example scenarios showing different use cases."""
    
    examples = {
        "solar_only": {
            "Site": {"latitude": 39.7407, "longitude": -104.9890},
            "ElectricLoad": {"annual_kwh": 500000},
            "ElectricTariff": {"urdb_label": ""},
            "PV": {}
        },
        "solar_and_battery": {
            "Site": {"latitude": 39.7407, "longitude": -104.9890},
            "ElectricLoad": {"doe_reference_name": "MediumOffice"},
            "ElectricTariff": {"urdb_label": ""},
            "PV": {},
            "ElectricStorage": {}
        },
        "with_constraints": {
            "Site": {"latitude": 39.7407, "longitude": -104.9890},
            "ElectricLoad": {"annual_kwh": 1000000},
            "ElectricTariff": {"urdb_label": ""},
            "PV": {"max_kw": 500},
            "ElectricStorage": {"max_kw": 250, "max_kwh": 1000}
        }
    }
    
    explanation = """## REopt Scenario Examples

### Example 1: Solar Only
```json
{
  "Site": {"latitude": 39.7407, "longitude": -104.9890},
  "ElectricLoad": {"doe_reference_name": "MediumOffice", "annual_kwh": 500000},
  "ElectricTariff": {"urdb_label": ""},
  "PV": {}
}
```
Evaluates solar PV with no constraints - REopt determines optimal size.

### Example 2: Solar + Battery
```json
{
  "Site": {"latitude": 39.7407, "longitude": -104.9890},
  "ElectricLoad": {"doe_reference_name": "RetailStore", "annual_kwh": 800000},
  "ElectricTariff": {"urdb_label": ""},
  "PV": {},
  "ElectricStorage": {}
}
```
Evaluates solar + battery with no constraints.

### Example 3: With Space/Budget Constraints
```json
{
  "Site": {"latitude": 39.7407, "longitude": -104.9890},
  "ElectricLoad": {"doe_reference_name": "LargeOffice", "annual_kwh": 1000000},
  "ElectricTariff": {"urdb_label": ""},
  "PV": {"max_kw": 500},
  "ElectricStorage": {"max_kw": 250, "max_kwh": 1000}
}
```
Only use constraints when you have actual limitations!

### Building Your Scenario:

1. Start with 3 required inputs
2. Add empty `{}` for each technology you want to evaluate
3. Only add constraints if you have specific limits
4. Submit and let REopt optimize!"""
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "examples": examples,
            "description": explanation
        }, indent=2)
    )]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="reopt-mcp",
            server_version="0.1.0",
            capabilities=app.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
        
        # Add server instructions if supported
        if hasattr(init_options, 'instructions'):
            init_options.instructions = DEFAULT_INSTRUCTIONS
        
        await app.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())

