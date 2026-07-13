/** Minimal fetch wrapper shared by the REopt and URDB clients.
 *
 * Auth for both APIs is an `api_key` **query param**, not a header. Requests use
 * a 30s timeout. Network failures become a friendly error message; non-2xx
 * responses become an {@link HttpStatusError} carrying the status + body so tool
 * handlers can branch on the HTTP status.
 */

const TIMEOUT_MS = 30_000;

/** Raised for a non-2xx response. */
export class HttpStatusError extends Error {
  constructor(
    readonly status: number,
    readonly body: string,
  ) {
    super(`HTTP ${status}`);
    this.name = "HttpStatusError";
  }
}

type QueryValue = string | number | undefined;

function buildUrl(base: string, params: Record<string, QueryValue>): string {
  const url = new URL(base);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function request(
  method: "GET" | "POST",
  base: string,
  params: Record<string, QueryValue>,
  body: unknown | undefined,
  apiName: string,
  baseEnvVar: string,
): Promise<unknown> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(buildUrl(base, params), {
      method,
      signal: controller.signal,
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    // undici wraps the real cause (DNS, TLS, timeout) one level down.
    const cause =
      error instanceof Error && error.cause instanceof Error
        ? error.cause.message
        : String(error);
    // A TLS-inspecting proxy (Netskope/Zscaler) re-signs HTTPS with a private
    // CA that Node's bundled store lacks. This is a trust gap, not an outage —
    // don't send the user chasing "network access".
    const isCertError = /certificate|self-signed|self signed|SSL|TLS/i.test(
      cause,
    );
    const hint = isCertError
      ? "This is a TLS certificate trust error, not a network outage. If you " +
        "are behind a corporate proxy, launch Node with --use-system-ca, or " +
        "set REOPT_TLS_INSECURE=1 to skip verification on a trusted network."
      : `Check ${baseEnvVar} and network access.`;
    throw new Error(`Cannot reach ${apiName} at ${base}. ${hint} (${cause})`);
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    throw new HttpStatusError(response.status, await response.text());
  }
  return response.json();
}

export function httpGetJson(
  base: string,
  params: Record<string, QueryValue>,
  apiName: string,
  baseEnvVar: string,
): Promise<unknown> {
  return request("GET", base, params, undefined, apiName, baseEnvVar);
}

export function httpPostJson(
  base: string,
  params: Record<string, QueryValue>,
  body: unknown,
  apiName: string,
  baseEnvVar: string,
): Promise<unknown> {
  return request("POST", base, params, body, apiName, baseEnvVar);
}
