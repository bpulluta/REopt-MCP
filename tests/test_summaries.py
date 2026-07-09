from reopt_mcp.summaries import (
    build_submit_summary,
    format_financial_summary,
    format_results_summary,
    format_system_summary,
)


def test_format_results_summary_includes_key_sections() -> None:
    outputs = {
        "PV": {
            "size_kw": 120,
            "annual_energy_produced_kwh": 180000,
            "annual_om_cost_before_tax": 1200,
            "federal_itc_fraction": 0.3,
        },
        "ElectricStorage": {
            "size_kw": 50,
            "size_kwh": 200,
            "annual_om_cost_before_tax": 500,
        },
        "Financial": {
            "npv": 78000,
            "lcc": 420000,
            "simple_payback_years": 8.5,
            "internal_rate_of_return": 0.11,
        },
        "ElectricUtility": {
            "year_one_bill_before_tax_bau": 100000,
            "year_one_bill_before_tax": 74000,
        },
    }

    text = format_results_summary(outputs)

    assert "Solar PV" in text
    assert "Battery Storage" in text
    assert "Financial Analysis" in text
    assert "Annual Savings" in text


def test_summaries_include_wind_and_generator() -> None:
    outputs = {
        "Wind": {
            "size_kw": 300,
            "annual_energy_produced_kwh": 850000,
            "annual_om_cost_before_tax": 9000,
        },
        "Generator": {
            "size_kw": 125,
            "annual_fuel_consumption_gal": 1500,
            "annual_om_cost_before_tax": 800,
        },
        "Financial": {"npv": 145000},
    }

    results = format_results_summary(outputs)
    assert "Wind" in results
    assert "Backup Generator" in results

    system = format_system_summary(outputs)
    assert "Wind System" in system
    assert "Backup Generator" in system
    assert "Fuel Use" in system

    submit = build_submit_summary("run-w", 30, "optimal", outputs)
    assert "Wind: 300.0 kW" in submit
    assert "Generator: 125.0 kW" in submit


def test_build_submit_summary_tolerates_missing_npv() -> None:
    text = build_submit_summary("run-x", 10, "optimal", {"Financial": {}})
    assert "Run UUID: run-x" in text
    assert "NPV" not in text


def test_format_financial_summary_handles_missing_financial() -> None:
    assert format_financial_summary({}) == "No financial results available."


def test_format_system_summary_no_systems_message() -> None:
    text = format_system_summary({})
    assert "No distributed energy systems recommended." in text


def test_build_submit_summary_includes_core_metrics() -> None:
    outputs = {
        "PV": {"size_kw": 100.0},
        "ElectricStorage": {"size_kw": 40.0, "size_kwh": 160.0},
        "Financial": {"npv": 50000},
    }

    text = build_submit_summary("abc-123", 45, "optimal", outputs)

    assert "Run UUID: abc-123" in text
    assert "Status: optimal" in text
    assert "Solar PV: 100.0 kW" in text
    assert "Battery: 40.0 kW / 160.0 kWh" in text
    assert "NPV: $50,000" in text
