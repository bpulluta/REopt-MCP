import { describe, it, expect } from "vitest";
import {
  KNOWN_TECHNOLOGIES,
  SCENARIO_MODULES,
  TECHNOLOGY_MODULES,
  TECH_ORDER,
  normalizeScenario,
} from "../src/modules/index.js";
import { SettingsModule } from "../src/modules/settings.js";
import { validateScenario } from "../src/validation.js";
import { formatResultsSummary, formatSystemSummary } from "../src/summaries.js";
import { getAllExamples } from "../src/examples.js";

describe("registry", () => {
  it("derives technology sets from the registry (never hardcoded)", () => {
    expect([...KNOWN_TECHNOLOGIES]).toEqual(TECH_ORDER as string[]);
    expect(TECH_ORDER).toEqual(["PV", "ElectricStorage", "Wind", "Generator"]);
    expect(TECHNOLOGY_MODULES.every((m) => m.kind === "technology")).toBe(true);
  });

  it("every module owns a unique key", () => {
    const keys = SCENARIO_MODULES.map((m) => m.key);
    expect(new Set(keys).size).toBe(keys.length);
  });
});

describe("examples round-trip through the registry", () => {
  it("every bundled example validates", () => {
    for (const [name, ex] of Object.entries(getAllExamples())) {
      const [ok, errors] = validateScenario(ex.scenario);
      expect(ok, `${name}: ${errors.join("; ")}`).toBe(true);
    }
  });
});

describe("technology modules render their own summaries", () => {
  // A synthetic outputs blob where every technology is "recommended".
  const outputs: Record<string, unknown> = {};
  for (const m of TECHNOLOGY_MODULES) {
    outputs[m.key] = {
      size_kw: 100,
      size_kwh: 200,
      annual_energy_produced_kwh: 150000,
      annual_om_cost_before_tax: 1000,
      annual_fuel_consumption_gal: 500,
      federal_itc_fraction: 0.3,
    };
  }

  it("results and system summaries include a block for each recommended tech", () => {
    const results = formatResultsSummary(outputs);
    const system = formatSystemSummary(outputs);
    const techCount = TECHNOLOGY_MODULES.length;
    // One "### " block per tech in results; one "## " section per tech in system.
    expect(results.match(/^### /gm)?.length).toBe(techCount);
    expect(system.match(/^## /gm)?.length).toBe(techCount);
    expect(system).not.toContain("No distributed energy systems recommended");
  });

  it("omits a tech whose size is zero", () => {
    const zeroed = { ...outputs, PV: { size_kw: 0 } };
    expect(formatResultsSummary(zeroed)).not.toContain("Solar PV");
  });
});

describe("normalizeScenario", () => {
  it("is deterministic (preview and confirm match)", () => {
    const scenario = {
      Site: { latitude: 39, longitude: -104 },
      ElectricLoad: { doe_reference_name: "MediumOffice", annual_kwh: 100 },
      ElectricTariff: {
        tou_energy_schedule: {
          default_rate: 0.1,
          periods: [{ rate: 0.3, months: [7], days: "weekday", hours: [[16, 21]] }],
        },
      },
      PV: {},
    };
    expect(JSON.stringify(normalizeScenario(scenario))).toBe(
      JSON.stringify(normalizeScenario(scenario)),
    );
  });
});

describe("SettingsModule", () => {
  const settings = new SettingsModule();

  it("accepts an empty Settings", () => {
    expect(settings.validate({})).toEqual([]);
  });

  it("rejects a non-boolean off_grid_flag", () => {
    expect(settings.validate({ off_grid_flag: "yes" })).toContain(
      "Settings 'off_grid_flag' must be a boolean",
    );
  });

  it("rejects an invalid time_steps_per_hour", () => {
    expect(settings.validate({ time_steps_per_hour: 3 })).toContain(
      "Settings 'time_steps_per_hour' must be one of 1, 2, or 4",
    );
    expect(settings.validate({ time_steps_per_hour: 4 })).toEqual([]);
  });
});
