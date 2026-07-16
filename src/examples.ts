/** Example REopt scenarios.
 *
 * Core section fragments (Site, ElectricLoad, ElectricTariff) and technology
 * fragments are pulled from each module's `example()` so an example can never
 * reference a section or technology the server doesn't actually implement. Most
 * scenarios use minimal inputs to let REopt optimize system sizes.
 */

import type { Dict } from "./guards.js";
import { moduleFor } from "./modules/index.js";

/** A fresh copy of a module's example fragment (empty dict if it has none). */
function frag(key: string): Dict {
  return structuredClone(moduleFor(key)?.example?.() ?? {});
}

/** The 3 required inputs — no technologies. Use as a starting point.
 *
 * CRITICAL: ElectricLoad MUST have BOTH fields:
 * - doe_reference_name: provides the hourly load pattern/shape
 * - annual_kwh: scales the pattern to your consumption
 */
export function getBaseInputs(): Dict {
  return {
    Site: frag("Site"),
    ElectricLoad: frag("ElectricLoad"),
    ElectricTariff: frag("ElectricTariff"),
  };
}

/** Evaluate solar PV only - no constraints. */
export function getSolarScenario(): Dict {
  const scenario = getBaseInputs();
  scenario.PV = frag("PV");
  return scenario;
}

/** Evaluate solar + battery - no constraints. */
export function getSolarBatteryScenario(): Dict {
  const scenario = getBaseInputs();
  scenario.PV = frag("PV");
  scenario.ElectricStorage = frag("ElectricStorage");
  return scenario;
}

/** Solar + battery with constraints (only if you have space/budget limits). */
export function getPvAndStorageScenario(): Dict {
  const scenario = getBaseInputs();
  scenario.PV = { max_kw: 500 };
  scenario.ElectricStorage = { max_kw: 250, max_kwh: 1000 };
  return scenario;
}

/** Resilience/backup power scenario with generator. */
export function getResilienceScenario(): Dict {
  const scenario = getBaseInputs();
  scenario.ElectricLoad = {
    doe_reference_name: "Hospital",
    annual_kwh: 5000000,
    critical_load_fraction: 0.5,
  };
  scenario.PV = frag("PV");
  scenario.ElectricStorage = frag("ElectricStorage");
  scenario.Generator = frag("Generator");
  scenario.Financial = { value_of_lost_load_per_kwh: 100.0 };
  return scenario;
}

/** Solar with month-by-month blended energy and demand rates (12 values each). */
export function getMonthlyRatesScenario(): Dict {
  const scenario = getBaseInputs();
  scenario.ElectricTariff = {
    monthly_energy_rates: [
      0.1, 0.1, 0.11, 0.12, 0.14, 0.18, 0.2, 0.2, 0.16, 0.12, 0.1, 0.1,
    ],
    monthly_demand_rates: [12, 12, 13, 14, 16, 20, 22, 22, 18, 14, 12, 12],
  };
  scenario.PV = frag("PV");
  return scenario;
}

/** Time-of-use energy rates via the schedule shorthand the server compiles.
 *
 * Summer (Jun-Sep) weekday 4-9pm is on-peak; everything else is off-peak.
 */
export function getTouRatesScenario(): Dict {
  const scenario = getBaseInputs();
  scenario.ElectricTariff = {
    tou_energy_schedule: {
      default_rate: 0.1,
      periods: [
        { rate: 0.32, months: [6, 7, 8, 9], days: "weekday", hours: [[16, 21]] },
        { rate: 0.2, months: [6, 7, 8, 9], days: "weekend", hours: [[16, 21]] },
      ],
    },
    monthly_demand_rates: [12, 12, 13, 14, 16, 20, 22, 22, 18, 14, 12, 12],
  };
  scenario.PV = frag("PV");
  return scenario;
}

/** Solar using a published URDB rate (find labels with searchUrdbRates). */
export function getUrdbScenario(): Dict {
  const scenario = getBaseInputs();
  scenario.ElectricTariff = { urdb_label: "5ed6c1a15457a3367add15ae" };
  scenario.PV = frag("PV");
  return scenario;
}

/** Multi-technology: solar + wind + battery. */
export function getWindScenario(): Dict {
  const scenario = getBaseInputs();
  (scenario.Site as Dict).latitude = 41.8781;
  (scenario.Site as Dict).longitude = -87.6298; // Chicago
  scenario.PV = frag("PV");
  scenario.Wind = frag("Wind");
  scenario.ElectricStorage = frag("ElectricStorage");
  return scenario;
}

