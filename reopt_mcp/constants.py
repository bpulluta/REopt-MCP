"""Shared constants for REopt MCP."""

VALID_DOE_REFERENCE_NAMES = {
    "FastFoodRest",
    "FullServiceRest",
    "Hospital",
    "LargeHotel",
    "LargeOffice",
    "MediumOffice",
    "MidriseApartment",
    "Outpatient",
    "PrimarySchool",
    "RetailStore",
    "SecondarySchool",
    "SmallHotel",
    "SmallOffice",
    "StripMall",
    "Supermarket",
    "Warehouse",
    "FlatLoad",
    "FlatLoad245",
    "FlatLoad167",
    "FlatLoad165",
    "FlatLoad87",
    "FlatLoad85",
}

INVALID_SITE_FIELDS = {"address", "city", "state", "zip", "country"}

VALID_ELECTRIC_TARIFF_KEYS = {
    "urdb_label",
    "urdb_response",
    "urdb_utility_name",
    "urdb_rate_name",
    "urdb_metadata",
    "wholesale_rate",
    "export_rate_beyond_net_metering_limit",
    "monthly_energy_rates",
    "monthly_demand_rates",
    "blended_annual_energy_rate",
    "blended_annual_demand_rate",
    "add_monthly_rates_to_urdb_rate",
    "tou_energy_rates_per_kwh",
    "add_tou_energy_rates_to_urdb_rate",
    "remove_tiers",
    "demand_lookback_months",
    "demand_lookback_percent",
    "demand_lookback_range",
    "coincident_peak_load_active_time_steps",
    "coincident_peak_load_charge_per_kw",
}

INVALID_ELECTRIC_TARIFF_ALIASES = {
    "blended_annual_rates_us_dollars_per_kwh": "blended_annual_energy_rate",
    "blended_annual_demand_charges_us_dollars_per_kw": "blended_annual_demand_rate",
}
