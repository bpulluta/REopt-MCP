"""
Example REopt Scenarios

This module provides various example scenarios for testing the REopt MCP server.

NOTE: Most scenarios now use minimal inputs (only Site, ElectricLoad, ElectricTariff)
      to let REopt automatically optimize system sizes.
"""


def get_base_inputs():
    """
    Returns just the 3 required inputs - no technologies.
    Use this as a starting point and add technologies as needed.
    
    CRITICAL: ElectricLoad MUST have BOTH fields:
    - doe_reference_name: provides hourly load pattern/shape
    - annual_kwh: scales the pattern to your consumption
    """
    return {
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


def get_solar_scenario():
    """Evaluate solar PV only - no constraints."""
    scenario = get_base_inputs()
    scenario["PV"] = {}
    return scenario


def get_solar_battery_scenario():
    """Evaluate solar + battery - no constraints."""
    scenario = get_base_inputs()
    scenario["PV"] = {}
    scenario["ElectricStorage"] = {}
    return scenario


def get_pv_and_storage_scenario():
    """
    Solar + battery with constraints (only if you have space/budget limits).
    """
    scenario = get_base_inputs()
    scenario["PV"] = {"max_kw": 500}
    scenario["ElectricStorage"] = {"max_kw": 250, "max_kwh": 1000}
    return scenario


def get_resilience_scenario():
    """
    Resilience/backup power scenario with generator.
    """
    scenario = get_base_inputs()
    scenario["ElectricLoad"] = {
        "doe_reference_name": "Hospital",
        "annual_kwh": 5000000,
        "critical_load_fraction": 0.5
    }
    scenario["PV"] = {}
    scenario["ElectricStorage"] = {}
    scenario["Generator"] = {}
    scenario["Financial"] = {"value_of_lost_load_per_kwh": 100.0}
    return scenario


def get_wind_scenario():
    """
    Multi-technology: solar + wind + battery.
    """
    scenario = get_base_inputs()
    scenario["Site"]["latitude"] = 41.8781
    scenario["Site"]["longitude"] = -87.6298  # Chicago
    scenario["PV"] = {}
    scenario["Wind"] = {}
    scenario["ElectricStorage"] = {}
    return scenario


def get_all_examples():
    """Return a dictionary of all example scenarios."""
    return {
        "base": {
            "name": "Base Inputs Only",
            "description": "Just the 3 required inputs - add technologies as needed",
            "scenario": get_base_inputs()
        },
        "solar": {
            "name": "Solar Only",
            "description": "Evaluate solar PV with no constraints",
            "scenario": get_solar_scenario()
        },
        "solar_battery": {
            "name": "Solar + Battery",
            "description": "Evaluate solar and battery with no constraints",
            "scenario": get_solar_battery_scenario()
        },
        "pv_and_storage": {
            "name": "With Constraints",
            "description": "Solar + battery with size limits (only if you have actual constraints)",
            "scenario": get_pv_and_storage_scenario()
        },
        "resilience": {
            "name": "Resilience Analysis",
            "description": "Backup power evaluation with generator",
            "scenario": get_resilience_scenario()
        },
        "wind": {
            "name": "Wind + Solar",
            "description": "Multi-technology evaluation",
            "scenario": get_wind_scenario()
        }
    }


if __name__ == "__main__":
    """Print all example scenarios."""
    import json
    
    examples = get_all_examples()
    
    print("Available Example Scenarios")
    print("=" * 60)
    
    for key, example in examples.items():
        print(f"\n{example['name']} ({key})")
        print(f"Description: {example['description']}")
        print("\nScenario JSON:")
        print(json.dumps(example['scenario'], indent=2))
        print("\n" + "-" * 60)