/** Guide to every supported ElectricTariff rate mode, simple to complex. */
export function getTariffHelp(): Dict {
  return {
    status: "success",
    name: "tariff",
    title: "ElectricTariff rate modes",
    description:
      "Pick the ONE energy-rate mode that matches how the user's rate is " +
      "actually structured (you may add demand charges alongside it). Ask the " +
      "user about the shape of their rate before choosing; don't default to " +
      "blended. Each mode lists 'when' to use it.",
    modes: [
      {
        mode: "blended_annual",
        when: "Quick estimate; one average price for the whole year.",
        keys: {
          blended_annual_energy_rate: "$/kWh (e.g. 0.12)",
          blended_annual_demand_rate: "$/kW/month (e.g. 15.0)",
        },
      },
      {
        mode: "monthly",
        when: "Rates vary by season/month but not by hour.",
        keys: {
          monthly_energy_rates: "12 values, $/kWh (Jan..Dec)",
          monthly_demand_rates: "12 values, $/kW (Jan..Dec)",
        },
      },
      {
        mode: "time_of_use",
        when: "Peak/off-peak pricing by hour of day, day type, and season.",
        keys: {
          tou_energy_schedule:
            "Shorthand the server compiles into an 8760-hour array: " +
            "{default_rate, periods:[{rate, months[1-12], " +
            "days:weekday|weekend|all, hours:[[start,end)]]}]}",
          tou_energy_rates_per_kwh:
            "Advanced: supply the raw 8760/17520/35040-length array " +
            "yourself instead of the shorthand.",
        },
      },
      {
        mode: "urdb",
        when: "Most accurate: use the utility's published tariff.",
        keys: {
          urdb_label: "URDB rate id (use searchUrdbRates to find it)",
          urdb_response: "Advanced: a full raw URDB rate JSON object",
        },
      },
    ],
    notes: [
      "Demand charges are optional; if none are given they are treated as $0.",
      "If you set a URDB rate AND blended/monthly/TOU rates, REopt uses only the " +
        "URDB rate unless add_monthly_rates_to_urdb_rate / " +
        "add_tou_energy_rates_to_urdb_rate is true.",
      "TOU weekday/weekend alignment uses ElectricLoad.year (default 2017).",
    ],
    examples: {
      monthly_rates: getMonthlyRatesScenario().ElectricTariff,
      tou_rates: getTouRatesScenario().ElectricTariff,
      urdb: getUrdbScenario().ElectricTariff,
    },
  };
}

/** Guide to every supported ElectricLoad input mode, simple to advanced. */
export function getLoadHelp(): Dict {
  return {
    status: "success",
    name: "load",
    title: "ElectricLoad input modes",
    description:
      "REopt needs a load SOURCE (the shape of demand) and usually a SCALER (how " +
      "much energy). Pick the source that matches what the user has; add a scaler " +
      "to match their actual usage. Ask before assuming.",
    sources: [
      {
        source: "doe_reference_name",
        when: "You only know the building type. Uses a DOE reference profile.",
        keys: { doe_reference_name: "e.g. 'MediumOffice' (see getScenarioHelp('minimal') for the list)" },
      },
      {
        source: "blended_doe_reference_names",
        when: "The building is a mix of types (e.g. office + warehouse).",
        keys: {
          blended_doe_reference_names: "list of building types",
          blended_doe_reference_percents: "matching weights, 0-1, summing to 1.0",
        },
      },
      {
        source: "loads_kw",
        when: "You have the actual hourly demand profile.",
        keys: {
          loads_kw:
            "8760 values (or 17520/35040 for Settings.time_steps_per_hour 2/4), kW per step",
        },
      },
      {
        source: "loads_csv",
        when: "The hourly profile is in a CSV file on this machine.",
        keys: {
          loads_csv:
            "path to a CSV with one kW value per row (optional header). The server " +
            "reads it and compiles it into loads_kw. NOTE: REopt.jl's 'path_to_csv' " +
            "does NOT work through the hosted API — use loads_csv.",
        },
      },
    ],
    scalers: {
      annual_kwh: "one annual total, kWh",
      monthly_totals_kwh: "12 monthly totals (Jan..Dec), kWh",
      monthly_peaks_kw: "12 monthly peak demands (Jan..Dec), kW",
    },
    notes: [
      "With a reference profile, a scaler (annual_kwh or monthly_totals_kwh) is " +
        "strongly recommended so the profile matches actual usage.",
      "To scale an explicit loads_kw/loads_csv profile with a scaler, also set " +
        "normalize_and_scale_load_profile_input=true; otherwise the profile is used as-is.",
      "Sub-hourly data requires Settings.time_steps_per_hour = 2 or 4 and a matching " +
        "array length (17520 or 35040).",
    ],
    examples: {
      reference: { doe_reference_name: "MediumOffice", annual_kwh: 500000 },
      monthly: {
        doe_reference_name: "RetailStore",
        monthly_totals_kwh: [
          18000, 16000, 17000, 15000, 19000, 24000, 28000, 27000, 22000, 17000,
          16000, 18000,
        ],
      },
      csv: { loads_csv: "./my_building_loads.csv" },
    },
  };
}

export interface Example {
  name: string;
  description: string;
  scenario: Dict;
}

/** Return a map of all example scenarios. */
export function getAllExamples(): Record<string, Example> {
  return {
    base: {
      name: "Base Inputs Only",
      description: "Just the 3 required inputs - add technologies as needed",
      scenario: getBaseInputs(),
    },
    solar: {
      name: "Solar Only",
      description: "Evaluate solar PV with no constraints",
      scenario: getSolarScenario(),
    },
    solar_battery: {
      name: "Solar + Battery",
      description: "Evaluate solar and battery with no constraints",
      scenario: getSolarBatteryScenario(),
    },
    pv_and_storage: {
      name: "With Constraints",
      description:
        "Solar + battery with size limits (only if you have actual constraints)",
      scenario: getPvAndStorageScenario(),
    },
    monthly_rates: {
      name: "Monthly Rates",
      description: "Solar with month-by-month energy and demand rates",
      scenario: getMonthlyRatesScenario(),
    },
    tou_rates: {
      name: "Time-of-Use Rates",
      description: "Solar with a time-of-use energy schedule the server compiles",
      scenario: getTouRatesScenario(),
    },
    urdb: {
      name: "URDB Rate",
      description: "Solar using a published URDB tariff label",
      scenario: getUrdbScenario(),
    },
    resilience: {
      name: "Resilience Analysis",
      description: "Backup power evaluation with generator",
      scenario: getResilienceScenario(),
    },
    wind: {
      name: "Wind + Solar",
      description: "Multi-technology evaluation",
      scenario: getWindScenario(),
    },
  };
}
