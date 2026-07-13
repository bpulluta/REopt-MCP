/** Example REopt scenarios.
 *
 * Most scenarios use minimal inputs (only Site, ElectricLoad, ElectricTariff) to let
 * REopt automatically optimize system sizes.
 */

type Dict = Record<string, unknown>;

/** The 3 required inputs — no technologies. Use as a starting point.
 *
 * CRITICAL: ElectricLoad MUST have BOTH fields:
 * - doe_reference_name: provides the hourly load pattern/shape
 * - annual_kwh: scales the pattern to your consumption
 */
export function getBaseInputs(): Dict {
  return {
    Site: { latitude: 39.7407, longitude: -104.989 },
    ElectricLoad: { doe_reference_name: "MediumOffice", annual_kwh: 500000 },
    ElectricTariff: {
      blended_annual_energy_rate: 0.12,
      blended_annual_demand_rate: 15.0,
    },
  };
}

/** Evaluate solar PV only - no constraints. */
export function getSolarScenario(): Dict {
  const scenario = getBaseInputs();
  scenario.PV = {};
  return scenario;
}

/** Evaluate solar + battery - no constraints. */
export function getSolarBatteryScenario(): Dict {
  const scenario = getBaseInputs();
  scenario.PV = {};
  scenario.ElectricStorage = {};
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
  scenario.PV = {};
  scenario.ElectricStorage = {};
  scenario.Generator = {};
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
  scenario.PV = {};
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
  scenario.PV = {};
  return scenario;
}

/** Solar using a published URDB rate (find labels with searchUrdbRates). */
export function getUrdbScenario(): Dict {
  const scenario = getBaseInputs();
  scenario.ElectricTariff = { urdb_label: "5ed6c1a15457a3367add15ae" };
  scenario.PV = {};
  return scenario;
}

/** Multi-technology: solar + wind + battery. */
export function getWindScenario(): Dict {
  const scenario = getBaseInputs();
  (scenario.Site as Dict).latitude = 41.8781;
  (scenario.Site as Dict).longitude = -87.6298; // Chicago
  scenario.PV = {};
  scenario.Wind = {};
  scenario.ElectricStorage = {};
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
