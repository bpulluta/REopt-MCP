#!/usr/bin/env python3
"""
Comprehensive test script for REopt MCP Server

This script tests the MCP server by:
1. Checking configuration and dependencies
2. Testing server startup
3. Testing each tool individually
4. Running an end-to-end scenario
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


async def test_configuration():
    """Test 1: Check configuration and environment."""
    print_header("Test 1: Configuration Check")
    
    all_good = True
    
    # Check .env file exists
    if Path(".env").exists():
        print_success(".env file found")
    else:
        print_error(".env file not found")
        print_info("Copy .env.example to .env and add your API key")
        all_good = False
    
    # Check API key
    api_key = os.getenv("NREL_API_KEY", "")
    if api_key and api_key != "your_api_key_here":
        print_success(f"NREL_API_KEY is set ({api_key[:8]}...)")
    else:
        print_error("NREL_API_KEY not properly configured")
        print_info("Get your API key from: https://developer.nrel.gov/signup/")
        all_good = False
    
    # Check API base URL
    api_url = os.getenv("REOPT_API_BASE_URL", "https://developer.nrel.gov/api/reopt")
    print_success(f"API Base URL: {api_url}")
    
    # Check Python version
    if sys.version_info >= (3, 10):
        print_success(f"Python version: {sys.version.split()[0]}")
    else:
        print_error(f"Python version {sys.version.split()[0]} is too old (need 3.10+)")
        all_good = False
    
    # Check dependencies
    try:
        import mcp
        print_success("mcp package installed")
    except ImportError:
        print_error("mcp package not installed")
        print_info("Run: pixi install")
        all_good = False
    
    try:
        import httpx
        print_success("httpx package installed")
    except ImportError:
        print_error("httpx package not installed")
        all_good = False
    
    try:
        import pydantic
        print_success("pydantic package installed")
    except ImportError:
        print_error("pydantic package not installed")
        all_good = False
    
    return all_good


async def test_api_connection():
    """Test 2: Verify API connection."""
    print_header("Test 2: API Connection Check")
    
    api_key = os.getenv("NREL_API_KEY", "")
    if not api_key or api_key == "your_api_key_here":
        print_warning("Skipping API test - no valid API key")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try a simple API call to verify the key works
            # Use a minimal scenario to test
            url = "https://developer.nrel.gov/api/reopt/v3/job"
            test_scenario = {
                "Site": {
                    "latitude": 39.7407,
                    "longitude": -104.9890
                },
                "ElectricLoad": {
                    "doe_reference_name": "MediumOffice"
                },
                "ElectricTariff": {
                    "urdb_label": "5ca4d1175457a39b23b3d45e"
                },
                "PV": {
                    "max_kw": 0  # Don't actually optimize, just test connection
                }
            }
            
            response = await client.post(
                url, 
                json=test_scenario,
                params={"api_key": api_key}
            )
            
            if response.status_code in [200, 201]:
                print_success("API connection successful")
                result = response.json()
                if "run_uuid" in result:
                    print_info(f"Test job created: {result['run_uuid']}")
                return True
            else:
                print_error(f"API returned status code {response.status_code}")
                print_info(f"Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print_error(f"Failed to connect to API: {e}")
        return False


async def test_server_import():
    """Test 3: Test server module import."""
    print_header("Test 3: Server Module Import")
    
    try:
        from reopt_mcp import server
        print_success("Server module imported successfully")
        
        # Check main functions exist
        if hasattr(server, 'main'):
            print_success("main() function found")
        
        if hasattr(server, 'app'):
            print_success("MCP server app found")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to import server: {e}")
        return False


async def test_example_scenarios():
    """Test 4: Test example scenario generation."""
    print_header("Test 4: Example Scenarios")
    
    try:
        from reopt_mcp.examples import (
            get_simple_pv_scenario,
            get_pv_and_storage_scenario
        )
        
        # Test simple PV scenario
        scenario = get_simple_pv_scenario()
        if "Site" in scenario and "PV" in scenario:
            print_success("Simple PV scenario generated")
            print_info(f"Location: {scenario['Site']['latitude']}, {scenario['Site']['longitude']}")
        else:
            print_error("Simple PV scenario missing required fields")
            return False
        
        # Test PV + storage scenario
        scenario = get_pv_and_storage_scenario()
        if "ElectricStorage" in scenario:
            print_success("PV + Storage scenario generated")
        else:
            print_error("PV + Storage scenario missing ElectricStorage")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Failed to generate scenarios: {e}")
        return False


async def test_full_workflow():
    """Test 5: Test complete workflow if API key is available."""
    print_header("Test 5: Full Workflow (Submit Job)")
    
    api_key = os.getenv("NREL_API_KEY", "")
    if not api_key or api_key == "your_api_key_here":
        print_warning("Skipping workflow test - no valid API key")
        print_info("Set your API key in .env to run this test")
        return None
    
    try:
        from reopt_mcp.server import submit_reopt_job, get_job_status
        from reopt_mcp.examples import get_simple_pv_scenario
        
        # Get example scenario
        scenario = get_simple_pv_scenario()
        print_info("Submitting optimization job...")
        
        # Submit job
        result = await submit_reopt_job(scenario)
        result_text = result[0].text
        result_data = json.loads(result_text)
        
        if result_data.get("status") == "success":
            run_uuid = result_data.get("run_uuid")
            print_success(f"Job submitted successfully!")
            print_info(f"Run UUID: {run_uuid}")
            
            # Check status
            print_info("Checking job status...")
            await asyncio.sleep(2)  # Wait a bit
            
            status_result = await get_job_status(run_uuid)
            status_text = status_result[0].text
            status_data = json.loads(status_text)
            
            if status_data.get("status") == "success":
                job_status = status_data.get("job_status")
                print_success(f"Job status retrieved: {job_status}")
                print_info("Note: Job may take several minutes to complete")
                return True
            else:
                print_error("Failed to retrieve job status")
                return False
        else:
            print_error(f"Job submission failed: {result_data}")
            return False
            
    except Exception as e:
        print_error(f"Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print test summary."""
    print_header("Test Summary")
    
    total = len([r for r in results.values() if r is not None])
    passed = sum(1 for r in results.values() if r is True)
    
    print(f"Tests passed: {passed}/{total}")
    print()
    
    for test_name, result in results.items():
        if result is True:
            print_success(test_name)
        elif result is False:
            print_error(test_name)
        else:
            print_warning(f"{test_name} (skipped)")
    
    print()
    
    if passed == total:
        print_success("All tests passed! Your MCP server is ready to use.")
        print_info("\nNext steps:")
        print_info("1. Reload VS Code (Cmd+Shift+P → 'Developer: Reload Window')")
        print_info("2. Open Copilot Chat")
        print_info("3. Try: '@reopt what tools are available?'")
    else:
        print_warning("Some tests failed. Please fix the issues above.")
        print_info("\nCommon fixes:")
        print_info("1. Run: pixi install")
        print_info("2. Copy .env.example to .env and add your API key")
        print_info("3. Get API key from: https://developer.nrel.gov/signup/")


async def main():
    """Run all tests."""
    print(f"{Colors.BOLD}REopt MCP Server Test Suite{Colors.END}")
    print(f"Testing server functionality...\n")
    
    results = {}
    
    # Run tests in order
    results["Configuration"] = await test_configuration()
    results["Server Import"] = await test_server_import()
    results["Example Scenarios"] = await test_example_scenarios()
    results["API Connection"] = await test_api_connection()
    results["Full Workflow"] = await test_full_workflow()
    
    # Print summary
    print_summary(results)
    
    # Return exit code
    failed = sum(1 for r in results.values() if r is False)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
