import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import {
  buildSubmitSummary,
  formatFinancialSummary,
  formatResultsSummary,
  formatSystemSummary,
} from "../src/summaries.js";

const optimal = JSON.parse(
  readFileSync(fileURLToPath(new URL("./fixtures/optimal_result.json", import.meta.url)), "utf8"),
);
const outputs = optimal.outputs;

describe("formatResultsSummary", () => {
  const md = formatResultsSummary(outputs);
  it("formats PV size (.1f), production (,.0f) and ITC (%)", () => {
    expect(md).toContain("**Recommended Size**: 120.0 kW");
    expect(md).toContain("**Year 1 Production**: 180,000 kWh");
    expect(md).toContain("**Federal ITC**: 30%");
  });
  it("formats financial NPV, payback, IRR", () => {
    expect(md).toContain("**Net Present Value**: $78,000");
    expect(md).toContain("**Simple Payback**: 8.5 years");
    expect(md).toContain("**Internal Rate of Return**: 11.0%");
  });
  it("computes utility bill savings", () => {
    expect(md).toContain("**Annual Savings**: $26,000");
  });
});

describe("formatSystemSummary", () => {
  const md = formatSystemSummary(outputs);
  it("formats PV size (.2f) and capacity factor", () => {
    expect(md).toContain("| System Size | 120.00 kW |");
    // 180000 / (120 * 8760) * 100 = 17.1232...% -> 17.1%
    expect(md).toContain("| Capacity Factor | 17.1% |");
  });
  it("computes battery duration", () => {
    expect(md).toContain("| Duration | 4.0 hours |"); // 200 / 50
  });
});

describe("formatFinancialSummary", () => {
  it("returns a table with capital costs", () => {
    const md = formatFinancialSummary(outputs);
    expect(md).toContain("| Initial Capital Cost | $250,000 |");
    expect(md).toContain("| Initial Capital Cost (after incentives) | $175,000 |");
  });
  it("handles missing Financial", () => {
    expect(formatFinancialSummary({})).toBe("No financial results available.");
  });
});

describe("formatSystemSummary (no systems)", () => {
  it("emits the no-recommendation block", () => {
    expect(formatSystemSummary({})).toContain(
      "No distributed energy systems recommended.",
    );
  });
});

describe("buildSubmitSummary", () => {
  it("lists sized techs and NPV", () => {
    const s = buildSubmitSummary("uuid-1", 3, "optimal", outputs);
    expect(s).toContain("Run UUID: uuid-1");
    expect(s).toContain("Solar PV: 120.0 kW");
    expect(s).toContain("Battery: 50.0 kW / 200.0 kWh");
    expect(s).toContain("NPV: $78,000");
  });
});
