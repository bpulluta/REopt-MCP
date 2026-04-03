from reopt_mcp.examples import get_base_inputs
from reopt_mcp.validation import guidance_for_errors, validate_scenario


def test_validate_scenario_accepts_valid_base_inputs() -> None:
    scenario = get_base_inputs()
    is_valid, errors = validate_scenario(scenario)

    assert is_valid is True
    assert errors == []


def test_validate_scenario_rejects_missing_required_fields() -> None:
    scenario = {
        "Site": {"latitude": 39.74},
        "ElectricLoad": {"doe_reference_name": "MediumOffice"},
        "ElectricTariff": {},
    }

    is_valid, errors = validate_scenario(scenario)

    assert is_valid is False
    assert "Site missing 'longitude'" in errors
    assert "ElectricLoad missing 'annual_kwh'" in errors
    assert any(
        "ElectricTariff must include either non-empty 'urdb_label'" in err
        for err in errors
    )


def test_validate_scenario_accepts_blended_tariff_path() -> None:
    scenario = get_base_inputs()
    scenario["ElectricTariff"] = {
        "blended_annual_energy_rate": 0.12,
        "blended_annual_demand_rate": 15.0,
    }

    is_valid, errors = validate_scenario(scenario)

    assert is_valid is True
    assert errors == []


def test_validate_scenario_rejects_invalid_blended_tariff_aliases() -> None:
    scenario = get_base_inputs()
    scenario["ElectricTariff"] = {
        "blended_annual_rates_us_dollars_per_kwh": 0.12,
        "blended_annual_demand_charges_us_dollars_per_kw": 15.0,
    }

    is_valid, errors = validate_scenario(scenario)

    assert is_valid is False
    assert any("invalid keys for REopt.jl" in err for err in errors)
    assert any("blended_annual_energy_rate" in err for err in errors)
    assert any("blended_annual_demand_rate" in err for err in errors)


def test_validate_scenario_rejects_invalid_site_fields() -> None:
    scenario = get_base_inputs()
    scenario["Site"]["address"] = "123 Main St"

    is_valid, errors = validate_scenario(scenario)

    assert is_valid is False
    assert any("Site contains invalid fields" in err for err in errors)


def test_validate_scenario_rejects_electric_tariff_for_off_grid() -> None:
    scenario = get_base_inputs()
    scenario["Settings"] = {"off_grid_flag": True}

    is_valid, errors = validate_scenario(scenario)

    assert is_valid is False
    assert any(
        "cannot be supplied when Settings 'off_grid_flag' is true" in err
        for err in errors
    )


def test_validate_scenario_allows_off_grid_without_tariff() -> None:
    scenario = get_base_inputs()
    scenario["Settings"] = {"off_grid_flag": True}
    scenario.pop("ElectricTariff", None)

    is_valid, errors = validate_scenario(scenario)

    assert is_valid is True
    assert errors == []


def test_validate_scenario_rejects_bad_blended_doe_percents() -> None:
    scenario = get_base_inputs()
    scenario["ElectricLoad"]["blended_doe_reference_names"] = [
        "MediumOffice",
        "RetailStore",
    ]
    scenario["ElectricLoad"]["blended_doe_reference_percents"] = [0.7, 0.4]

    is_valid, errors = validate_scenario(scenario)

    assert is_valid is False
    assert any("must sum to 1.0" in err for err in errors)


def test_guidance_for_errors_maps_to_expected_prompts() -> None:
    errors = [
        "Site missing 'latitude'",
        "ElectricLoad missing 'annual_kwh'",
        "ElectricTariff must include either non-empty 'urdb_label' or both blended annual rate fields",
    ]

    guidance = guidance_for_errors(errors)

    assert any("look up coordinates" in item for item in guidance)
    assert any("annual electricity consumption" in item for item in guidance)
    assert any("URDB label" in item for item in guidance)
