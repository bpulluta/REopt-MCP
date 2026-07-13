/** Number- and list-formatting helpers for the markdown result summaries. */

/** Coerce an arbitrary value to a finite number, else the fallback. */
export function num(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

/** Format with one decimal place, e.g. `12.3`. */
export function fixed1(value: unknown): string {
  return num(value).toFixed(1);
}

/** Format with two decimal places, e.g. `12.34`. */
export function fixed2(value: unknown): string {
  return num(value).toFixed(2);
}

/** Thousands-separated integer, e.g. `1,234`. */
export function comma0(value: unknown): string {
  return num(value).toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

/** Round to `digits` decimal places. */
export function roundTo(value: number, digits: number): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

/** Render strings as a quoted, bracketed list — e.g. `['a', 'b']` — for error messages. */
export function quotedList(items: string[]): string {
  return `[${items.map((s) => `'${s}'`).join(", ")}]`;
}

