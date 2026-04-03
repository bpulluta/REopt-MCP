"""Scenario validation and guidance."""

from reopt_mcp.constants import (
    INVALID_ELECTRIC_TARIFF_ALIASES,
    INVALID_SITE_FIELDS,
    VALID_DOE_REFERENCE_NAMES,
    VALID_ELECTRIC_TARIFF_KEYS,
)


def validate_scenario(scenario: dict) -> tuple[bool, list[str]]:
    """Validate that scenario has all required fields and no invalid assumptions."""
    if not isinstance(scenario, dict):
        return False, ["Scenario must be an object"]

    errors: list[str] = []

    settings = scenario.get("Settings", {})
    off_grid_flag = False
    if settings:
        if not isinstance(settings, dict):
            errors.append("Settings must be an object when provided")
        elif "off_grid_flag" in settings:
            if isinstance(settings["off_grid_flag"], bool):
                off_grid_flag = settings["off_grid_flag"]
            else:
                errors.append("Settings 'off_grid_flag' must be a boolean")

    if "Site" not in scenario:
        errors.append("Missing 'Site' object")
    else:
        site = scenario["Site"]
        invalid_fields = set(site.keys()) & INVALID_SITE_FIELDS
        if invalid_fields:
            errors.append(
                f"Site contains invalid fields: {invalid_fields}. Only use latitude/longitude."
            )
        if "latitude" not in site:
            errors.append("Site missing 'latitude'")
        if "longitude" not in site:
            errors.append("Site missing 'longitude'")

    if "ElectricLoad" not in scenario:
        errors.append("Missing 'ElectricLoad' object")
    else:
        load = scenario["ElectricLoad"]
        if not isinstance(load, dict):
            errors.append("ElectricLoad must be an object")
            return (len(errors) == 0, errors)

        if "doe_reference_name" not in load:
            errors.append("ElectricLoad missing 'doe_reference_name'")
        elif load["doe_reference_name"] not in VALID_DOE_REFERENCE_NAMES:
            errors.append(
                f"Invalid doe_reference_name: '{load['doe_reference_name']}'. Must be one of: {', '.join(sorted(VALID_DOE_REFERENCE_NAMES))}"
            )

        if "annual_kwh" not in load:
            errors.append("ElectricLoad missing 'annual_kwh'")
        elif (
            not isinstance(load["annual_kwh"], (int, float)) or load["annual_kwh"] <= 0
        ):
            errors.append("ElectricLoad 'annual_kwh' must be a positive number")

        blended_names = load.get("blended_doe_reference_names")
        blended_percents = load.get("blended_doe_reference_percents")
        if blended_names is not None or blended_percents is not None:
            if not isinstance(blended_names, list) or not isinstance(
                blended_percents, list
            ):
                errors.append(
                    "ElectricLoad blended DOE inputs must include both list fields: 'blended_doe_reference_names' and 'blended_doe_reference_percents'"
                )
            elif len(blended_names) != len(blended_percents):
                errors.append(
                    "ElectricLoad blended DOE inputs must have matching lengths"
                )
            elif len(blended_names) == 0:
                errors.append(
                    "ElectricLoad blended DOE inputs cannot be empty when provided"
                )
            else:
                invalid_names = [
                    name
                    for name in blended_names
                    if name not in VALID_DOE_REFERENCE_NAMES
                ]
                if invalid_names:
                    errors.append(
                        f"ElectricLoad blended_doe_reference_names contains invalid entries: {invalid_names}"
                    )

                if not all(
                    isinstance(percent, (int, float)) for percent in blended_percents
                ):
                    errors.append(
                        "ElectricLoad blended_doe_reference_percents must be numeric values"
                    )
                else:
                    total = sum(float(percent) for percent in blended_percents)
                    if abs(total - 1.0) > 1e-6:
                        errors.append(
                            "ElectricLoad blended_doe_reference_percents must sum to 1.0"
                        )

    if off_grid_flag and "ElectricTariff" in scenario:
        errors.append(
            "ElectricTariff cannot be supplied when Settings 'off_grid_flag' is true"
        )
    elif not off_grid_flag and "ElectricTariff" not in scenario:
        errors.append("Missing 'ElectricTariff' object")
    else:
        tariff = scenario.get("ElectricTariff")
        if tariff is None:
            return (len(errors) == 0, errors)

        if not isinstance(tariff, dict):
            errors.append("ElectricTariff must be an object")
            return (len(errors) == 0, errors)

        invalid_aliases_used = set(tariff.keys()) & set(
            INVALID_ELECTRIC_TARIFF_ALIASES.keys()
        )
        if invalid_aliases_used:
            alias_guidance = ", ".join(
                f"'{bad}' -> '{INVALID_ELECTRIC_TARIFF_ALIASES[bad]}'"
                for bad in sorted(invalid_aliases_used)
            )
            errors.append(
                f"ElectricTariff contains invalid keys for REopt.jl: {sorted(invalid_aliases_used)}. Use {alias_guidance}."
            )

        unknown_tariff_keys = set(tariff.keys()) - VALID_ELECTRIC_TARIFF_KEYS
        if unknown_tariff_keys:
            errors.append(
                f"ElectricTariff contains unsupported keys: {sorted(unknown_tariff_keys)}"
            )

        urdb_label = tariff.get("urdb_label")
        has_urdb = isinstance(urdb_label, str) and bool(urdb_label.strip())
        has_blended_energy = "blended_annual_energy_rate" in tariff
        has_blended_demand = "blended_annual_demand_rate" in tariff
        has_blended = has_blended_energy and has_blended_demand

        if not has_urdb and not has_blended:
            errors.append(
                "ElectricTariff must include either non-empty 'urdb_label' or both 'blended_annual_energy_rate' and 'blended_annual_demand_rate'"
            )

    return (len(errors) == 0, errors)


def guidance_for_errors(errors: list[str]) -> list[str]:
    guidance: list[str] = []
    for err in errors:
        if "latitude" in err or "longitude" in err:
            guidance.append(
                "📍 Ask user for the city/address, then look up coordinates"
            )
        elif "doe_reference_name" in err:
            guidance.append(
                "🏢 Ask user for building type (office, retail, warehouse, etc.)"
            )
        elif "annual_kwh" in err:
            guidance.append("⚡ Ask user for annual electricity consumption in kWh")
        elif "off_grid_flag" in err:
            guidance.append(
                "🔌 For off-grid scenarios set Settings.off_grid_flag=true and remove ElectricTariff"
            )
        elif "ElectricTariff" in err or "urdb_label" in err:
            guidance.append(
                "💵 Look up utility-specific URDB label or collect blended rates using REopt.jl keys: blended_annual_energy_rate and blended_annual_demand_rate"
            )
    return list(set(guidance))
