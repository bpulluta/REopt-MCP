/** ElectricLoad module: how the building's electricity demand is described.
 *
 * REopt needs a *load source* (a profile) and, usually, a *scaler* (how much energy).
 * This module supports every way the hosted REopt API accepts a load, plus one
 * server-side convenience shorthand:
 *
 *   Sources (pick one):
 *     - doe_reference_name              a DOE commercial reference building profile
 *     - blended_doe_reference_names     a weighted blend of reference profiles
 *     - loads_kw                        an explicit 8760/17520/35040-value profile
 *     - loads_csv  (shorthand)          a path to a CSV of hourly kW; the SERVER reads
 *                                       it and compiles it into loads_kw (the hosted
 *                                       API cannot read files on your machine, so the
 *                                       REopt.jl `path_to_csv` key does not work here)
 *
 *   Scalers (optional; scale the profile's total):
 *     - annual_kwh                      one annual total
 *     - monthly_totals_kwh             12 monthly totals (Jan..Dec)
 *     - monthly_peaks_kw               12 monthly peak demands (Jan..Dec)
 *
 * All keys except `loads_csv` are verified against dev-docs/reoptjl_docs/bundles/inputs.md.
 */

import { readFileSync } from "node:fs";

import { isDict, isNumber, type Dict } from "../guards.js";
import { VALID_DOE_REFERENCE_NAMES } from "../constants.js";
import { quotedList } from "../format.js";
import {
  VALID_TIMESERIES_LENGTHS,
  resolveTimeStepsPerHour,
} from "./helpers.js";
import type { ScenarioModule } from "./types.js";

// Canonical REopt.jl ElectricLoad keys (from inputs.md). `path_to_csv` is handled
// specially below (unsupported by the hosted API), so it is intentionally absent.
const VALID_ELECTRIC_LOAD_KEYS: ReadonlySet<string> = new Set([
  "doe_reference_name",
  "blended_doe_reference_names",
  "blended_doe_reference_percents",
  "loads_kw",
  "normalize_and_scale_load_profile_input",
  "year",
  "city",
  "annual_kwh",
  "monthly_totals_kwh",
  "monthly_peaks_kw",
  "critical_loads_kw",
  "loads_kw_is_net",
  "critical_loads_kw_is_net",
  "critical_load_fraction",
  "operating_reserve_required_fraction",
  "min_load_met_annual_fraction",
]);

// Server-side shorthands compiled into canonical keys by `expand` (NOT sent to REopt).
const LOAD_SHORTHAND_KEYS: ReadonlySet<string> = new Set(["loads_csv"]);

// A load source is any one of these (loads_csv compiles to loads_kw).
const LOAD_SOURCE_KEYS = [
  "doe_reference_name",
  "blended_doe_reference_names",
  "loads_kw",
  "loads_csv",
] as const;

const SCALER_KEYS = ["annual_kwh", "monthly_totals_kwh", "monthly_peaks_kw"] as const;

const MONTHLY_LENGTH = 12;

export class ElectricLoadModule implements ScenarioModule {
  readonly key = "ElectricLoad";
  readonly kind = "core" as const;
  readonly label = "Electric Load";
  readonly required = true;

  example(): Dict {
    return { doe_reference_name: "MediumOffice", annual_kwh: 500000 };
  }

  /** Compile the `loads_csv` path shorthand into an explicit `loads_kw` array. */
  expand(section: Dict, _scenario: Dict): Dict {
    const csv = section.loads_csv;
    if (typeof csv !== "string" || !csv.trim()) return section;

    let loads: number[];
    try {
      loads = readLoadsCsv(csv);
    } catch {
      return section; // validate() surfaces the specific read/parse error
    }

    const expanded: Dict = {};
    for (const [k, v] of Object.entries(section)) {
      if (k !== "loads_csv") expanded[k] = v;
    }
    expanded.loads_kw = loads;
    return expanded;
  }

  validate(section: unknown, scenario: Dict): string[] {
    if (!isDict(section)) return ["ElectricLoad must be an object"];
    const load = section;
    const errors: string[] = [];

    rejectPathToCsv(load, errors);
    validateKnownKeys(load, errors);
    validateSource(load, errors);
    validateDoeName(load, errors);
    validateBlendedDoe(load, errors);
    validateLoadsKw(load, scenario, errors);
    validateCsvShorthand(load, scenario, errors);
    validateScalers(load, errors);
    validateFractions(load, errors);
    validateBooleans(load, errors);
    return errors;
  }

