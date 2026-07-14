/** URDB (Utility Rate Database) search via the OpenEI API.
 *
 * Users almost never know their `urdb_label` but do know their utility. This helper
 * searches URDB and returns candidate rates so the agent can present them and let the
 * user pick a label to drop into `ElectricTariff.urdb_label`.
 */

import { OPENEI_API_KEY, URDB_API_BASE_URL } from "./config.js";
import { httpGetJson } from "./http.js";

// Sectors accepted by the URDB API.
export const VALID_URDB_SECTORS: ReadonlySet<string> = new Set([
  "Residential",
  "Commercial",
  "Industrial",
  "Lighting",
]);

export interface UrdbRate {
  label: unknown;
  name: unknown;
  utility: unknown;
  sector: unknown;
  approved: unknown;
  /** True when the rate has no end date or ends in the future. */
  active: boolean;
  /** Human-readable effective span, e.g. "2022-09-22 – present". */
  effective_period: string;
  /** Browser link to view/verify the rate on OpenEI. */
  view_url: string;
}

/** URDB timestamps are seconds since epoch. Convert one to a UTC YYYY-MM-DD
 * string, or null when it is missing/unparseable. */
function epochToIsoDate(value: unknown): string | null {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    return null;
  }
  return new Date(value * 1000).toISOString().slice(0, 10);
}

/** OpenEI rate-view URL for a label, used when the API omits `uri`. */
export function urdbViewUrl(label: unknown): string {
  return `https://apps.openei.org/USURDB/rate/view/${String(label ?? "")}`;
}

/** Reduce a raw URDB record to the fields useful for choosing a rate, adding
 * derived active/effective_period/view_url so the user can judge whether it is
 * the current tariff and open it to verify. */
function trimItem(item: Record<string, unknown>): UrdbRate {
  const start = epochToIsoDate(item.startdate);
  const end = epochToIsoDate(item.enddate);

  return {
    label: item.label,
    name: item.name,
    utility: item.utility,
    sector: item.sector,
    approved: item.approved,
    active: isActive(item),
    effective_period: `${start ?? "unknown"} – ${end ?? "present"}`,
    view_url:
      typeof item.uri === "string" && item.uri.trim()
        ? item.uri
        : urdbViewUrl(item.label),
  };
}

/** True when a rate has no end date or ends in the future. */
function isActive(item: Record<string, unknown>): boolean {
  const end = item.enddate;
  if (typeof end !== "number" || !Number.isFinite(end) || end <= 0) return true;
  return end * 1000 > Date.now();
}

/** Rank so the current tariff surfaces first: active before expired, then the
 * sector's default (most-common current) rate, then most recent start date, then
 * expert-approved before unverified. */
function compareRates(
  a: Record<string, unknown>,
  b: Record<string, unknown>,
): number {
  const byActive = (isActive(b) ? 1 : 0) - (isActive(a) ? 1 : 0);
  if (byActive !== 0) return byActive;

  const byDefault = (b.is_default === true ? 1 : 0) - (a.is_default === true ? 1 : 0);
  if (byDefault !== 0) return byDefault;

  const aStart = typeof a.startdate === "number" ? a.startdate : 0;
  const bStart = typeof b.startdate === "number" ? b.startdate : 0;
  if (aStart !== bStart) return bStart - aStart;

  return (b.approved === true ? 1 : 0) - (a.approved === true ? 1 : 0);
}

export interface UrdbSearchOptions {
  utility?: string | null;
  address?: string | null;
  sector?: string | null;
  rate_name?: string | null;
  limit?: number;
}

/** Search URDB and return a trimmed list of candidate rates.
 *
 * Provide `utility` (name) and/or `address` (address or ZIP). `rate_name` filters
 * the returned candidates by substring on the client side.
 */
export async function searchUrdbRates(
  options: UrdbSearchOptions = {},
): Promise<UrdbRate[]> {
  const { utility, address, sector, rate_name, limit = 10 } = options;
  const displayLimit = Math.max(1, Math.min(Math.trunc(limit), 50));

  if (!OPENEI_API_KEY) {
    throw new Error(
      "URDB search needs an API key. Set OPENEI_API_KEY (or NLR_API_KEY, which " +
        "URDB accepts) in your environment/.env.",
    );
  }
  if (!utility && !address) {
    throw new RangeError(
      "Provide at least one of 'utility' or 'address' to search.",
    );
  }

  // URDB accepts only these four sector values (docs: Request Parameters →
  // sector). Normalize case so "residential" matches "Residential" instead of
  // reaching the API as an invalid value and coming back a 400.
  let normalizedSector: string | undefined;
  if (sector) {
    const canonical =
      sector.charAt(0).toUpperCase() + sector.slice(1).toLowerCase();
    if (!VALID_URDB_SECTORS.has(canonical)) {
      throw new RangeError(
        `Invalid sector '${sector}'. Valid options: ${[...VALID_URDB_SECTORS].join(", ")}.`,
      );
    }
    normalizedSector = canonical;
  }

  // URDB stores every historical version of a rate; in default order the current
  // tariff is buried at the end (for some utilities hundreds deep). direction=desc
  // sorts newest-first server-side, so a small page returns the current rates
  // instead of a wall of expired ones — far less to transfer and parse. When a
  // rate_name filter is set we pull a wider page (still tiny) so the substring has
  // more newest-first candidates to match against, then slice back to displayLimit.
  const fetchLimit = rate_name ? 50 : displayLimit;
  const params: Record<string, string | number | undefined> = {
    version: "latest",
    format: "json",
    detail: "minimal",
    direction: "desc",
    api_key: OPENEI_API_KEY,
    limit: fetchLimit,
  };
  if (utility) params.ratesforutility = utility;
  if (address) params.address = address;
  if (normalizedSector) params.sector = normalizedSector;

  const payload = (await httpGetJson(
    URDB_API_BASE_URL,
    params,
    "URDB API",
    "URDB_API_BASE_URL",
  )) as Record<string, unknown>;

  if (payload && typeof payload === "object" && payload.error) {
    throw new Error(`URDB API error: ${String(payload.error)}`);
  }

  const rawItems = Array.isArray(payload?.items) ? payload.items : [];
  let records = rawItems.filter(
    (item): item is Record<string, unknown> =>
      item !== null && typeof item === "object" && !Array.isArray(item),
  );

  if (rate_name) {
    const needle = rate_name.toLowerCase();
    records = records.filter((row) =>
      String(row.name ?? "").toLowerCase().includes(needle),
    );
  }

  // The API page is already newest-first; this just guarantees active rates sort
  // above any expired one that happens to share a recent start date.
  records.sort(compareRates);
  return records.slice(0, displayLimit).map(trimItem);
}
