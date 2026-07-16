/** Settings module: grid mode and simulation resolution.
 *
 * Also exposes `readOffGridFlag`, which the top-level validator needs to enforce
 * the cross-section rule that ElectricTariff is required on-grid and forbidden
 * off-grid.
 */

import { isDict, isTruthy, type Dict } from "../guards.js";
import type { ScenarioModule } from "./types.js";

const VALID_TIME_STEPS_PER_HOUR: ReadonlySet<number> = new Set([1, 2, 4]);

/** Read Settings.off_grid_flag, defaulting to false. Never throws or reports —
 * `validate` surfaces malformed values. */
export function readOffGridFlag(scenario: Dict): boolean {
  const settings = scenario.Settings;
  if (isDict(settings) && typeof settings.off_grid_flag === "boolean") {
    return settings.off_grid_flag;
  }
  return false;
}

export class SettingsModule implements ScenarioModule {
  readonly key = "Settings";
  readonly kind = "core" as const;
  readonly label = "Settings";

  validate(section: unknown): string[] {
    // Preserve prior behavior: an empty/absent Settings is fine.
    if (!isTruthy(section)) return [];
    if (!isDict(section)) return ["Settings must be an object when provided"];

    const errors: string[] = [];
    if ("off_grid_flag" in section && typeof section.off_grid_flag !== "boolean") {
      errors.push("Settings 'off_grid_flag' must be a boolean");
    }
    if (
      "time_steps_per_hour" in section &&
      !(
        typeof section.time_steps_per_hour === "number" &&
        VALID_TIME_STEPS_PER_HOUR.has(section.time_steps_per_hour)
      )
    ) {
      errors.push("Settings 'time_steps_per_hour' must be one of 1, 2, or 4");
    }
    return errors;
  }
}
