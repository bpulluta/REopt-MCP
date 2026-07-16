/** ElectricTariff module: shorthand expansion, validation, and the TOU compiler.
 *
 * The reference implementation of the ScenarioModule contract. All
 * ElectricTariff-specific rate logic (and its constants) live here so other
 * sections can follow the same expand/validate/warnings/example shape without
 * touching the registry.
 */

import { isDict, isNumber, type Dict } from "../guards.js";
import { quotedList } from "../format.js";
import type { ScenarioModule } from "./types.js";

// --- ElectricTariff constants (module-local) --------------------------------

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
// submission. These are NOT sent to REopt; they are expanded by `expand` below.
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

const VALID_DAY_FILTERS = ["all", "weekday", "weekend"];
const VALID_TIME_STEPS_PER_HOUR: ReadonlySet<number> = new Set([1, 2, 4]);

/** Reference year used to align the TOU schedule with weekdays/weekends. */
function resolveYear(scenario: Dict): number {
  const load = scenario.ElectricLoad;
  if (isDict(load) && Number.isInteger(load.year)) {
    return load.year as number;
  }
  return DEFAULT_RATE_SCHEDULE_YEAR;
}

function resolveTimeStepsPerHour(scenario: Dict): number {
  const settings = scenario.Settings;
  if (isDict(settings)) {
    const steps = settings.time_steps_per_hour ?? 1;
    if (typeof steps === "number" && VALID_TIME_STEPS_PER_HOUR.has(steps)) {
      return steps;
    }
  }
  return 1;
}

