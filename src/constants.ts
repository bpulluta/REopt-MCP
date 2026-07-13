/** Shared constants for REopt MCP. */

// Technologies the server validates and summarizes. Only these keys may be added
// to a scenario as generation/storage options; each must be a JSON object ({}).
export const KNOWN_TECHNOLOGIES: ReadonlySet<string> = new Set([
  "PV",
  "Wind",
  "ElectricStorage",
  "Generator",
]);

// Valid geographic coordinate bounds (WGS84 degrees).
export const LATITUDE_RANGE: readonly [number, number] = [-90.0, 90.0];
export const LONGITUDE_RANGE: readonly [number, number] = [-180.0, 180.0];

export const VALID_DOE_REFERENCE_NAMES: ReadonlySet<string> = new Set([
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
]);

export const INVALID_SITE_FIELDS: ReadonlySet<string> = new Set([
  "address",
  "city",
  "state",
  "zip",
  "country",
]);

export const VALID_ELECTRIC_TARIFF_KEYS: ReadonlySet<string> = new Set([
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
]);

export const INVALID_ELECTRIC_TARIFF_ALIASES: Readonly<Record<string, string>> = {
  blended_annual_rates_us_dollars_per_kwh: "blended_annual_energy_rate",
  blended_annual_demand_charges_us_dollars_per_kw: "blended_annual_demand_rate",
};

// Convenience shorthand keys the server compiles into canonical REopt keys before
// submission. These are NOT sent to REopt; they are expanded by a section handler.
// (see src/sections.ts and src/tariff.ts)
export const TARIFF_SHORTHAND_KEYS: ReadonlySet<string> = new Set([
  "tou_energy_schedule",
]);

// Any one of these keys constitutes a valid energy-price signal for a tariff.
// REopt requires an energy rate; demand charges are optional.
export const TARIFF_ENERGY_RATE_SOURCE_KEYS: ReadonlySet<string> = new Set([
  "urdb_label",
  "urdb_response",
  "blended_annual_energy_rate",
  "monthly_energy_rates",
  "tou_energy_rates_per_kwh",
  "tou_energy_schedule", // shorthand; compiles to tou_energy_rates_per_kwh
]);

// Monthly blended-rate arrays must cover all 12 calendar months.
export const MONTHLY_RATE_LENGTH = 12;

// Valid lengths for a full-year timeseries at 1, 2, or 4 time steps per hour.
export const VALID_TOU_ARRAY_LENGTHS: ReadonlySet<number> = new Set([
  8760, 17520, 35040,
]);

// Reference calendar year REopt uses to align rate schedules with weekdays/weekends
// when a load profile comes from a DOE CRB reference building.
export const DEFAULT_RATE_SCHEDULE_YEAR = 2017;
