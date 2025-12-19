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
You are provided with MCP tools that integrate with the REopt API, NREL's energy optimization platform for distributed energy resources.

REopt helps analyze and optimize:
- Solar PV systems
- Battery energy storage
- Combined heat and power (CHP)
- Electric vehicle charging
- Wind turbines
- Other distributed energy resources

The optimization considers:
- Utility tariffs and rate structures
- Capital and operating costs
- Financial incentives (federal ITC, depreciation, etc.)
- Site load profiles
- Technology performance characteristics

## Core Workflow:

1. **Define Scenario**: Create a scenario object with Site, ElectricLoad, ElectricTariff, and technology parameters
2. **Submit & Wait**: Use `submitAndWait` (RECOMMENDED) for automatic job submission and polling
3. **Retrieve Results**: Get formatted summaries with financial and system sizing recommendations

## Best Practices:

1. **Always use `submitAndWait`** instead of manual submission + polling. It handles exponential backoff automatically.
2. **Jobs take 30-120 seconds typically**. The tool will wait automatically.
3. **Start with `getExampleScenario`** if user is unfamiliar with REopt structure.
4. **Use summary tools** (`getResultsSummary`, `getFinancialSummary`, `getSystemSummary`) for concise outputs rather than full results.
5. **Provide location context**: REopt requires latitude/longitude or you can use DOE reference building names.
6. **Tariff selection matters**: Use URDB labels for accurate utility rates, or provide custom tariff structures.

## Important Notes:

- All optimization jobs run asynchronously on NREL servers
- Results include both optimal system sizes and financial analysis (NPV, payback, IRR)
- The API requires an NREL_API_KEY environment variable to be configured
- Large result arrays are automatically truncated to save tokens - use summary tools for key metrics

## Common Use Cases:

- "Should I install solar at my facility?" → Use submitAndWait with site location and load profile
- "What's the payback period?" → Check Financial section in results (simple_payback_years)
- "How much battery storage do I need?" → ElectricStorage results show optimal kW/kWh sizing
- "What are my utility savings?" → ElectricUtility section compares baseline vs optimized bills

