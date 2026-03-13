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
You help users run REopt energy optimizations.

## ⚠️ CRITICAL: ASK BEFORE SUBMITTING ⚠️
NEVER call submitAndWait with made-up values. If you don't have exact information, ASK the user.

## Required Before Submission

✓ Location: latitude & longitude (look up if user gives city/address)
✓ Building type: valid doe_reference_name from approved list
✓ Annual consumption: exact annual_kwh number from user
✓ Utility rate: MUST ask about utility company, then either:
  - Look up correct URDB label for their specific utility, OR
  - Ask for blended rates ($/kWh energy charge, $/kW demand charge) to build custom tariff
  - NEVER use example/default URDB labels like "" without verification
✓ Technologies: ONLY what user explicitly requested

## Scenario Structure

Every scenario needs 3 inputs + requested technologies:

```json
{
  "Site": {"latitude": 30.27, "longitude": -97.74},
  "ElectricLoad": {"doe_reference_name": "RetailStore", "annual_kwh": 200000},
  "ElectricTariff": {"urdb_label": "REGION_SPECIFIC_LABEL"},
  "PV": {},
  "ElectricStorage": {}
}
```

### Site
- Include ONLY: latitude, longitude
- NEVER add unless user specifies these constraints: roof_squarefeet, land_acres, load_profile

### ElectricLoad (BOTH required)
- `doe_reference_name` - building type from list below
- `annual_kwh` - user's consumption number

**ONLY Valid doe_reference_name**:
FastFoodRest,FullServiceRest,Hospital,LargeHotel,LargeOffice,MediumOffice,MidriseApartment,Outpatient,PrimarySchool,RetailStore,SecondarySchool,SmallHotel,SmallOffice,StripMall,Supermarket,Warehouse,FlatLoad,FlatLoad245,FlatLoad167,FlatLoad165,FlatLoad87,FlatLoad85

### ElectricTariff
**Option 1: URDB Label (Preferred)**
- ASK user: "What utility company provides your electricity?"
- Search NREL URDB database or ask user to look up their URDB label
- Each utility has its own unique label - NEVER reuse across utilities
- Example: Xcel Energy in Colorado might be "" but verify!
- Common utilities: Xcel Energy, ComEd, PG&E, Southern California Edison, Duke Energy, etc.

**Option 2: Custom Rates (If URDB not available)**
If you can't find URDB label, ask user:
- "What's your average electricity cost per kWh?"
- "Do you have demand charges? If so, what's the $/kW rate?"
- Build custom tariff:
  ```json
  "ElectricTariff": {
    "blended_annual_rates_us_dollars_per_kwh": 0.12,
    "blended_annual_demand_charges_us_dollars_per_kw": 15.0
  }
  ```

### Technologies
Add `{}` for ONLY what user requests:
- "solar" → `"PV": {}`
- "battery" → `"ElectricStorage": {}`
- "solar and battery" → both
- NEVER add unrequested technologies

## Workflow

1. User: "retail store in Austin" → ASK: "What's the annual kWh consumption?"
2. User: "500k kWh" → ASK: "What's your utility company?"
3. Look up URDB label for that utility OR ask for blended rates
4. Have all info → Build with exact values, submit via submitAndWait
5. Missing info → ASK, don't guess

## Examples

❌ User: "retail store in Austin"
   [submits with guessed annual_kwh, random URDB label, extra fields]

✅ User: "retail store in Austin"  
   You: "What's the annual kWh consumption?"
   User: "200,000"
   You: "What utility company provides your electricity?"
   User: "Austin Energy"
   [Look up Austin Energy URDB label OR ask for blended rates]
   [submits: Austin coords, RetailStore, 200000, correct URDB/rates, PV]

❌ User: "analyze solar in Denver"
   [uses default/example URDB label "" without asking about utility]

✅ User: "analyze solar in Denver"
   You: "What type of building?"
   You: "What's your annual consumption?"
   You: "What utility company serves your location?"
   User: "Xcel Energy"
   [Look up Xcel Energy Colorado URDB label - may be "" but VERIFY]
   [adds ONLY PV]

