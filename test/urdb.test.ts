import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// config.ts captures env at import time, so set the key before importing urdb.
process.env.NLR_API_KEY = "test-key";
const { searchUrdbRates } = await import("../src/urdb.js");

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

  it("sends the expected query params and trims items", async () => {
    const fn = mockFetchJson({
      items: [
        {
          label: "L1",
          name: "Commercial TOU",
          utility: "PGE",
          sector: "Commercial",
          startdate: 1,
          uri: "http://x",
          extra: "dropped",
        },
      ],
    });
    const results = await searchUrdbRates({ utility: "PGE", limit: 3 });
    const url = new URL(String(fn.mock.calls[0][0]));
    expect(url.searchParams.get("version")).toBe("latest");
    expect(url.searchParams.get("format")).toBe("json");
    expect(url.searchParams.get("detail")).toBe("minimal");
    expect(url.searchParams.get("limit")).toBe("3");
    expect(url.searchParams.get("ratesforutility")).toBe("PGE");
    expect(results).toEqual([
      {
        label: "L1",
        name: "Commercial TOU",
        utility: "PGE",
        sector: "Commercial",
        startdate: 1,
        uri: "http://x",
      },
    ]);
  });

  it("clamps limit to 1..50", async () => {
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

  it("raises on a URDB API error payload", async () => {
    mockFetchJson({ error: "bad request" });
    await expect(searchUrdbRates({ utility: "PGE" })).rejects.toThrow(/URDB API error/);
  });
});