For technical support or API details, visit: https://github.com/NREL/REopt_API
"""

# Initialize MCP server
app = Server("reopt-mcp")


# Helper function to truncate large arrays
def truncate_large_arrays(data: Any, max_items: int = 10) -> Any:
    """Recursively truncate arrays longer than max_items to save space."""
    if isinstance(data, dict):
        return {k: truncate_large_arrays(v, max_items) for k, v in data.items()}
    elif isinstance(data, list):
        if len(data) > max_items:
            return {
                "_truncated": True,
                "_length": len(data),
                "_first_items": data[:max_items],
                "_sum": sum(data) if all(isinstance(x, (int, float)) for x in data) else None,
                "_mean": sum(data) / len(data) if len(data) > 0 and all(isinstance(x, (int, float)) for x in data) else None
            }
        return [truncate_large_arrays(item, max_items) for item in data]
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
                "<use_case>Submit a REopt optimization job and automatically wait for completion. "
                "This is the RECOMMENDED approach for all optimization requests.</use_case>"
                "<aliases>Also known as: submit optimization, run optimization, optimize system, analyze scenario</aliases>"
                "<behavior>Submits the job to NREL's API and polls automatically with exponential backoff (3-15s intervals). "
                "Jobs typically complete in 30-120 seconds. Returns complete results when ready.</behavior>"
                "<important_notes>Use this instead of submitReoptJob + multiple getJobStatus calls. "
                "Provides better UX by handling all polling logic automatically.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "object",
                        "description": "The REopt scenario definition with Site, ElectricTariff, PV, ElectricStorage, and other parameters",
                    },
                    "max_wait_seconds": {
                        "type": "integer",
                        "description": "Maximum time to wait for completion (default 300 seconds / 5 minutes)",
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
            name="getExampleScenario",
            description=(
                "<use_case>Get a template showing the required structure for a REopt scenario definition.</use_case>"
                "<aliases>Also known as: show example, get template, scenario structure, how to format</aliases>"
                "<behavior>Returns a complete example scenario with Site, ElectricLoad, ElectricTariff, PV, "
                "and ElectricStorage parameters for a medium office building in Denver.</behavior>"
                "<important_notes>Use this when user is unfamiliar with REopt or asks how to structure their input. "
                "The example can be modified for their specific location and requirements.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
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
    
    elif name == "getExampleScenario":
        return await get_example_scenario()
    
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def submit_and_wait(scenario: dict, max_wait_seconds: int = 300) -> list[types.TextContent]:
    """Submit a job and automatically wait for completion with intelligent polling."""
    try:
        # First submit the job
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{REOPT_API_BASE_URL}/job"
            response = await client.post(
                url,
                json=scenario,
                params={"api_key": NREL_API_KEY}
            )
            response.raise_for_status()
            result = response.json()
            run_uuid = result.get("run_uuid")
        
        # Now poll until complete
        poll_result = await poll_until_complete(run_uuid, max_wait_seconds)
        
        if poll_result["status"] == "complete":
            # Extract outputs for summary
            outputs = poll_result["result"].get("outputs", {})
            
            # Build summary message
            summary_lines = [
                f"✓ Optimization completed successfully in {poll_result['elapsed_seconds']} seconds",
                f"  Run UUID: {run_uuid}",
                f"  Status: {poll_result['job_status']}",
                ""
            ]
            
            # Add PV summary if present
            if "PV" in outputs and outputs["PV"].get("size_kw", 0) > 0:
                pv = outputs["PV"]
                summary_lines.append(f"  Solar PV: {pv.get('size_kw', 0):.1f} kW")
            
            # Add battery summary if present
            if "ElectricStorage" in outputs and outputs["ElectricStorage"].get("size_kw", 0) > 0:
                storage = outputs["ElectricStorage"]
                summary_lines.append(f"  Battery: {storage.get('size_kw', 0):.1f} kW / {storage.get('size_kwh', 0):.1f} kWh")
            
            # Add financial summary
            if "Financial" in outputs:
                fin = outputs["Financial"]
                summary_lines.append(f"  NPV: ${fin.get('npv', 0):,.0f}")
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "run_uuid": run_uuid,
                    "elapsed_seconds": poll_result["elapsed_seconds"],
                    "summary": "\n".join(summary_lines),
                    "outputs": outputs,
                    "messages": poll_result["result"].get("messages", {})
                }, indent=2)
            )]
        else:
            # Timeout or error
            return [types.TextContent(
                type="text",
                text=json.dumps(poll_result, indent=2)
            )]
            
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
            text=json.dumps({
                "status": "error",
                "error": str(e)
            }, indent=2)
        )]


async def wait_for_job(run_uuid: str, max_wait_seconds: int = 300) -> list[types.TextContent]:
    """Wait for a previously submitted job to complete."""
    try:
        poll_result = await poll_until_complete(run_uuid, max_wait_seconds)
        
        if poll_result["status"] == "complete":
            outputs = poll_result["result"].get("outputs", {})
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "run_uuid": run_uuid,
                    "elapsed_seconds": poll_result["elapsed_seconds"],
                    "poll_count": poll_result["poll_count"],
                    "job_status": poll_result["job_status"],
                    "message": f"Job completed after {poll_result['elapsed_seconds']}s ({poll_result['poll_count']} polls)",
                    "outputs": outputs,
                    "messages": poll_result["result"].get("messages", {})
                }, indent=2)
            )]
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps(poll_result, indent=2)
            )]
            
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": str(e),
                "run_uuid": run_uuid
            }, indent=2)
        )]


async def submit_reopt_job(scenario: dict) -> list[types.TextContent]:
    """Submit an optimization job to REopt API."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{REOPT_API_BASE_URL}/job"
            
            response = await client.post(
                url,
                json=scenario,
                params={"api_key": NREL_API_KEY}
            )
            response.raise_for_status()
            
            result = response.json()
            run_uuid = result.get("run_uuid")
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "run_uuid": run_uuid,
                    "message": f"Job submitted successfully. Use run_uuid '{run_uuid}' to check status and retrieve results.",
                    "tip": "Jobs typically complete in 30-120 seconds. Use waitForJob for automatic polling."
                }, indent=2)
            )]
            
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": f"HTTP {e.response.status_code}",
                "detail": error_detail
            }, indent=2)
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": str(e)
            }, indent=2)
        )]