  warnings(section: unknown, _scenario: Dict): string[] {
    if (!isDict(section)) return [];
    const load = section;
    const warnings: string[] = [];

    const usesProfileInput = "loads_kw" in load || "loads_csv" in load;
    const scaler = SCALER_KEYS.find((k) => k in load);
    if (usesProfileInput && scaler && load.normalize_and_scale_load_profile_input !== true) {
      warnings.push(
        `ElectricLoad has an explicit profile (loads_kw/loads_csv) and a scaler ` +
          `(${scaler}), but normalize_and_scale_load_profile_input is not true, so ` +
          `${scaler} is ignored and the profile is used as-is.`,
      );
    }

    const usesReference =
      "doe_reference_name" in load || "blended_doe_reference_names" in load;
    if (usesReference && !scaler) {
      warnings.push(
        "ElectricLoad has a reference profile but no annual_kwh / monthly_totals_kwh, " +
          "so REopt uses the reference building's built-in annual energy, which may " +
          "not match the site's actual usage.",
      );
    }
    return warnings;
  }
}

/** The hosted REopt API cannot read files on the user's machine. */
function rejectPathToCsv(load: Dict, errors: string[]): void {
  if ("path_to_csv" in load) {
    errors.push(
      "ElectricLoad 'path_to_csv' is not supported by the hosted REopt API (it " +
        "cannot read local files). Use the 'loads_csv' shorthand instead — the " +
        "server reads the CSV and sends loads_kw.",
    );
  }
}

function validateKnownKeys(load: Dict, errors: string[]): void {
  const allowed = new Set([...VALID_ELECTRIC_LOAD_KEYS, ...LOAD_SHORTHAND_KEYS]);
  const unknown = Object.keys(load).filter(
    (k) => !allowed.has(k) && k !== "path_to_csv", // path_to_csv reported separately
  );
  if (unknown.length > 0) {
    errors.push(
      `ElectricLoad contains unsupported keys: ${quotedList([...unknown].sort())}`,
    );
  }
}

function validateSource(load: Dict, errors: string[]): void {
  const hasSource = LOAD_SOURCE_KEYS.some((k) => {
    const v = load[k];
    if (k === "doe_reference_name" || k === "loads_csv") {
      return typeof v === "string" && v.trim().length > 0;
    }
    return Array.isArray(v) && v.length > 0;
  });
  if (!hasSource) {
    errors.push(
      "ElectricLoad needs a load source: doe_reference_name, " +
        "blended_doe_reference_names, loads_kw, or loads_csv.",
    );
  }
}

function validateDoeName(load: Dict, errors: string[]): void {
  if (!("doe_reference_name" in load)) return;
  if (!VALID_DOE_REFERENCE_NAMES.has(load.doe_reference_name as string)) {
    errors.push(
      `Invalid doe_reference_name: '${load.doe_reference_name}'. Must be one of: ${[
        ...VALID_DOE_REFERENCE_NAMES,
      ]
        .sort()
        .join(", ")}`,
    );
  }
}

function validateBlendedDoe(load: Dict, errors: string[]): void {
  const names = load.blended_doe_reference_names;
  const percents = load.blended_doe_reference_percents;
  if (
    (names === undefined || names === null) &&
    (percents === undefined || percents === null)
  ) {
    return;
  }

  if (!Array.isArray(names) || !Array.isArray(percents)) {
    errors.push(
      "ElectricLoad blended DOE inputs must include both list fields: 'blended_doe_reference_names' and 'blended_doe_reference_percents'",
    );
    return;
  }
  if (names.length !== percents.length) {
    errors.push("ElectricLoad blended DOE inputs must have matching lengths");
    return;
  }
  if (names.length === 0) {
    errors.push("ElectricLoad blended DOE inputs cannot be empty when provided");
    return;
  }

  const invalidNames = names.filter(
    (name) => !VALID_DOE_REFERENCE_NAMES.has(name as string),
  );
  if (invalidNames.length > 0) {
    errors.push(
      `ElectricLoad blended_doe_reference_names contains invalid entries: ${quotedList(
        invalidNames.map((n) => String(n)),
      )}`,
    );
  }

  if (!percents.every((p) => typeof p === "number")) {
    errors.push(
      "ElectricLoad blended_doe_reference_percents must be numeric values",
    );
  } else {
    const total = percents.reduce((a, b) => a + (b as number), 0);
    if (Math.abs(total - 1.0) > 1e-6) {
      errors.push("ElectricLoad blended_doe_reference_percents must sum to 1.0");
    }
  }
}

