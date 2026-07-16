/** Site module: geographic coordinates only (no address/city fields). */

import { isDict, isNumber, type Dict } from "../guards.js";
import { INVALID_SITE_FIELDS, LATITUDE_RANGE, LONGITUDE_RANGE } from "../constants.js";
import type { ScenarioModule } from "./types.js";

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

export class SiteModule implements ScenarioModule {
  readonly key = "Site";
  readonly kind = "core" as const;
  readonly label = "Site";
  readonly required = true;

  example(): Dict {
    return { latitude: 39.7407, longitude: -104.989 };
  }

  validate(section: unknown): string[] {
    if (!isDict(section)) return ["Site must be an object"];
    const errors: string[] = [];
    const invalidFields = Object.keys(section).filter((k) =>
      INVALID_SITE_FIELDS.has(k),
    );
    if (invalidFields.length > 0) {
      errors.push(
        `Site contains invalid fields: ${bracedList(invalidFields)}. Only use latitude/longitude.`,
      );
    }
    validateCoordinate(section, "latitude", LATITUDE_RANGE, errors);
    validateCoordinate(section, "longitude", LONGITUDE_RANGE, errors);
    return errors;
  }
}