❌ User: "analyze solar"
   [adds PV + ElectricStorage + Generator without asking]

✅ User: "analyze solar"
   [adds ONLY PV since only solar was mentioned]

For technical support: https://github.com/NREL/REopt_API
✅ User: "retail store in Austin"  
   You: "What's the annual kWh consumption?"
   User: "200,000"
   [submits: Austin coords, RetailStore, 200000, TX URDB, PV + ElectricStorage]

❌ User: "analyze solar"
   [adds PV + ElectricStorage]

✅ User: "analyze solar"
   [adds ONLY PV]

For technical support: https://github.com/NREL/REopt_API
"""


# Initialize MCP server
app = Server("reopt-mcp")


# Valid building types for validation
VALID_DOE_REFERENCE_NAMES = {
    "FastFoodRest", "FullServiceRest", "Hospital", "LargeHotel", "LargeOffice",
    "MediumOffice", "MidriseApartment", "Outpatient", "PrimarySchool", "RetailStore",
    "SecondarySchool", "SmallHotel", "SmallOffice", "StripMall", "Supermarket",
    "Warehouse", "FlatLoad", "FlatLoad245", "FlatLoad167", "FlatLoad165", "FlatLoad87", "FlatLoad85"
}

# Invalid field names that should never appear
INVALID_SITE_FIELDS = {"address", "city", "state", "zip", "country"}


def validate_scenario(scenario: dict) -> tuple[bool, list[str]]:
    """Validate that scenario has all required fields and no invalid assumptions.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for Site
    if "Site" not in scenario:
        errors.append("Missing 'Site' object")
    else:
        site = scenario["Site"]
        
        # Check for invalid fields
        invalid_fields = set(site.keys()) & INVALID_SITE_FIELDS
        if invalid_fields:
            errors.append(f"Site contains invalid fields: {invalid_fields}. Only use latitude/longitude.")
        
        # Check for required coordinates
        if "latitude" not in site:
            errors.append("Site missing 'latitude'")
        if "longitude" not in site:
            errors.append("Site missing 'longitude'")
    
    # Check for ElectricLoad
    if "ElectricLoad" not in scenario:
        errors.append("Missing 'ElectricLoad' object")
    else:
        load = scenario["ElectricLoad"]
        if "doe_reference_name" not in load:
            errors.append("ElectricLoad missing 'doe_reference_name'")
        elif load["doe_reference_name"] not in VALID_DOE_REFERENCE_NAMES:
            errors.append(f"Invalid doe_reference_name: '{load['doe_reference_name']}'. Must be one of: {', '.join(sorted(VALID_DOE_REFERENCE_NAMES))}")
        
        if "annual_kwh" not in load:
            errors.append("ElectricLoad missing 'annual_kwh'")
        elif not isinstance(load["annual_kwh"], (int, float)) or load["annual_kwh"] <= 0:
            errors.append("ElectricLoad 'annual_kwh' must be a positive number")
    
    # Check for ElectricTariff
    if "ElectricTariff" not in scenario:
        errors.append("Missing 'ElectricTariff' object")
    else:
        tariff = scenario["ElectricTariff"]
        has_urdb = "urdb_label" in tariff
        has_blended = "blended_annual_energy_rate" in tariff or "blended_annual_rates_us_dollars_per_kwh" in tariff
        has_monthly = "monthly_energy_rates" in tariff
        has_tou = "tou_energy_rates_per_kwh" in tariff
        has_urdb_name = "urdb_utility_name" in tariff and "urdb_rate_name" in tariff
        if not has_urdb and not has_blended and not has_monthly and not has_tou and not has_urdb_name:
            errors.append("ElectricTariff missing rate info. Provide 'urdb_label', 'blended_annual_energy_rate', or another valid rate input.")
    
    return (len(errors) == 0, errors)


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
                "<use_case>Submit REopt optimization and wait for results. PRIMARY tool for running optimizations.</use_case>"
                "<behavior>Builds scenario from user-provided information, submits to NREL API, polls automatically (30-120s), returns results.</behavior>"
                "<critical_validation>MUST have ALL of these BEFORE calling this tool:\n"
                "1. EXACT latitude/longitude (not city name - look up coordinates first)\n"
                "2. EXACT annual_kwh from user (NEVER estimate or make up - ASK if missing)\n"
                "3. VALID doe_reference_name from approved list (NEVER guess - ASK user for building type)\n"
                "4. CORRECT utility rate - MUST ASK 'What utility company?' then:\n"
                "   a) Look up specific URDB label for that utility (preferred), OR\n"
                "   b) Ask for blended rates ($/kWh and $/kW) if URDB not available\n"
                "   NEVER use example URDB labels without verification!\n"
                "5. Technologies: ONLY {} for what user explicitly mentioned (solar=PV, battery=ElectricStorage)\n\n"
                "FORBIDDEN: address field (invalid), made-up annual_kwh, guessed URDB labels, unrequested technologies, assumed constraints.\n\n"
                "IF MISSING ANY INFO: STOP and ASK user. Do NOT proceed with assumptions.</critical_validation>"
                "<workflow>When user mentions location but missing details: (1) Ask for building type, (2) Ask for annual kWh, (3) Ask 'What utility company provides your electricity?', (4) Look up correct URDB label for that specific utility OR ask for blended rates if URDB unavailable, (5) Look up coordinates, (6) THEN call submitAndWait with exact values.</workflow>"
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
            name="validateScenario",
            description=(
                "<use_case>Check if a scenario has all required information before submission.</use_case>"
                "<behavior>Validates scenario structure and returns detailed errors for any missing/invalid fields. "
                "Use this BEFORE calling submitAndWait to catch issues early.</behavior>"
                "<important_notes>This helps identify what information is still needed from the user. "
                "Returns specific validation errors that should be addressed by asking the user.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "object",
                        "description": "The scenario object to validate",
                    }
                },
                "required": ["scenario"],
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
    
    elif name == "validateScenario":
        return await validate_scenario_tool(arguments.get("scenario"))
    
    elif name == "getMinimalScenario":
        return await get_minimal_scenario()
    
    elif name == "getExampleScenario":
        return await get_example_scenario()
    
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def validate_scenario_tool(scenario: dict) -> list[types.TextContent]:
    """Validate scenario and return detailed feedback."""
    is_valid, errors = validate_scenario(scenario)
    
    if is_valid:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "valid",
                "message": "✓ Scenario is valid and ready for submission",
                "scenario": scenario
            }, indent=2)
        )]
    else:
        guidance = []
        for err in errors:
            if "latitude" in err or "longitude" in err:
                guidance.append("📍 Ask user for the city/address, then look up coordinates")
            elif "doe_reference_name" in err:
                guidance.append("🏢 Ask user for building type (office, retail, warehouse, etc.)")
            elif "annual_kwh" in err:
                guidance.append("⚡ Ask user for annual electricity consumption in kWh")
            elif "urdb_label" in err or "ElectricTariff missing rate" in err:
                guidance.append("💵 Look up correct URDB label for the user's specific utility/region, or use blended_annual_energy_rate")
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "invalid",
                "valid": False,
                "errors": errors,
                "guidance": list(set(guidance)),  # Remove duplicates
                "message": "Scenario needs more information before submission"
            }, indent=2)
        )]


async def submit_and_wait(scenario: dict, max_wait_seconds: int = 300) -> list[types.TextContent]:
    """Submit optimization job and wait for completion."""
    try:
        # VALIDATE SCENARIO FIRST
        is_valid, errors = validate_scenario(scenario)
        if not is_valid:
            error_msg = "❌ Cannot submit - scenario is missing required information:\n\n"
            for i, err in enumerate(errors, 1):
                error_msg += f"{i}. {err}\n"
            error_msg += "\n⚠️ Please provide the missing information before submitting."
            error_msg += "\n\nUse getMinimalScenario or getExampleScenario to see proper structure."
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "validation_error",
                    "errors": errors,
                    "message": error_msg,
                    "scenario_received": scenario
                }, indent=2)
            )]
        
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

