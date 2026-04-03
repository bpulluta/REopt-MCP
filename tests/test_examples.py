from reopt_mcp.examples import get_all_examples, get_base_inputs
from reopt_mcp.validation import validate_scenario


def test_all_bundled_examples_validate() -> None:
    examples = get_all_examples()
    failures: list[tuple[str, list[str]]] = []

    for key, payload in examples.items():
        is_valid, errors = validate_scenario(payload["scenario"])
        if not is_valid:
            failures.append((key, errors))

    assert failures == []


def test_base_inputs_include_only_required_sections() -> None:
    scenario = get_base_inputs()
    assert set(scenario.keys()) == {"Site", "ElectricLoad", "ElectricTariff"}
    assert "doe_reference_name" in scenario["ElectricLoad"]
    assert "annual_kwh" in scenario["ElectricLoad"]