async def get_job_status(run_uuid: str) -> list[types.TextContent]:
    """Check the status of a REopt job by polling the results endpoint."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{REOPT_API_BASE_URL}/job/{run_uuid}/results"
            
            response = await client.get(
                url,
                params={"api_key": NREL_API_KEY}
            )
            response.raise_for_status()
            
            result = response.json()
            status = result.get("status", "Unknown")
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "run_uuid": run_uuid,
                    "job_status": status,
                    "messages": result.get("messages", {}),
                    "note": "Job is complete if status is 'optimal' or 'not optimal'. Otherwise it's still running."
                }, indent=2)
            )]
            
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
            text=json.dumps({
                "status": "error",
                "error": str(e)
            }, indent=2)
        )]


async def get_job_results(run_uuid: str) -> list[types.TextContent]:
    """Retrieve results from a completed REopt job with formatted summary and truncated arrays."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{REOPT_API_BASE_URL}/job/{run_uuid}/results"
            
            response = await client.get(
                url,
                params={"api_key": NREL_API_KEY}
            )
            response.raise_for_status()
            
            result = response.json()
            outputs = result.get("outputs", {})
            
            # Create a formatted summary
            summary = {
                "status": "success",
                "run_uuid": run_uuid,
                "summary": {}
            }
            
            # Extract PV results
            if "PV" in outputs:
                pv = outputs["PV"]
                summary["summary"]["solar_pv"] = {
                    "recommended_size_kw": round(pv.get("size_kw", 0), 2),
                    "year_1_energy_kwh": round(pv.get("annual_energy_produced_kwh", 0), 0),
                    "lifecycle_om_cost": round(pv.get("lifecycle_om_cost_after_tax", 0), 0),
                    "federal_itc_fraction": pv.get("federal_itc_fraction", 0)
                }
            
            # Extract Storage results
            if "ElectricStorage" in outputs:
                storage = outputs["ElectricStorage"]
                if storage.get("size_kw", 0) > 0:
                    summary["summary"]["battery_storage"] = {
                        "power_capacity_kw": round(storage.get("size_kw", 0), 2),
                        "energy_capacity_kwh": round(storage.get("size_kwh", 0), 2)
                    }
            
            # Extract Financial results
            if "Financial" in outputs:
                fin = outputs["Financial"]
                summary["summary"]["financial"] = {
                    "net_present_value_usd": round(fin.get("npv", 0), 0),
                    "lifecycle_cost_usd": round(fin.get("lcc", 0), 0),
                    "simple_payback_years": round(fin.get("simple_payback_years", 0), 1) if fin.get("simple_payback_years") else None,
                    "internal_rate_of_return_pct": round(fin.get("internal_rate_of_return", 0) * 100, 1) if fin.get("internal_rate_of_return") else None
                }
            
            # Extract utility bill savings
            if "ElectricUtility" in outputs:
                util = outputs["ElectricUtility"]
                summary["summary"]["utility_bills"] = {
                    "year_1_bill_with_system_usd": round(util.get("year_one_bill_before_tax", 0), 0),
                    "year_1_bill_baseline_usd": round(util.get("year_one_bill_before_tax_bau", 0), 0),
                    "year_1_savings_usd": round(util.get("year_one_bill_before_tax_bau", 0) - util.get("year_one_bill_before_tax", 0), 0)
                }
            
            # Truncate large arrays in full results to avoid overwhelming output
            truncated_result = truncate_large_arrays(result, max_items=10)
            summary["full_results_preview"] = truncated_result
            summary["note"] = "Large arrays (>10 items) are truncated. Arrays show: length, first 10 items, sum, and mean. Use getResultsSummary, getFinancialSummary, or getSystemSummary for formatted analysis."
            
            return [types.TextContent(
                type="text",
                text=json.dumps(summary, indent=2)
            )]
            
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
            text=json.dumps({
                "status": "error",
                "error": str(e)
            }, indent=2)
        )]


async def get_results_summary(run_uuid: str) -> list[types.TextContent]:
    """Get a concise summary of key optimization results."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{REOPT_API_BASE_URL}/job/{run_uuid}/results"
            response = await client.get(url, params={"api_key": NREL_API_KEY})
            response.raise_for_status()
            result = response.json()
            outputs = result.get("outputs", {})
            
            summary = f"""# REopt Optimization Results Summary

