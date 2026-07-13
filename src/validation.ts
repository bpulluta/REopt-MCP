/** Scenario validation and guidance. */

import {
  INVALID_SITE_FIELDS,
  KNOWN_TECHNOLOGIES,
  LATITUDE_RANGE,
  LONGITUDE_RANGE,
  VALID_DOE_REFERENCE_NAMES,
} from "./constants.js";
import { sectionWarnings, validateSections } from "./sections.js";
import { quotedList } from "./format.js";

type Dict = Record<string, unknown>;

/** True for real numbers, excluding bool. */
function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isDict(value: unknown): value is Dict {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Truthiness check: empty dict/list/string, 0, null, and false are all falsy. */
function isTruthy(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  if (typeof value === "string") return value.length > 0;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "object") return Object.keys(value).length > 0;
  return true;
}

/** Render a number with a trailing `.0` for whole values, e.g. `90.0` not `90`. */
function floatStr(x: number): string {
  return Number.isInteger(x) ? `${x}.0` : `${x}`;
}

/** Render strings as a quoted, brace-wrapped set (sorted), e.g. `{'a', 'b'}`. */
function bracedList(items: string[]): string {
  return `{${[...items].sort().map((s) => `'${s}'`).join(", ")}}`;
}

function validateCoordinate(
  site: Dict,
  field: string,
  bounds: readonly [number, number],
  errors: string[],
): void {
  if (!(field in site)) {
    errors.push(`Site missing '${field}'`);
    return;
  }
  const value = site[field];
  if (!isNumber(value)) {
    errors.push(`Site '${field}' must be a number`);
    return;
  }
  const [low, high] = bounds;
  if (!(low <= value && value <= high)) {
    errors.push(
      `Site '${field}' must be between ${floatStr(low)} and ${floatStr(high)} (got ${value})`,
    );
  }
}

/** Validate that scenario has all required fields and no invalid assumptions. */
export function validateScenario(scenario: unknown): [boolean, string[]] {
  if (!isDict(scenario)) return [false, ["Scenario must be an object"]];

  const errors: string[] = [];

  const settings = "Settings" in scenario ? scenario.Settings : {};
  let offGridFlag = false;
  if (isTruthy(settings)) {
    if (!isDict(settings)) {
      errors.push("Settings must be an object when provided");
    } else if ("off_grid_flag" in settings) {
      if (typeof settings.off_grid_flag === "boolean") {
        offGridFlag = settings.off_grid_flag;
      } else {
        errors.push("Settings 'off_grid_flag' must be a boolean");
      }
    }
  }

  if (!("Site" in scenario)) {
    errors.push("Missing 'Site' object");
  } else if (!isDict(scenario.Site)) {
    errors.push("Site must be an object");
  } else {
    const site = scenario.Site;
    const invalidFields = Object.keys(site).filter((k) => INVALID_SITE_FIELDS.has(k));
    if (invalidFields.length > 0) {
      errors.push(
        `Site contains invalid fields: ${bracedList(invalidFields)}. Only use latitude/longitude.`,
      );
    }
    validateCoordinate(site, "latitude", LATITUDE_RANGE, errors);
    validateCoordinate(site, "longitude", LONGITUDE_RANGE, errors);
  }

  if (!("ElectricLoad" in scenario)) {
    errors.push("Missing 'ElectricLoad' object");
  } else {
    const load = scenario.ElectricLoad;
    if (!isDict(load)) {
      errors.push("ElectricLoad must be an object");
      return [errors.length === 0, errors];
    }

    if (!("doe_reference_name" in load)) {
      errors.push("ElectricLoad missing 'doe_reference_name'");
    } else if (!VALID_DOE_REFERENCE_NAMES.has(load.doe_reference_name as string)) {
      errors.push(
        `Invalid doe_reference_name: '${load.doe_reference_name}'. Must be one of: ${[
          ...VALID_DOE_REFERENCE_NAMES,
        ]
          .sort()
          .join(", ")}`,
      );
    }

    if (!("annual_kwh" in load)) {
      errors.push("ElectricLoad missing 'annual_kwh'");
    } else if (!isNumber(load.annual_kwh) || (load.annual_kwh as number) <= 0) {
      errors.push("ElectricLoad 'annual_kwh' must be a positive number");
    }

    if ("critical_load_fraction" in load) {
      const fraction = load.critical_load_fraction;
      if (!isNumber(fraction) || !(fraction >= 0.0 && fraction <= 1.0)) {
        errors.push(
          "ElectricLoad 'critical_load_fraction' must be a number between 0 and 1",
        );
      }
    }

    const blendedNames = load.blended_doe_reference_names;
    const blendedPercents = load.blended_doe_reference_percents;
    if (
      (blendedNames !== undefined && blendedNames !== null) ||
      (blendedPercents !== undefined && blendedPercents !== null)
    ) {
      if (!Array.isArray(blendedNames) || !Array.isArray(blendedPercents)) {
        errors.push(
          "ElectricLoad blended DOE inputs must include both list fields: 'blended_doe_reference_names' and 'blended_doe_reference_percents'",
        );
      } else if (blendedNames.length !== blendedPercents.length) {
        errors.push("ElectricLoad blended DOE inputs must have matching lengths");
      } else if (blendedNames.length === 0) {
        errors.push("ElectricLoad blended DOE inputs cannot be empty when provided");
      } else {
        const invalidNames = blendedNames.filter(
          (name) => !VALID_DOE_REFERENCE_NAMES.has(name as string),
        );
        if (invalidNames.length > 0) {
          errors.push(
            `ElectricLoad blended_doe_reference_names contains invalid entries: ${quotedList(
              invalidNames.map((n) => String(n)),
            )}`,
          );
        }

        if (!blendedPercents.every((p) => typeof p === "number")) {
          errors.push(
            "ElectricLoad blended_doe_reference_percents must be numeric values",
          );
        } else {
          const total = blendedPercents.reduce((a, b) => a + (b as number), 0);
          if (Math.abs(total - 1.0) > 1e-6) {
            errors.push(
              "ElectricLoad blended_doe_reference_percents must sum to 1.0",
            );
          }
        }
      }
    }
  }

  const offGridTariffPresent = offGridFlag && "ElectricTariff" in scenario;
  if (offGridTariffPresent) {
    errors.push(
      "ElectricTariff cannot be supplied when Settings 'off_grid_flag' is true",
    );
  } else if (!offGridFlag && !("ElectricTariff" in scenario)) {
    errors.push("Missing 'ElectricTariff' object");
  }

  for (const tech of [...KNOWN_TECHNOLOGIES].sort()) {
    if (tech in scenario && !isDict(scenario[tech])) {
      errors.push(
        `Technology '${tech}' must be an object (use {} to let REopt optimize sizing)`,
      );
    }
  }

  // Delegate per-section content checks (ElectricTariff rate modes, and any future
  // sections) to their handlers. Skip ElectricTariff when its mere presence off-grid
  // is already flagged above.
  const skip = offGridTariffPresent ? new Set(["ElectricTariff"]) : null;
  errors.push(...validateSections(scenario, skip));

  return [errors.length === 0, errors];
}

