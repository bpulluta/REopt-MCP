/** Small shared helpers for modules: output summaries and timeseries handling. */

import { isDict, type Dict } from "../guards.js";
import { num } from "../format.js";

/** Valid lengths for a full-year timeseries at 1, 2, or 4 time steps per hour. */
export const VALID_TIMESERIES_LENGTHS: ReadonlySet<number> = new Set([
  8760, 17520, 35040,
]);

const VALID_TIME_STEPS_PER_HOUR: ReadonlySet<number> = new Set([1, 2, 4]);

/** Resolve Settings.time_steps_per_hour, defaulting to 1. */
export function resolveTimeStepsPerHour(scenario: Dict): number {
  const settings = scenario.Settings;
  if (isDict(settings)) {
    const steps = settings.time_steps_per_hour ?? 1;
    if (typeof steps === "number" && VALID_TIME_STEPS_PER_HOUR.has(steps)) {
      return steps;
    }
  }
  return 1;
}

/** A technology's output sub-block, or an empty dict when absent/malformed. */
export function techBlock(outputs: Dict, key: string): Dict {
  const block = outputs[key];
  return isDict(block) ? block : {};
}

/** Default "was this technology recommended?" heuristic: size_kw > 0. */
export function defaultIsPresent(outputs: Dict, key: string): boolean {
  const block = outputs[key];
  return isDict(block) && num(block.size_kw) > 0;
}

/** Capacity factor (%) from annual production and rated size. */
export function capacityFactor(block: Dict): number {
  const produced =
    num(block.annual_energy_produced_kwh) ||
    num(block.average_annual_energy_produced_kwh);
  const sizeKw = num(block.size_kw);
  return sizeKw > 0 ? (produced / (sizeKw * 8760)) * 100 : 0;
}
