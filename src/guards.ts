/** Shared runtime type guards used across modules.
 *
 * These were previously duplicated in index.ts, validation.ts, tariff.ts,
 * sections.ts, and summaries.ts. Keep a single copy here so every module agrees
 * on what counts as a dict, a real number, etc.
 */

export type Dict = Record<string, unknown>;

/** A non-null, non-array object. */
export function isDict(value: unknown): value is Dict {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** A finite real number, excluding boolean (which is `typeof "number"`? no — but
 * guards against NaN/Infinity and keeps intent explicit). */
export function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

/** A string with at least one non-whitespace character. */
export function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

/** Truthiness check: empty dict/list/string, 0, null, and false are all falsy. */
export function isTruthy(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  if (typeof value === "string") return value.length > 0;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "object") return Object.keys(value).length > 0;
  return true;
}