/** Non-blocking advisories to surface for human review before submission. */
export function scenarioWarnings(scenario: unknown): string[] {
  const warnings: string[] = [];
  if (!isDict(scenario)) return warnings;

  const requested = [...KNOWN_TECHNOLOGIES].filter((tech) => tech in scenario);
  if (requested.length === 0) {
    warnings.push(
      "No technology requested (PV, Wind, ElectricStorage, Generator). " +
        "This runs a baseline-only scenario with no recommended systems.",
    );
  }

  warnings.push(...sectionWarnings(scenario));
  return warnings;
}

export function guidanceForErrors(errors: string[]): string[] {
  const guidance: string[] = [];
  for (const err of errors) {
    if (err.includes("must be an object") && err.includes("Technology")) {
      guidance.push(
        '🔧 Add technologies as empty objects, e.g. "PV": {} — never a string or list',
      );
    } else if (err.includes("latitude") || err.includes("longitude")) {
      guidance.push(
        "📍 Ask user for the city/address, then look up valid coordinates (lat -90..90, lon -180..180)",
      );
    } else if (err.includes("doe_reference_name")) {
      guidance.push(
        "🏢 Ask user for building type (office, retail, warehouse, etc.)",
      );
    } else if (err.includes("annual_kwh")) {
      guidance.push("⚡ Ask user for annual electricity consumption in kWh");
    } else if (err.includes("off_grid_flag")) {
      guidance.push(
        "🔌 For off-grid scenarios set Settings.off_grid_flag=true and remove ElectricTariff",
      );
    } else if (err.includes("energy-rate source")) {
      guidance.push(
        "💵 Pick a rate mode: blended (blended_annual_energy_rate + blended_annual_demand_rate), monthly (monthly_energy_rates), time-of-use (tou_energy_schedule), or a URDB label (urdb_label — use searchUrdbRates to find one). See getScenarioHelp('tariff').",
      );
    } else if (
      err.includes("monthly_energy_rates") ||
      err.includes("monthly_demand_rates")
    ) {
      guidance.push(
        "📅 Monthly rates need exactly 12 non-negative values (Jan–Dec). Ask the user for each month's $/kWh (energy) or $/kW (demand).",
      );
    } else if (err.includes("tou_energy_schedule")) {
      guidance.push(
        "🕐 Fix the time-of-use schedule: each period needs a non-negative rate, months 1–12, days weekday|weekend|all, and [start, end) hour ranges within 0–24.",
      );
    } else if (err.includes("tou_energy_rates_per_kwh")) {
      guidance.push(
        "🕐 A raw TOU array must have 8760/17520/35040 values. Prefer the 'tou_energy_schedule' shorthand and let the server compile it.",
      );
    } else if (err.includes("ElectricTariff") || err.includes("urdb_label")) {
      guidance.push(
        "💵 Pick a rate mode: blended (blended_annual_energy_rate + blended_annual_demand_rate), monthly (monthly_energy_rates), time-of-use (tou_energy_schedule), or a URDB label (urdb_label — use searchUrdbRates to find one). See getScenarioHelp('tariff').",
      );
    }
  }
  // Dedupe while preserving first-occurrence order for stable, deterministic output.
  return [...new Set(guidance)];
}
