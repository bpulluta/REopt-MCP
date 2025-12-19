#!/usr/bin/env python3
"""
Direct test of REopt API to verify endpoints work correctly.
"""

import os
import asyncio
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

NREL_API_KEY = os.getenv("NREL_API_KEY", "")
BASE_URL = "https://developer.nrel.gov/api/reopt/stable"

async def test_submit_job():
    """Test submitting a job."""
    scenario = {
        "Site": {
            "latitude": 39.7407,
            "longitude": -104.989
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
        }
    }
    
    print("Testing job submission...")
    print(f"URL: {BASE_URL}/job")
    print(f"Scenario: {json.dumps(scenario, indent=2)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/job",
            json=scenario,
            params={"api_key": NREL_API_KEY}
        )
        
        print(f"\nStatus Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code in [200, 201]:
            run_uuid = result.get("run_uuid")
            print(f"\n✓ Job submitted successfully!")
            print(f"Run UUID: {run_uuid}")
            return run_uuid
        else:
            print(f"\n✗ Job submission failed")
            return None

async def test_get_status(run_uuid):
    """Test getting job status via results endpoint."""
    if not run_uuid:
        print("\nSkipping status check - no run_uuid")
        return
    
    print(f"\n\nTesting status check for {run_uuid}...")
    print(f"URL: {BASE_URL}/job/{run_uuid}/results")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/job/{run_uuid}/results",
            params={"api_key": NREL_API_KEY}
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "Unknown")
            print(f"Job Status: {status}")
            print(f"Messages: {result.get('messages', {})}")
            print(f"\n✓ Status check successful!")
            print(f"Note: Job is complete if status is 'optimal' or 'not optimal'")
        else:
            print(f"Response: {response.text[:200]}")
            print(f"\n✗ Status check failed")

async def main():
    print("=" * 60)
    print("REopt API Direct Test")
    print("=" * 60)
    
    if not NREL_API_KEY:
        print("ERROR: NREL_API_KEY not set!")
        return
    
    print(f"\nUsing API Key: {NREL_API_KEY[:10]}...")
    print(f"Base URL: {BASE_URL}")
    
    # Test job submission
    run_uuid = await test_submit_job()
    
    # Test status check
    await test_get_status(run_uuid)
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
