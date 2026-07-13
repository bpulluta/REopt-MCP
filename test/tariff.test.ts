import { describe, it, expect } from "vitest";
import {
  compileTouSchedule,
  ElectricTariffHandler,
} from "../src/tariff.js";

const handler = new ElectricTariffHandler();

describe("compileTouSchedule", () => {
  it("produces an 8760-hour array (non-leap year, Feb 29 skipped)", () => {
    const arr = compileTouSchedule(
      { default_rate: 0.1, periods: [] },
      { year: 2020, timeStepsPerHour: 1 }, // 2020 is a leap year
    );
    expect(arr.length).toBe(8760);
    expect(arr.every((v) => v === 0.1)).toBe(true);
  });

  it("applies summer weekday on-peak (Jun-Sep, 16-21) in 2017", () => {
    const arr = compileTouSchedule(
      {
        default_rate: 0.1,
        periods: [
          { rate: 0.32, months: [6, 7, 8, 9], days: "weekday", hours: [[16, 21]] },
        ],
      },
      { year: 2017, timeStepsPerHour: 1 },
    );
    // 87 weekdays in Jun-Sep 2017 * 5 on-peak hours = 435 hours at 0.32.
    const onPeak = arr.filter((v) => v === 0.32).length;
    expect(onPeak).toBe(435);
    const sum = arr.reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(971.7, 1);
  });

  it("half-open hour ranges: [16,21) covers 16..20, not 21", () => {
    const arr = compileTouSchedule(
      {
        default_rate: 0,
        periods: [{ rate: 1, months: [1], days: "all", hours: [[16, 21]] }],
      },
      { year: 2017, timeStepsPerHour: 1 },
    );
    // Jan 1 hour 15 = off, 16..20 = on, 21 = off.
    expect(arr[15]).toBe(0);
    expect(arr[16]).toBe(1);
    expect(arr[20]).toBe(1);
    expect(arr[21]).toBe(0);
  });

  it("last matching period wins", () => {
    const arr = compileTouSchedule(
      {
        default_rate: 0,
        periods: [
          { rate: 0.5, months: [1], days: "all", hours: [[0, 24]] },
          { rate: 0.9, months: [1], days: "all", hours: [[10, 12]] },
        ],
      },
      { year: 2017, timeStepsPerHour: 1 },
    );
    expect(arr[9]).toBe(0.5);
    expect(arr[10]).toBe(0.9); // later period overrides
    expect(arr[12]).toBe(0.5);
  });

  it("expands to sub-hourly when time_steps_per_hour > 1", () => {
    const arr = compileTouSchedule(
      { default_rate: 0.1, periods: [] },
      { year: 2017, timeStepsPerHour: 4 },
    );
    expect(arr.length).toBe(35040);
  });

  it("defaults: missing months=all, days=all, hours=all-day", () => {
    const arr = compileTouSchedule(
      { default_rate: 0, periods: [{ rate: 2 }] },
      { year: 2017, timeStepsPerHour: 1 },
    );
    expect(arr.every((v) => v === 2)).toBe(true);
  });
});

describe("ElectricTariffHandler.expand", () => {
  it("compiles tou_energy_schedule into tou_energy_rates_per_kwh", () => {
    const section = {
      tou_energy_schedule: { default_rate: 0.1, periods: [{ rate: 0.3 }] },
    };
    const scenario = { ElectricTariff: section };
    const out = handler.expand(section, scenario);
    expect(out.tou_energy_schedule).toBeUndefined();
    expect(Array.isArray(out.tou_energy_rates_per_kwh)).toBe(true);
    expect((out.tou_energy_rates_per_kwh as number[]).length).toBe(8760);
  });

  it("leaves the section unchanged when there is no schedule", () => {
    const section = { blended_annual_energy_rate: 0.12 };
    expect(handler.expand(section, {})).toBe(section);
  });

  it("uses ElectricLoad.year and Settings.time_steps_per_hour", () => {
    const section = { tou_energy_schedule: { default_rate: 0.1, periods: [{ rate: 0.3 }] } };
    const scenario = {
      ElectricLoad: { year: 2019 },
      Settings: { time_steps_per_hour: 2 },
      ElectricTariff: section,
    };
    const out = handler.expand(section, scenario);
    expect((out.tou_energy_rates_per_kwh as number[]).length).toBe(17520);
  });
});

describe("ElectricTariffHandler.validate", () => {
  it("accepts a blended rate", () => {
    expect(handler.validate({ blended_annual_energy_rate: 0.12 }, {})).toEqual([]);
  });

  it("requires an energy-rate source", () => {
    const errors = handler.validate({ blended_annual_demand_rate: 10 }, {});
    expect(errors.some((e) => e.includes("energy-rate source"))).toBe(true);
  });

  it("flags deprecated aliases", () => {
    const errors = handler.validate(
      { blended_annual_rates_us_dollars_per_kwh: 0.12 },
      {},
    );
    expect(errors[0]).toContain("invalid keys for REopt.jl");
    expect(errors[0]).toContain("blended_annual_energy_rate");
  });

  it("flags unsupported keys", () => {
    const errors = handler.validate(
      { blended_annual_energy_rate: 0.1, bogus_key: 1 },
      {},
    );
    expect(errors.some((e) => e.includes("unsupported keys"))).toBe(true);
  });

  it("monthly rates must have exactly 12 non-negative values", () => {
    expect(
      handler.validate({ monthly_energy_rates: [0.1, 0.2] }, {}).some((e) =>
        e.includes("exactly 12"),
      ),
    ).toBe(true);
    expect(
      handler
        .validate({ monthly_energy_rates: new Array(12).fill(-1) }, {})
        .some((e) => e.includes("non-negative")),
    ).toBe(true);
  });

  it("tou array length must match time steps", () => {
    const errors = handler.validate(
      { tou_energy_rates_per_kwh: new Array(8760).fill(0.1) },
      { Settings: { time_steps_per_hour: 2 } },
    );
    expect(errors.some((e) => e.includes("time steps per year"))).toBe(true);
  });

  it("validates schedule period structure", () => {
    const errors = handler.validate(
      {
        tou_energy_schedule: {
          periods: [{ rate: -1, months: [13], days: "someday", hours: [[5, 5]] }],
        },
      },
      {},
    );
    expect(errors.some((e) => e.includes(".rate"))).toBe(true);
    expect(errors.some((e) => e.includes(".months"))).toBe(true);
    expect(errors.some((e) => e.includes(".days"))).toBe(true);
    expect(errors.some((e) => e.includes(".hours"))).toBe(true);
  });
});

describe("ElectricTariffHandler.warnings", () => {
  it("warns when URDB coexists with custom rates without add_* flags", () => {
    const warnings = handler.warnings(
      { urdb_label: "abc", blended_annual_energy_rate: 0.1 },
      {},
    );
    expect(warnings.some((w) => w.includes("uses only the URDB rate"))).toBe(true);
  });

  it("warns when there is no demand source", () => {
    const warnings = handler.warnings({ blended_annual_energy_rate: 0.1 }, {});
    expect(warnings.some((w) => w.includes("Demand charges will be $0"))).toBe(true);
  });
});
