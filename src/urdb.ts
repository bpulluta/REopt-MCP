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
  startdate: unknown;
  uri: unknown;
}

/** Reduce a raw URDB record to the fields useful for choosing a rate. */
function trimItem(item: Record<string, unknown>): UrdbRate {
  return {
    label: item.label,
    name: item.name,
    utility: item.utility,
    sector: item.sector,
    startdate: item.startdate,
    uri: item.uri,
  };
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

  const params: Record<string, string | number | undefined> = {
    version: "latest",
    format: "json",
    detail: "minimal",
    api_key: OPENEI_API_KEY,
    limit: Math.max(1, Math.min(Math.trunc(limit), 50)),
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
  let results = rawItems
    .filter((item): item is Record<string, unknown> =>
      item !== null && typeof item === "object" && !Array.isArray(item),
    )
    .map(trimItem);

  if (rate_name) {
    const needle = rate_name.toLowerCase();
    results = results.filter((row) =>
      String(row.name ?? "").toLowerCase().includes(needle),
    );
  }
  return results;
}
