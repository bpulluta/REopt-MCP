"""
Example REopt Scenarios

This module provides various example scenarios for testing the REopt MCP server.
"""


def get_simple_pv_scenario():
    """
    A simple scenario evaluating solar PV for a medium office building.
    
    This scenario:
    - Uses a DOE reference building load profile
    - Evaluates solar PV up to 1000 kW
    - Uses a Colorado utility rate
    """
    return {
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
        }
    }


def get_pv_and_storage_scenario():
    """
    A scenario evaluating solar PV with battery storage.
    
    This scenario:
    - Uses a DOE reference building load profile
    - Evaluates solar PV up to 1000 kW
    - Evaluates battery storage (500 kW / 1000 kWh)
    - Uses a Colorado utility rate
    """
    return {
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


def get_custom_load_scenario():
    """
    A scenario with custom hourly load data.
    
    This scenario:
    - Uses custom hourly electric load data (8760 hours)
    - Evaluates solar PV
    - Uses a California utility rate
    """
    # Create a simple load profile (flat 100 kW)
    loads_kw = [100.0] * 8760
    
    return {
        "Site": {
            "latitude": 37.7749,
            "longitude": -122.4194
        },
        "ElectricLoad": {
            "loads_kw": loads_kw
        },
        "ElectricTariff": {
            "urdb_label": "5ca4d1175457a39b23b3d45e"  # Example rate
        },
        "PV": {
            "max_kw": 500
        }
    }


def get_resilience_scenario():
    """
    A scenario focused on resilience (backup power).
    
    This scenario:
    - Evaluates backup power capabilities
    - Includes critical load definition
    - Evaluates solar PV and battery storage
    - Specifies outage duration requirements
    """
    return {
        "Site": {
            "latitude": 39.7407,
            "longitude": -104.9890
        },
        "ElectricLoad": {
            "doe_reference_name": "Hospital",
            "annual_kwh": 5000000,
            "critical_load_fraction": 0.5
        },
        "ElectricTariff": {
            "urdb_label": "5ca4d1175457a39b23b3d45e"
        },
        "PV": {
            "max_kw": 2000
        },
        "ElectricStorage": {
            "max_kw": 1000,
            "max_kwh": 4000
        },
        "Financial": {
            "analysis_years": 25,
            "value_of_lost_load_per_kwh": 100.0
        }
    }


def get_wind_scenario():
    """
    A scenario evaluating wind energy.
    
    This scenario:
    - Evaluates wind turbines
    - Uses a location with good wind resources
    - Includes solar PV for comparison
    """
    return {
        "Site": {
            "latitude": 41.8781,
            "longitude": -87.6298  # Chicago
        },
        "ElectricLoad": {
            "doe_reference_name": "LargeOffice",
            "annual_kwh": 10000000
        },
        "ElectricTariff": {
            "urdb_label": "5ca4d1175457a39b23b3d45e"
        },
        "Wind": {
            "max_kw": 2000
        },
        "PV": {
            "max_kw": 1000
        }
    }


def get_all_examples():
    """Return a dictionary of all example scenarios."""
    return {
        "simple_pv": {
            "name": "Simple Solar PV",
            "description": "Basic solar PV evaluation for a medium office",
            "scenario": get_simple_pv_scenario()
        },
        "pv_and_storage": {
            "name": "Solar PV with Battery Storage",
            "description": "Solar PV and battery storage evaluation",
            "scenario": get_pv_and_storage_scenario()
        },
        "custom_load": {
            "name": "Custom Load Profile",
            "description": "Scenario with custom hourly load data",
            "scenario": get_custom_load_scenario()
        },
        "resilience": {
            "name": "Resilience Analysis",
            "description": "Backup power and resilience evaluation",
            "scenario": get_resilience_scenario()
        },
        "wind": {
            "name": "Wind Energy",
            "description": "Wind turbine evaluation with solar comparison",
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
