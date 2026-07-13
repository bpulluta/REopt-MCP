import { describe, it, expect, vi, afterEach } from "vitest";
import {
  truncateLargeArrays,
  pollUntilComplete,
  submitJob,
} from "../src/client.js";

afterEach(() => {
  vi.restoreAllMocks();
});

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

describe("truncateLargeArrays", () => {
  it("summarizes numeric arrays with length >= 8760", () => {
    const arr = new Array(8760).fill(2);
    const out = truncateLargeArrays({ series: arr }) as any;
    expect(out.series).toEqual({
      _truncated: true,
      _type: "timeseries",
      _length: 8760,
      _sum: 17520,
      _mean: 2,
      _min: 2,
      _max: 2,
    });
  });

  it("leaves short arrays and non-numeric arrays untouched", () => {
    expect(truncateLargeArrays([1, 2, 3])).toEqual([1, 2, 3]);
    const strs = new Array(8760).fill("x");
    expect((truncateLargeArrays(strs) as unknown[]).length).toBe(8760);
  });

  it("recurses into nested structures", () => {
    const out = truncateLargeArrays({ a: { b: [1, 2] } }) as any;
    expect(out.a.b).toEqual([1, 2]);
  });
});

describe("submitJob", () => {
  it("returns the run_uuid from the API", async () => {
    const fn = mockFetchJson({ run_uuid: "abc-123" });
    const uuid = await submitJob({ Site: {} });
    expect(uuid).toBe("abc-123");
    const url = String(fn.mock.calls[0][0]);
    expect(url).toContain("/job");
    expect(url).toContain("api_key=");
  });
});

describe("pollUntilComplete", () => {
  it("returns complete immediately when status is optimal", async () => {
    mockFetchJson({ status: "optimal", outputs: { PV: { size_kw: 10 } } });
    const result = await pollUntilComplete("uuid-1", 300);
    expect(result.status).toBe("complete");
    if (result.status === "complete") {
      expect(result.job_status).toBe("optimal");
      expect(result.poll_count).toBe(1);
    }
  });

  it("times out when maxWaitSeconds is exceeded", async () => {
    mockFetchJson({ status: "Optimizing" });
    const result = await pollUntilComplete("uuid-1", -1); // already over budget
    expect(result.status).toBe("timeout");
  });
});