function validateLoadsKw(load: Dict, scenario: Dict, errors: string[]): void {
  for (const key of ["loads_kw", "critical_loads_kw"]) {
    if (!(key in load)) continue;
    const value = load[key];
    if (!Array.isArray(value)) {
      errors.push(`ElectricLoad '${key}' must be a list of numbers`);
      continue;
    }
    const lengthError = timeseriesLengthError(key, value, scenario);
    if (lengthError) errors.push(lengthError);
    if (!value.every((n) => isNumber(n) && n >= 0)) {
      errors.push(`ElectricLoad '${key}' must contain only non-negative numbers`);
    }
  }
}

function validateCsvShorthand(load: Dict, scenario: Dict, errors: string[]): void {
  if (!("loads_csv" in load)) return;
  const csv = load.loads_csv;
  if (typeof csv !== "string" || !csv.trim()) {
    errors.push("ElectricLoad 'loads_csv' must be a non-empty file path string");
    return;
  }
  let loads: number[];
  try {
    loads = readLoadsCsv(csv);
  } catch (error) {
    errors.push(
      `ElectricLoad 'loads_csv' could not be read: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
    return;
  }
  const lengthError = timeseriesLengthError("loads_csv", loads, scenario);
  if (lengthError) errors.push(lengthError);
}

function timeseriesLengthError(
  key: string,
  value: unknown[],
  scenario: Dict,
): string | null {
  if (!VALID_TIMESERIES_LENGTHS.has(value.length)) {
    return (
      `ElectricLoad '${key}' must have length 8760, 17520, or 35040 ` +
      `(time steps per year), got ${value.length}`
    );
  }
  const expected = 8760 * resolveTimeStepsPerHour(scenario);
  if (value.length !== expected) {
    return (
      `ElectricLoad '${key}' has length ${value.length} but ` +
      `Settings.time_steps_per_hour implies ${expected} time steps per year`
    );
  }
  return null;
}

function validateScalers(load: Dict, errors: string[]): void {
  if ("annual_kwh" in load) {
    if (!isNumber(load.annual_kwh) || (load.annual_kwh as number) <= 0) {
      errors.push("ElectricLoad 'annual_kwh' must be a positive number");
    }
  }
  for (const key of ["monthly_totals_kwh", "monthly_peaks_kw"]) {
    if (!(key in load)) continue;
    const value = load[key];
    if (!Array.isArray(value) || value.length !== MONTHLY_LENGTH) {
      errors.push(
        `ElectricLoad '${key}' must have exactly ${MONTHLY_LENGTH} values (Jan..Dec)`,
      );
      continue;
    }
    if (!value.every((n) => isNumber(n) && n >= 0)) {
      errors.push(`ElectricLoad '${key}' must contain only non-negative numbers`);
    }
  }
}

function validateFractions(load: Dict, errors: string[]): void {
  for (const key of [
    "critical_load_fraction",
    "operating_reserve_required_fraction",
    "min_load_met_annual_fraction",
  ]) {
    if (!(key in load)) continue;
    const v = load[key];
    if (!isNumber(v) || !(v >= 0 && v <= 1)) {
      errors.push(`ElectricLoad '${key}' must be a number between 0 and 1`);
    }
  }
}

function validateBooleans(load: Dict, errors: string[]): void {
  for (const key of [
    "normalize_and_scale_load_profile_input",
    "loads_kw_is_net",
    "critical_loads_kw_is_net",
  ]) {
    if (key in load && typeof load[key] !== "boolean") {
      errors.push(`ElectricLoad '${key}' must be a boolean`);
    }
  }
}

/** Read a CSV of hourly kW values and return them as a number array.
 *
 * Accepts one numeric value per row (a single column), with an optional non-numeric
 * header row. Throws a clear Error on any non-numeric data cell so `validate` can
 * report it. Deliberately strict: multi-column rows are rejected to avoid silently
 * picking the wrong column. */
export function readLoadsCsv(path: string): number[] {
  const text = readFileSync(path, "utf8");
  const rows = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
  if (rows.length === 0) throw new Error("file is empty");

  // Drop a single non-numeric header row if present.
  if (rows.length > 0 && Number.isNaN(Number(rows[0]))) rows.shift();

  const loads: number[] = [];
  rows.forEach((row, i) => {
    if (row.includes(",")) {
      throw new Error(
        `row ${i + 1} has multiple columns; provide one kW value per row`,
      );
    }
    const value = Number(row);
    if (!Number.isFinite(value)) {
      throw new Error(`row ${i + 1} ('${row}') is not a number`);
    }
    loads.push(value);
  });
  return loads;
}
