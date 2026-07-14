import { describe, it, expect, vi, afterEach } from "vitest";

// config.ts captures env at import time, so set the key before importing urdb.
process.env.NLR_API_KEY = "test-key";
const { searchUrdbRates, urdbViewUrl } = await import("../src/urdb.js");

// Epoch seconds. The "expired" rate ends in 2015 regardless of today's date;
// the "active" rate has no enddate, so these assertions are time-independent.
const START_2014 = 1404198000; // 2014-07-01
const END_2015 = 1451545200; // 2015-12-31
const START_2022 = 1663804800; // 2022-09-22

function mockFetchJson(payload: unknown) {
  const fn = vi.fn(async (..._args: unknown[]) => ({
    ok: true,
    status: 200,
    json: async () => payload,
    text: async () => "",
  }));
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => vi.restoreAllMocks());

describe("searchUrdbRates", () => {
  it("requires utility or address", async () => {
    await expect(searchUrdbRates({})).rejects.toThrow(/utility.*address/);
  });

  it("sends the expected query params and returns a trimmed, enriched shape", async () => {
    const fn = mockFetchJson({
      items: [
        {
          label: "L1",
          name: "Commercial TOU",
          utility: "PGE",
          sector: "Commercial",
          approved: true,
          startdate: START_2022,
          uri: "https://apps.openei.org/USURDB/rate/view/L1",
          extra: "dropped",
        },
      ],
    });
    const results = await searchUrdbRates({ utility: "PGE", limit: 3 });
    const url = new URL(String(fn.mock.calls[0][0]));
    expect(url.searchParams.get("version")).toBe("latest");
    expect(url.searchParams.get("format")).toBe("json");
    expect(url.searchParams.get("detail")).toBe("minimal");
    // Newest-first server-side so a small page returns the current rates.
    expect(url.searchParams.get("direction")).toBe("desc");
    expect(url.searchParams.get("limit")).toBe("3");
    expect(url.searchParams.get("ratesforutility")).toBe("PGE");
    expect(results).toEqual([
      {
        label: "L1",
        name: "Commercial TOU",
        utility: "PGE",
        sector: "Commercial",
        approved: true,
        active: true,
        effective_period: "2022-09-22 – present",
        view_url: "https://apps.openei.org/USURDB/rate/view/L1",
      },
    ]);
  });

  it("clamps the requested limit to 1..50", async () => {
    const fn = mockFetchJson({ items: [] });
    await searchUrdbRates({ utility: "PGE", limit: 999 });
    const url = new URL(String(fn.mock.calls[0][0]));
    expect(url.searchParams.get("limit")).toBe("50");
  });

  it("filters by rate_name substring (case-insensitive)", async () => {
    mockFetchJson({
      items: [
        { label: "A", name: "Residential Flat" },
        { label: "B", name: "Commercial TOU" },
      ],
    });
    const results = await searchUrdbRates({ utility: "PGE", rate_name: "tou" });
    expect(results.map((r) => r.label)).toEqual(["B"]);
  });

  it("ranks active before expired, then most recent start date", async () => {
    mockFetchJson({
      items: [
        { label: "expired", name: "Old", startdate: START_2014, enddate: END_2015 },
        { label: "active-old", name: "Cur1", startdate: START_2014 },
        { label: "active-new", name: "Cur2", startdate: START_2022 },
      ],
    });
    const results = await searchUrdbRates({ utility: "PGE" });
    expect(results.map((r) => r.label)).toEqual([
      "active-new",
      "active-old",
      "expired",
    ]);
    const expired = results.find((r) => r.label === "expired")!;
    expect(expired.active).toBe(false);
    expect(expired.effective_period).toBe("2014-07-01 – 2015-12-31");
  });

  it("falls back to a constructed view_url when the API omits uri", async () => {
    mockFetchJson({ items: [{ label: "abc123", name: "R" }] });
    const [row] = await searchUrdbRates({ utility: "PGE" });
    expect(row.view_url).toBe("https://apps.openei.org/USURDB/rate/view/abc123");
    // No dates -> treated as currently active with an unknown start.
    expect(row.active).toBe(true);
    expect(row.effective_period).toBe("unknown – present");
  });

  it("raises on a URDB API error payload", async () => {
    mockFetchJson({ error: "bad request" });
    await expect(searchUrdbRates({ utility: "PGE" })).rejects.toThrow(/URDB API error/);
  });
});

describe("urdbViewUrl", () => {
  it("builds the OpenEI rate-view URL from a label", () => {
    expect(urdbViewUrl("xyz")).toBe(
      "https://apps.openei.org/USURDB/rate/view/xyz",
    );
  });
});
