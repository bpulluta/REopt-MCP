/** Shared constants used by more than one scenario module.
 *
 * Section- or technology-specific constants live inside their module (e.g.
 * ElectricTariff's key sets are in src/modules/electric-tariff.ts). Technology
 * names are derived from the registry (src/modules/index.ts), never hardcoded.
 */

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
