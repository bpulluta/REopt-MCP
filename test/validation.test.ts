import { describe, it, expect } from "vitest";
import {
  guidanceForErrors,
  scenarioWarnings,
  validateScenario,
} from "../src/validation.js";
import { getSolarScenario } from "../src/examples.js";

describe("validateScenario", () => {
  it("accepts a valid solar scenario", () => {
    const [ok, errors] = validateScenario(getSolarScenario());
    expect(ok).toBe(true);
    expect(errors).toEqual([]);
  });

  it("rejects a non-object", () => {
    expect(validateScenario("nope")).toEqual([false, ["Scenario must be an object"]]);
  });

  it("flags invalid Site fields and missing coordinates", () => {
    const [ok, errors] = validateScenario({
      Site: { city: "Denver" },
      ElectricLoad: { doe_reference_name: "MediumOffice", annual_kwh: 100 },
      ElectricTariff: { blended_annual_energy_rate: 0.1 },
    });
    expect(ok).toBe(false);
    expect(errors).toContain("Site contains invalid fields: {'city'}. Only use latitude/longitude.");
    expect(errors).toContain("Site missing 'latitude'");
    expect(errors).toContain("Site missing 'longitude'");
  });

  it("validates coordinate bounds and formats them with a trailing .0", () => {
    const [, errors] = validateScenario({
      Site: { latitude: 200, longitude: 0 },
      ElectricLoad: { doe_reference_name: "MediumOffice", annual_kwh: 100 },
      ElectricTariff: { blended_annual_energy_rate: 0.1 },
    });
    expect(errors).toContain("Site 'latitude' must be between -90.0 and 90.0 (got 200)");
  });

  it("rejects invalid doe_reference_name and non-positive annual_kwh", () => {
    const [, errors] = validateScenario({
      Site: { latitude: 39, longitude: -104 },
      ElectricLoad: { doe_reference_name: "Castle", annual_kwh: 0 },
      ElectricTariff: { blended_annual_energy_rate: 0.1 },
    });
    expect(errors.some((e) => e.startsWith("Invalid doe_reference_name: 'Castle'"))).toBe(true);
    expect(errors).toContain("ElectricLoad 'annual_kwh' must be a positive number");
  });

  it("rejects booleans as numbers (annual_kwh: true)", () => {
    const [, errors] = validateScenario({
      Site: { latitude: 39, longitude: -104 },
      ElectricLoad: { doe_reference_name: "MediumOffice", annual_kwh: true },
      ElectricTariff: { blended_annual_energy_rate: 0.1 },
    });
    expect(errors).toContain("ElectricLoad 'annual_kwh' must be a positive number");
  });

  it("off-grid: tariff present is an error", () => {
    const [, errors] = validateScenario({
      Settings: { off_grid_flag: true },
      Site: { latitude: 39, longitude: -104 },
      ElectricLoad: { doe_reference_name: "MediumOffice", annual_kwh: 100 },
      ElectricTariff: { blended_annual_energy_rate: 0.1 },
    });
    expect(errors).toContain(
      "ElectricTariff cannot be supplied when Settings 'off_grid_flag' is true",
    );
  });

  it("on-grid: missing tariff is an error", () => {
    const [, errors] = validateScenario({
      Site: { latitude: 39, longitude: -104 },
      ElectricLoad: { doe_reference_name: "MediumOffice", annual_kwh: 100 },
    });
    expect(errors).toContain("Missing 'ElectricTariff' object");
  });

  it("technology must be an object", () => {
    const [, errors] = validateScenario({
      Site: { latitude: 39, longitude: -104 },
      ElectricLoad: { doe_reference_name: "MediumOffice", annual_kwh: 100 },
      ElectricTariff: { blended_annual_energy_rate: 0.1 },
      PV: "yes",
    });
    expect(errors).toContain(
      "Technology 'PV' must be an object (use {} to let REopt optimize sizing)",
    );
  });

  it("blended DOE percents must sum to 1.0", () => {
    const [, errors] = validateScenario({
      Site: { latitude: 39, longitude: -104 },
      ElectricLoad: {
        doe_reference_name: "MediumOffice",
        annual_kwh: 100,
        blended_doe_reference_names: ["MediumOffice", "Warehouse"],
        blended_doe_reference_percents: [0.5, 0.4],
      },
      ElectricTariff: { blended_annual_energy_rate: 0.1 },
    });
    expect(errors).toContain(
      "ElectricLoad blended_doe_reference_percents must sum to 1.0",
    );
  });
});

describe("guidanceForErrors", () => {
  it("dedupes and maps errors to guidance", () => {
    const guidance = guidanceForErrors([
      "Site missing 'latitude'",
      "Site missing 'longitude'",
    ]);
    expect(guidance.length).toBe(1); // both map to the same coordinate guidance
    expect(guidance[0]).toContain("📍");
  });
});

describe("scenarioWarnings", () => {
  it("warns when no technology is requested", () => {
    const warnings = scenarioWarnings({
      Site: { latitude: 39, longitude: -104 },
      ElectricLoad: { doe_reference_name: "MediumOffice", annual_kwh: 100 },
      ElectricTariff: { blended_annual_energy_rate: 0.1, blended_annual_demand_rate: 5 },
    });
    expect(warnings.some((w) => w.includes("baseline-only"))).toBe(true);
  });
});
