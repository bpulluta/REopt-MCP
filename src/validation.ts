/** Top-level scenario validation and guidance.
 *
 * This is a thin orchestrator. It enforces the cross-section invariants that don't
 * belong to any single module (required sections; the on-grid/off-grid ElectricTariff
 * rule) and then delegates all per-section content checks to the module registry
 * (src/modules/index.ts). Each module owns the details of its own section.
 */

import { isDict, type Dict } from "./guards.js";
import {
  KNOWN_TECHNOLOGIES,
  REQUIRED_MODULES,
  moduleWarnings,
  validateModules,
} from "./modules/index.js";
import { readOffGridFlag } from "./modules/settings.js";

/** Validate that a scenario has all required fields and no invalid assumptions. */
export function validateScenario(scenario: unknown): [boolean, string[]] {
  if (!isDict(scenario)) return [false, ["Scenario must be an object"]];

  const errors: string[] = [];
  const offGridFlag = readOffGridFlag(scenario);

  // Required sections (Site, ElectricLoad) must be present.
  for (const m of REQUIRED_MODULES) {
    if (!(m.key in scenario)) errors.push(`Missing '${m.key}' object`);
  }

  // Cross-section rule: on-grid needs ElectricTariff; off-grid forbids it.
  const offGridTariffPresent = offGridFlag && "ElectricTariff" in scenario;
  if (offGridTariffPresent) {
    errors.push(
      "ElectricTariff cannot be supplied when Settings 'off_grid_flag' is true",
    );
  } else if (!offGridFlag && !("ElectricTariff" in scenario)) {
    errors.push("Missing 'ElectricTariff' object");
  }

  // Technologies must be objects ({} lets REopt optimize sizing).
  for (const tech of [...KNOWN_TECHNOLOGIES].sort()) {
    if (tech in scenario && !isDict(scenario[tech])) {
      errors.push(
        `Technology '${tech}' must be an object (use {} to let REopt optimize sizing)`,
      );
    }
  }

  // Delegate per-section content checks to their modules. Skip ElectricTariff when
  // its mere presence off-grid is already flagged above.
  const skip = offGridTariffPresent ? new Set(["ElectricTariff"]) : null;
  errors.push(...validateModules(scenario, skip));

  return [errors.length === 0, errors];
}

/** Non-blocking advisories to surface for human review before submission. */
export function scenarioWarnings(scenario: unknown): string[] {
  const warnings: string[] = [];
  if (!isDict(scenario)) return warnings;

  const requested = [...KNOWN_TECHNOLOGIES].filter((tech) => tech in scenario);
  if (requested.length === 0) {
    warnings.push(
      "No technology requested (PV, Wind, ElectricStorage, Generator). " +
        "This runs a baseline-only scenario with no recommended systems.",
    );
  }

  warnings.push(...moduleWarnings(scenario));
  return warnings;
}

export function guidanceForErrors(errors: string[]): string[] {
  const guidance: string[] = [];
  for (const err of errors) {
    if (err.includes("must be an object") && err.includes("Technology")) {
      guidance.push(
        '🔧 Add technologies as empty objects, e.g. "PV": {} — never a string or list',
      );
    } else if (err.includes("latitude") || err.includes("longitude")) {
      guidance.push(
        "📍 Ask user for the city/address, then look up valid coordinates (lat -90..90, lon -180..180)",
      );
    } else if (err.includes("doe_reference_name")) {
      guidance.push(
        "🏢 Ask user for building type (office, retail, warehouse, etc.)",
      );
    } else if (err.includes("annual_kwh")) {
      guidance.push("⚡ Ask user for annual electricity consumption in kWh");
    } else if (err.includes("off_grid_flag")) {
      guidance.push(
        "🔌 For off-grid scenarios set Settings.off_grid_flag=true and remove ElectricTariff",
      );
    } else if (err.includes("energy-rate source")) {
      guidance.push(
        "💵 Pick a rate mode: blended (blended_annual_energy_rate + blended_annual_demand_rate), monthly (monthly_energy_rates), time-of-use (tou_energy_schedule), or a URDB label (urdb_label — use searchUrdbRates to find one). See getScenarioHelp('tariff').",
      );
    } else if (
      err.includes("monthly_energy_rates") ||
      err.includes("monthly_demand_rates")
    ) {
      guidance.push(
        "📅 Monthly rates need exactly 12 non-negative values (Jan–Dec). Ask the user for each month's $/kWh (energy) or $/kW (demand).",
      );
    } else if (err.includes("tou_energy_schedule")) {
      guidance.push(
        "🕐 Fix the time-of-use schedule: each period needs a non-negative rate, months 1–12, days weekday|weekend|all, and [start, end) hour ranges within 0–24.",
      );
    } else if (err.includes("tou_energy_rates_per_kwh")) {
      guidance.push(
        "🕐 A raw TOU array must have 8760/17520/35040 values. Prefer the 'tou_energy_schedule' shorthand and let the server compile it.",
      );
    } else if (err.includes("ElectricTariff") || err.includes("urdb_label")) {
      guidance.push(
        "💵 Pick a rate mode: blended (blended_annual_energy_rate + blended_annual_demand_rate), monthly (monthly_energy_rates), time-of-use (tou_energy_schedule), or a URDB label (urdb_label — use searchUrdbRates to find one). See getScenarioHelp('tariff').",
      );
    }
  }
  // Dedupe while preserving first-occurrence order for stable, deterministic output.
  return [...new Set(guidance)];
}
