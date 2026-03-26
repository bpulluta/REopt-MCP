#!/usr/bin/env python3
"""
Simple test to verify REopt MCP server configuration.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_environment():
    """Test environment configuration."""
    print("=" * 60)
    print("REopt MCP Configuration Test")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("NREL_API_KEY", "")
    if api_key and api_key != "your_api_key_here":
        print("✓ NREL_API_KEY is set")
        print(f"  Key: {api_key[:10]}...")
    else:
        print("✗ NREL_API_KEY not set or using placeholder")
        print("  Get a key at: https://developer.nrel.gov/signup/")
        return False
    
    # Check base URL
    base_url = os.getenv("REOPT_API_BASE_URL", "https://developer.nrel.gov/api/reopt/stable")
    print(f"✓ REOPT_API_BASE_URL: {base_url}")
    
    if "/stable" not in base_url and "/v3" not in base_url:
        print("  Warning: Base URL should include /stable or /v3")
    
    return True

def test_imports():
    """Test that required packages are available."""
    print("\nTesting imports...")
    
    try:
        import httpx
        print("✓ httpx installed")
    except ImportError:
        print("✗ httpx not installed")
        return False
    
    try:
        import mcp
        print("✓ mcp installed")
    except ImportError:
        print("✗ mcp not installed")
        return False
    
    return True

def test_server_import():
    """Test that server module can be imported."""
    print("\nTesting server module...")
    
    try:
        from reopt_mcp import server
        print("✓ reopt_mcp.server can be imported")
    except Exception as e:
        print(f"✗ Failed to import server: {e}")
        return False
    
    try:
        from reopt_mcp import examples
        print("✓ reopt_mcp.examples can be imported")
        
        # Test getting an example
        example = examples.get_solar_scenario()
        
        # Verify structure
        if "ElectricLoad" in example:
            print("✓ Example scenarios use correct structure (ElectricLoad)")
        else:
            print("✗ Example scenarios use old structure (missing ElectricLoad)")
            return False
            
    except Exception as e:
        print(f"✗ Failed to import examples: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    success = True
    
    success = test_environment() and success
    success = test_imports() and success
    success = test_server_import() and success
    
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
        print("\nYou can now:")
        print("1. Reload VS Code (Cmd+Shift+P → Developer: Reload Window)")
        print("2. Test in Copilot: @reopt get me an example scenario")
        print("3. Run full test: pixi run python test_api_direct.py")
    else:
        print("✗ Some tests failed")
        print("\nTroubleshooting:")
        print("1. Run: pixi install")
        print("2. Copy .env.example to .env and add your API key")
        print("3. Check README.md for setup instructions")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