/** Days in a given 1-based month (Feb 29 is skipped separately). */
function daysInMonth(year: number, month: number): number {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

/** True when the given date is a Saturday or Sunday. */
function isWeekendDay(year: number, month: number, day: number): boolean {
  const dow = new Date(Date.UTC(year, month - 1, day)).getUTCDay(); // 0=Sun..6=Sat
  return dow === 0 || dow === 6;
}

interface CompiledPeriod {
  rate: number;
  months: Set<number>;
  dayFilter: string;
  hourRanges: number[][];
}

/** Expand a human-friendly TOU schedule into a full-year hourly rate array.
 *
 * The returned array is ordered chronologically from Jan 1 00:00 and has length
 * 8760 * time_steps_per_hour. Each hour takes the rate of the LAST matching period,
 * or the schedule's `default_rate` when no period matches. Leap days (Feb 29) are
 * skipped so the array is always a non-leap 8760-hour year.
 *
 * Throws on structurally invalid input; the handler catches and leaves the section
 * unchanged so `validate` can surface a clear error.
 */
export function compileTouSchedule(
  schedule: Dict,
  opts: { year: number; timeStepsPerHour: number },
): number[] {
  const { year, timeStepsPerHour } = opts;

  const rawDefault = schedule.default_rate ?? 0.0;
  if (!isNumber(rawDefault)) {
    throw new TypeError("tou_energy_schedule.default_rate must be a number");
  }
  const defaultRate = rawDefault;

  const periodsRaw = Array.isArray(schedule.periods) ? schedule.periods : [];
  const compiledPeriods: CompiledPeriod[] = [];
  for (const period of periodsRaw) {
    if (!isDict(period)) {
      throw new TypeError("tou_energy_schedule.periods entries must be objects");
    }
    if (!isNumber(period.rate)) {
      throw new TypeError("tou_energy_schedule period.rate must be a number");
    }
    const months =
      Array.isArray(period.months) && period.months.length > 0
        ? (period.months as number[])
        : range(1, 13);
    const dayFilter =
      typeof period.days === "string" ? period.days : "all";
    const hourRanges =
      Array.isArray(period.hours) && period.hours.length > 0
        ? (period.hours as number[][])
        : [[0, 24]];
    compiledPeriods.push({
      rate: period.rate,
      months: new Set(months),
      dayFilter,
      hourRanges,
    });
  }

  const hourly: number[] = [];
  for (let month = 1; month <= 12; month++) {
    const days = daysInMonth(year, month);
    for (let day = 1; day <= days; day++) {
      if (month === 2 && day === 29) continue; // keep a 365-day / 8760-hour year
      const weekend = isWeekendDay(year, month, day);
      for (let hour = 0; hour < 24; hour++) {
        let rate = defaultRate;
        for (const p of compiledPeriods) {
          if (!p.months.has(month)) continue;
          if (p.dayFilter === "weekday" && weekend) continue;
          if (p.dayFilter === "weekend" && !weekend) continue;
          const inWindow = p.hourRanges.some(
            ([start, end]) => start <= hour && hour < end,
          );
          if (!inWindow) continue;
          rate = p.rate; // last matching period wins
        }
        hourly.push(rate);
      }
    }
  }

  if (timeStepsPerHour > 1) {
    const expanded: number[] = [];
    for (const value of hourly) {
      for (let i = 0; i < timeStepsPerHour; i++) expanded.push(value);
    }
    return expanded;
  }
  return hourly;
}

function range(start: number, stop: number): number[] {
  const out: number[] = [];
  for (let i = start; i < stop; i++) out.push(i);
  return out;
}

export class ElectricTariffModule implements ScenarioModule {
  readonly key = "ElectricTariff";
  readonly kind = "section" as const;
  readonly label = "Electric Tariff";

  example(): Dict {
    return { blended_annual_energy_rate: 0.12, blended_annual_demand_rate: 15.0 };
  }

  /** Compile the `tou_energy_schedule` shorthand into REopt's hourly array. */
  expand(section: Dict, scenario: Dict): Dict {
    const schedule = section.tou_energy_schedule;
    if (schedule === undefined || schedule === null) return section;
    if (!isDict(schedule)) return section;

    let compiled: number[];
    try {
      compiled = compileTouSchedule(schedule, {
        year: resolveYear(scenario),
        timeStepsPerHour: resolveTimeStepsPerHour(scenario),
      });
    } catch {
      return section; // validate() will surface the malformed shorthand
    }

    const expanded: Dict = {};
    for (const [k, v] of Object.entries(section)) {
      if (k !== "tou_energy_schedule") expanded[k] = v;
    }
    expanded.tou_energy_rates_per_kwh = compiled;
    return expanded;
  }

  validate(section: unknown, scenario: Dict): string[] {
    const errors: string[] = [];
    if (!isDict(section)) return ["ElectricTariff must be an object"];

    validateAliases(section, errors);
    validateKnownKeys(section, errors);
    validateEnergyRateSource(section, errors);
    validateBlendedRates(section, errors);
    validateMonthlyRates(section, errors);
    validateTouArray(section, scenario, errors);
    validateTouSchedule(section, errors);
    return errors;
  }

  warnings(section: unknown, _scenario: Dict): string[] {
    const warnings: string[] = [];
    if (!isDict(section)) return warnings;

    const hasUrdb = hasUrdbRate(section);
    const blendedOrCustom = [
      "blended_annual_energy_rate",
      "blended_annual_demand_rate",
      "monthly_energy_rates",
      "monthly_demand_rates",
      "tou_energy_rates_per_kwh",
      "tou_energy_schedule",
    ].some((key) => key in section);
    const addMonthly = section.add_monthly_rates_to_urdb_rate === true;
    const addTou = section.add_tou_energy_rates_to_urdb_rate === true;

    if (hasUrdb && blendedOrCustom && !(addMonthly || addTou)) {
      warnings.push(
        "ElectricTariff has both a URDB rate and custom/blended rates. REopt " +
          "uses only the URDB rate unless you set add_monthly_rates_to_urdb_rate " +
          "or add_tou_energy_rates_to_urdb_rate to true.",
      );
    }
    if (addMonthly && !hasUrdb) {
      warnings.push(
        "add_monthly_rates_to_urdb_rate is true but no urdb_label/urdb_response " +
          "is set, so it has no effect.",
      );
    }
    if (addTou && !hasUrdb) {
      warnings.push(
        "add_tou_energy_rates_to_urdb_rate is true but no urdb_label/urdb_response " +
          "is set, so it has no effect.",
      );
    }

    const hasDemandSource =
      hasUrdb ||
      ["blended_annual_demand_rate", "monthly_demand_rates"].some(
        (key) => key in section,
      );
    if (!hasDemandSource) {
      warnings.push(
        "No demand charge specified (blended_annual_demand_rate, " +
          "monthly_demand_rates, or a URDB rate). Demand charges will be $0, " +
          "which may understate utility costs.",
      );
    }
    return warnings;
  }
}

function hasUrdbRate(section: Dict): boolean {
  const label = section.urdb_label;
  if (typeof label === "string" && label.trim()) return true;
  const response = section.urdb_response;
  return isDict(response) && Object.keys(response).length > 0;
}

function validateAliases(section: Dict, errors: string[]): void {
  const used = Object.keys(section).filter(
    (k) => k in INVALID_ELECTRIC_TARIFF_ALIASES,
  );
  if (used.length > 0) {
    const sortedUsed = [...used].sort();
    const guidance = sortedUsed
      .map((bad) => `'${bad}' -> '${INVALID_ELECTRIC_TARIFF_ALIASES[bad]}'`)
      .join(", ");
    errors.push(
      `ElectricTariff contains invalid keys for REopt.jl: ${quotedList(sortedUsed)}. Use ${guidance}.`,
    );
  }
}

function validateKnownKeys(section: Dict, errors: string[]): void {
  const allowed = new Set([
    ...VALID_ELECTRIC_TARIFF_KEYS,
    ...TARIFF_SHORTHAND_KEYS,
  ]);
  const unknown = Object.keys(section).filter(
    (k) => !allowed.has(k) && !(k in INVALID_ELECTRIC_TARIFF_ALIASES),
  );
  if (unknown.length > 0) {
    errors.push(
      `ElectricTariff contains unsupported keys: ${quotedList([...unknown].sort())}`,
    );
  }
}

function validateEnergyRateSource(section: Dict, errors: string[]): void {
  const sources = [...TARIFF_ENERGY_RATE_SOURCE_KEYS].filter((k) => k in section);
  const valid = sources.filter((k) => rateSourceIsPresent(section, k));
  if (valid.length === 0) {
    errors.push(
      "ElectricTariff needs at least one energy-rate source: urdb_label, " +
        "urdb_response, blended_annual_energy_rate, monthly_energy_rates, " +
        "tou_energy_rates_per_kwh, or tou_energy_schedule.",
    );
  }
}

function rateSourceIsPresent(section: Dict, key: string): boolean {
  const value = section[key];
  if (key === "urdb_label") return typeof value === "string" && !!value.trim();
  if (key === "urdb_response")
    return isDict(value) && Object.keys(value).length > 0;
  if (key === "monthly_energy_rates" || key === "tou_energy_rates_per_kwh")
    return Array.isArray(value) && value.length > 0;
  if (key === "tou_energy_schedule")
    return isDict(value) && Object.keys(value).length > 0;
  return value !== null && value !== undefined; // blended_annual_energy_rate
}

function validateBlendedRates(section: Dict, errors: string[]): void {
  for (const key of ["blended_annual_energy_rate", "blended_annual_demand_rate"]) {
    if (key in section && (!isNumber(section[key]) || (section[key] as number) < 0)) {
      errors.push(`ElectricTariff '${key}' must be a non-negative number`);
    }
  }
}

function validateMonthlyRates(section: Dict, errors: string[]): void {
  for (const key of ["monthly_energy_rates", "monthly_demand_rates"]) {
    if (!(key in section)) continue;
    const value = section[key];
    if (!Array.isArray(value)) {
      errors.push(`ElectricTariff '${key}' must be a list`);
      continue;
    }
    if (value.length !== MONTHLY_RATE_LENGTH) {
      errors.push(
        `ElectricTariff '${key}' must have exactly ${MONTHLY_RATE_LENGTH} ` +
          `values (one per month), got ${value.length}`,
      );
      continue;
    }
    if (!value.every((rate) => isNumber(rate) && rate >= 0)) {
      errors.push(`ElectricTariff '${key}' must contain only non-negative numbers`);
    }
  }
}

function validateTouArray(section: Dict, scenario: Dict, errors: string[]): void {
  if (!("tou_energy_rates_per_kwh" in section)) return;
  const value = section.tou_energy_rates_per_kwh;
  if (!Array.isArray(value)) {
    errors.push("ElectricTariff 'tou_energy_rates_per_kwh' must be a list");
    return;
  }
  if (!VALID_TOU_ARRAY_LENGTHS.has(value.length)) {
    errors.push(
      "ElectricTariff 'tou_energy_rates_per_kwh' must have length 8760, 17520, " +
        `or 35040 (time steps per year), got ${value.length}`,
    );
    return;
  }
  const expected = 8760 * resolveTimeStepsPerHour(scenario);
  if (value.length !== expected) {
    errors.push(
      `ElectricTariff 'tou_energy_rates_per_kwh' has length ${value.length} but ` +
        `Settings.time_steps_per_hour implies ${expected} time steps per year`,
    );
  }
  if (!value.every((rate) => isNumber(rate) && rate >= 0)) {
    errors.push(
      "ElectricTariff 'tou_energy_rates_per_kwh' must contain only non-negative " +
        "numbers",
    );
  }
}

function validateTouSchedule(section: Dict, errors: string[]): void {
  if (!("tou_energy_schedule" in section)) return;
  const schedule = section.tou_energy_schedule;
  if (!isDict(schedule)) {
    errors.push("ElectricTariff 'tou_energy_schedule' must be an object");
    return;
  }

  if (
    "default_rate" in schedule &&
    (!isNumber(schedule.default_rate) || (schedule.default_rate as number) < 0)
  ) {
    errors.push(
      "ElectricTariff 'tou_energy_schedule.default_rate' must be a non-negative " +
        "number",
    );
  }

  const periods = schedule.periods;
  if (!Array.isArray(periods) || periods.length === 0) {
    errors.push(
      "ElectricTariff 'tou_energy_schedule.periods' must be a non-empty list",
    );
    return;
  }

  periods.forEach((period, index) => {
    const label = `tou_energy_schedule.periods[${index}]`;
    if (!isDict(period)) {
      errors.push(`ElectricTariff '${label}' must be an object`);
      return;
    }
    const rate = period.rate;
    if (!isNumber(rate) || (rate as number) < 0) {
      errors.push(`ElectricTariff '${label}.rate' must be a non-negative number`);
    }
    validatePeriodMonths(period.months, label, errors);
    validatePeriodDays(period.days, label, errors);
    validatePeriodHours(period.hours, label, errors);
  });
}

function validatePeriodMonths(
  months: unknown,
  label: string,
  errors: string[],
): void {
  if (months === undefined || months === null) return;
  if (
    !Array.isArray(months) ||
    !months.every((m) => Number.isInteger(m) && m >= 1 && m <= 12)
  ) {
    errors.push(
      `ElectricTariff '${label}.months' must be a list of integers 1-12`,
    );
  }
}

function validatePeriodDays(days: unknown, label: string, errors: string[]): void {
  if (days === undefined || days === null) return;
  if (typeof days !== "string" || !VALID_DAY_FILTERS.includes(days)) {
    errors.push(
      `ElectricTariff '${label}.days' must be one of ${quotedList([...VALID_DAY_FILTERS].sort())}`,
    );
  }
}

function validatePeriodHours(hours: unknown, label: string, errors: string[]): void {
  if (hours === undefined || hours === null) return;
  if (!Array.isArray(hours) || hours.length === 0) {
    errors.push(
      `ElectricTariff '${label}.hours' must be a non-empty list of ` +
        "[start, end) ranges",
    );
    return;
  }
  for (const window of hours) {
    if (
      !Array.isArray(window) ||
      window.length !== 2 ||
      !window.every((h) => Number.isInteger(h)) ||
      !(0 <= window[0] && window[0] < window[1] && window[1] <= 24)
    ) {
      errors.push(
        `ElectricTariff '${label}.hours' entries must be [start, end) with ` +
          "0 <= start < end <= 24",
      );
      return;
    }
  }
}