## System Recommendations"""
            
            # PV System
            if "PV" in outputs and outputs["PV"].get("size_kw", 0) > 0:
                pv = outputs["PV"]
                summary += f"""

### Solar PV
- **Recommended Size**: {pv.get('size_kw', 0):.1f} kW
- **Year 1 Production**: {pv.get('annual_energy_produced_kwh', 0):,.0f} kWh
- **Annual O&M Cost**: ${pv.get('annual_om_cost_before_tax', 0):,.0f}
- **Federal ITC**: {pv.get('federal_itc_fraction', 0)*100:.0f}%"""
            
            # Battery Storage
            if "ElectricStorage" in outputs and outputs["ElectricStorage"].get("size_kw", 0) > 0:
                storage = outputs["ElectricStorage"]
                summary += f"""

### Battery Storage
- **Power Capacity**: {storage.get('size_kw', 0):.1f} kW
- **Energy Capacity**: {storage.get('size_kwh', 0):.1f} kWh
- **Annual O&M Cost**: ${storage.get('annual_om_cost_before_tax', 0):,.0f}"""
            
            # Financial Summary
            if "Financial" in outputs:
                fin = outputs["Financial"]
                payback_str = f"{fin.get('simple_payback_years', 0):.1f}" if fin.get('simple_payback_years') else 'N/A'
                irr_str = f"{fin.get('internal_rate_of_return', 0)*100:.1f}%" if fin.get('internal_rate_of_return') else 'N/A'
                summary += f"""

## Financial Analysis
- **Net Present Value**: ${fin.get('npv', 0):,.0f}
- **Lifecycle Cost**: ${fin.get('lcc', 0):,.0f}
- **Simple Payback**: {payback_str} years
- **Internal Rate of Return**: {irr_str}"""
            
            # Utility Savings
            if "ElectricUtility" in outputs:
                util = outputs["ElectricUtility"]
                baseline_bill = util.get("year_one_bill_before_tax_bau", 0)
                optimized_bill = util.get("year_one_bill_before_tax", 0)
                savings = baseline_bill - optimized_bill
                summary += f"""

## Year 1 Utility Bill Analysis
- **Baseline Bill**: ${baseline_bill:,.0f}
- **With System**: ${optimized_bill:,.0f}
- **Annual Savings**: ${savings:,.0f}"""
            
            return [types.TextContent(type="text", text=summary)]
            
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error retrieving results summary: {str(e)}"
        )]


async def get_financial_summary(run_uuid: str) -> list[types.TextContent]:
    """Get detailed financial analysis in table format."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{REOPT_API_BASE_URL}/job/{run_uuid}/results"
            response = await client.get(url, params={"api_key": NREL_API_KEY})
            response.raise_for_status()
            result = response.json()
            outputs = result.get("outputs", {})
            
            if "Financial" not in outputs:
                return [types.TextContent(type="text", text="No financial results available.")]
            
            fin = outputs["Financial"]
            
            table = """# Financial Analysis

| Metric | Value |
|--------|-------|
"""
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
        return [types.TextContent(
            type="text",
            text=f"Error retrieving financial summary: {str(e)}"
        )]


async def get_system_summary(run_uuid: str) -> list[types.TextContent]:
    """Get technology system sizes and performance in table format."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{REOPT_API_BASE_URL}/job/{run_uuid}/results"
            response = await client.get(url, params={"api_key": NREL_API_KEY})
            response.raise_for_status()
            result = response.json()
            outputs = result.get("outputs", {})
            
            summary = "# System Technology Summary\n\n"
            
            # PV Table
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
            
            # Storage Table
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
            
            if "PV" not in outputs and "ElectricStorage" not in outputs:
                summary += """No distributed energy systems recommended by optimization.

This typically means that the economics don't favor installing solar PV or battery storage 
under the current scenario assumptions (tariff rates, load profile, technology costs, etc.).

Consider:
- Checking if utility rates are accurate (use URDB labels for real rates)
- Reviewing technology cost assumptions
- Adjusting financial parameters (discount rate, analysis period)
- Exploring different technologies or configurations
"""
            
            return [types.TextContent(type="text", text=summary)]
            
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error retrieving system summary: {str(e)}"
        )]


async def get_example_scenario() -> list[types.TextContent]:
    """Return an example REopt scenario."""
    example = {
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
    
    explanation = """This is a basic REopt scenario for a medium office building in Denver, CO.

Key Components:
- Site: Location coordinates (Denver, CO) for solar resource data
- ElectricLoad: Using DOE reference building profile for a medium office (1,000 MWh/year)
- ElectricTariff: Xcel Energy commercial rate (URDB label) with demand charges
- PV: Solar photovoltaic system up to 1000 kW
- ElectricStorage: Battery storage up to 500 kW / 1000 kWh

To customize for your project:
1. Change latitude/longitude to your site location
2. Use your actual load data or select appropriate DOE reference building
3. Find your utility rate URDB label at https://openei.org/apps/USURDB/ or provide custom tariff structure
4. Adjust max_kw limits based on available space and budget
5. Add other technologies like Wind, Generator, CHP as needed

Submit this example with submitAndWait to see how REopt optimizes the system design!"""
    
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "example_scenario": example,
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

