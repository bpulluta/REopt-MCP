import { describe, it, expect, afterAll } from "vitest";
import { writeFileSync, rmSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  ElectricLoadModule,
  readLoadsCsv,
} from "../src/modules/electric-load.js";

const load = new ElectricLoadModule();

describe("ElectricLoadModule.validate", () => {
  it("accepts the classic reference-building + annual_kwh", () => {
    expect(
      load.validate({ doe_reference_name: "MediumOffice", annual_kwh: 500000 }, {}),
    ).toEqual([]);
  });

  it("requires a load source", () => {
    const errors = load.validate({ annual_kwh: 100 }, {});
    expect(errors.some((e) => e.includes("needs a load source"))).toBe(true);
  });

  it("accepts monthly_totals_kwh (12 values) as the scaler", () => {
    const errors = load.validate(
      {
        doe_reference_name: "RetailStore",
        monthly_totals_kwh: new Array(12).fill(10000),
      },
      {},
    );
    expect(errors).toEqual([]);
  });

  it("rejects monthly_totals_kwh with the wrong count", () => {
    const errors = load.validate(
      { doe_reference_name: "RetailStore", monthly_totals_kwh: [1, 2, 3] },
      {},
    );
    expect(errors.some((e) => e.includes("exactly 12 values"))).toBe(true);
  });

  it("accepts loads_kw of length 8760", () => {
    const errors = load.validate({ loads_kw: new Array(8760).fill(50) }, {});
    expect(errors).toEqual([]);
  });

  it("rejects loads_kw of the wrong length", () => {
    const errors = load.validate({ loads_kw: new Array(100).fill(50) }, {});
    expect(errors.some((e) => e.includes("length 8760, 17520, or 35040"))).toBe(true);
  });

  it("ties loads_kw length to Settings.time_steps_per_hour", () => {
    const errors = load.validate(
      { loads_kw: new Array(8760).fill(50) },
      { Settings: { time_steps_per_hour: 2 } },
    );
    expect(errors.some((e) => e.includes("implies 17520"))).toBe(true);
  });

  it("rejects the REopt.jl path_to_csv key with guidance", () => {
    const errors = load.validate(
      { doe_reference_name: "MediumOffice", path_to_csv: "/x.csv" },
      {},
    );
    expect(errors.some((e) => e.includes("path_to_csv") && e.includes("loads_csv"))).toBe(
      true,
    );
  });

  it("flags unsupported (possibly invented) keys", () => {
    const errors = load.validate(
      { doe_reference_name: "MediumOffice", made_up_key: 1 },
      {},
    );
    expect(errors.some((e) => e.includes("unsupported keys"))).toBe(true);
  });
});

describe("ElectricLoadModule.warnings", () => {
  it("warns when an explicit profile has a scaler but no normalize flag", () => {
    const warnings = load.warnings(
      { loads_kw: new Array(8760).fill(1), annual_kwh: 100000 },
      {},
    );
    expect(warnings.some((w) => w.includes("is ignored"))).toBe(true);
  });

  it("warns when a reference profile has no scaler", () => {
    const warnings = load.warnings({ doe_reference_name: "MediumOffice" }, {});
    expect(warnings.some((w) => w.includes("built-in annual energy"))).toBe(true);
  });
});

describe("loads_csv shorthand", () => {
  const dir = mkdtempSync(join(tmpdir(), "reopt-csv-"));
  afterAll(() => rmSync(dir, { recursive: true, force: true }));

  function writeCsv(name: string, body: string): string {
    const path = join(dir, name);
    writeFileSync(path, body, "utf8");
    return path;
  }

  it("reads one value per row, skipping a header", () => {
    const rows = ["load_kw", ...new Array(8760).fill("42")].join("\n");
    const path = writeCsv("ok.csv", rows);
    expect(readLoadsCsv(path)).toHaveLength(8760);
    expect(readLoadsCsv(path).every((v) => v === 42)).toBe(true);
  });

  it("expand() compiles loads_csv into loads_kw and drops the shorthand", () => {
    const path = writeCsv("expand.csv", new Array(8760).fill("7").join("\n"));
    const out = load.expand({ loads_csv: path }, {});
    expect(out.loads_csv).toBeUndefined();
    expect(Array.isArray(out.loads_kw)).toBe(true);
    expect((out.loads_kw as number[]).length).toBe(8760);
  });

  it("validate() surfaces a read error for a missing file", () => {
    const errors = load.validate({ loads_csv: join(dir, "nope.csv") }, {});
    expect(errors.some((e) => e.includes("could not be read"))).toBe(true);
  });

  it("rejects multi-column rows rather than guessing a column", () => {
    const path = writeCsv("multi.csv", "1,2\n3,4\n");
    expect(() => readLoadsCsv(path)).toThrow(/multiple columns/);
  });

  it("rejects a non-numeric data cell", () => {
    const path = writeCsv("bad.csv", "10\nabc\n12\n");
    expect(() => readLoadsCsv(path)).toThrow(/not a number/);
  });
});
