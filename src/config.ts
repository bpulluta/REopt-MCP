/** Runtime configuration for REopt MCP. */

/**
 * Read an env var, trim it, and fall back to a default when empty/whitespace.
 */
function envOr(name: string, fallback: string): string {
  const value = (process.env[name] ?? "").trim();
  return value || fallback;
}

export const REOPT_API_BASE_URL: string = envOr(
  "REOPT_API_BASE_URL",
  "https://developer.nlr.gov/api/reopt/stable",
);

export const NLR_API_KEY: string = (process.env.NLR_API_KEY ?? "").trim();

// URDB (Utility Rate Database) lives at OpenEI and accepts the same NLR /
// api.data.gov developer key, so OPENEI_API_KEY falls back to NLR_API_KEY.
export const URDB_API_BASE_URL: string = envOr(
  "URDB_API_BASE_URL",
  "https://api.openei.org/utility_rates",
);

export const OPENEI_API_KEY: string =
  (process.env.OPENEI_API_KEY ?? "").trim() || NLR_API_KEY;

/**
 * Skip TLS certificate verification for outbound API calls when
 * REOPT_TLS_INSECURE is truthy.
 *
 * Some networks (e.g. a corporate Netskope/Zscaler TLS-inspecting proxy)
 * re-sign HTTPS with a private CA that lives in the OS trust store but NOT in
 * Node's bundled CA store. `curl` trusts it; Node's `fetch` (undici) throws
 * "self-signed certificate in certificate chain". The secure fix is to launch
 * Node with `--use-system-ca` (Node >= 22.15) so it reads the OS store — see
 * .env.example. This flag is the blunt escape hatch for when that isn't
 * available. It disables verification for the whole process, so only enable it
 * on trusted networks.
 */
export const TLS_INSECURE: boolean = /^(1|true|yes|on)$/i.test(
  (process.env.REOPT_TLS_INSECURE ?? "").trim(),
);

/**
 * Apply the insecure-TLS escape hatch. undici reads
 * NODE_TLS_REJECT_UNAUTHORIZED per connection, so setting it here — before any
 * fetch runs — is enough; no restart needed. Called once at startup.
 */
export function applyTlsConfig(): void {
  if (TLS_INSECURE && process.env.NODE_TLS_REJECT_UNAUTHORIZED !== "0") {
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
    // stderr so it never corrupts the stdio JSON-RPC stream.
    console.error(
      "Warning: REOPT_TLS_INSECURE is set — TLS certificate verification is " +
        "DISABLED for all outbound requests. Use only on trusted networks.",
    );
  }
}

/** Print a startup warning when the API key is missing. */
export function warnIfUnconfigured(): void {
  if (!NLR_API_KEY) {
    // stderr so it never corrupts the stdio JSON-RPC stream.
    console.error("Warning: NLR_API_KEY is not set.");
  }
}
