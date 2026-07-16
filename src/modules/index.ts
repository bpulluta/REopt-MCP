/** The scenario-module registry.
 *
 * One ordered list drives all of normalization (shorthand expansion), validation,
 * warnings, output summaries, and examples. Adding coverage for a new REopt
 * section or technology is a matter of writing one module file that implements
 * {@link ScenarioModule} and appending it here — no changes to validation,
 * summary, or example plumbing.
 */

import { isDict, type Dict } from "../guards.js";
import type { ScenarioModule } from "./types.js";

import { SiteModule } from "./site.js";
import { ElectricLoadModule } from "./electric-load.js";
import { SettingsModule } from "./settings.js";
import { ElectricTariffModule } from "./electric-tariff.js";
import { PvModule } from "./pv.js";
import { ElectricStorageModule } from "./electric-storage.js";
import { WindModule } from "./wind.js";
import { GeneratorModule } from "./generator.js";

export type { ScenarioModule, ModuleKind } from "./types.js";

/** Ordered registry. Order controls example assembly and summary section order.
 * Register new modules here (technologies in the order they should be summarized). */
export const SCENARIO_MODULES: ScenarioModule[] = [
  new SiteModule(),
  new ElectricLoadModule(),
  new SettingsModule(),
  new ElectricTariffModule(),
  new PvModule(),
  new ElectricStorageModule(),
  new WindModule(),
  new GeneratorModule(),
];

export const TECHNOLOGY_MODULES: ScenarioModule[] = SCENARIO_MODULES.filter(
  (m) => m.kind === "technology",
);

/** Technology keys, derived from the registry so they can never drift. */
export const KNOWN_TECHNOLOGIES: ReadonlySet<string> = new Set(
  TECHNOLOGY_MODULES.map((m) => m.key),
);

/** Technology summary order, derived from registry order. */
export const TECH_ORDER: readonly string[] = TECHNOLOGY_MODULES.map((m) => m.key);

/** Modules that must be present in every scenario (Site, ElectricLoad). */
export const REQUIRED_MODULES: ScenarioModule[] = SCENARIO_MODULES.filter(
  (m) => m.required === true,
);

/** Look up a module by its scenario key. */
export function moduleFor(key: string): ScenarioModule | undefined {
  return SCENARIO_MODULES.find((m) => m.key === key);
}

/** Return a deep copy of the scenario with all shorthands compiled to REopt keys.
 *
 * Deterministic: re-normalizing the same input always yields the same payload, so
 * the two-step submit gate (preview, then confirm) stays consistent.
 */
export function normalizeScenario(scenario: unknown): unknown {
  if (!isDict(scenario)) return scenario;

  const normalized = structuredClone(scenario);
  for (const m of SCENARIO_MODULES) {
    if (!m.expand) continue;
    const section = normalized[m.key];
    if (isDict(section)) {
      normalized[m.key] = m.expand(section, normalized);
    }
  }
  return normalized;
}

/** Aggregate per-section validation errors across all registered modules.
 *
 * `skip` names section keys whose content validation should be bypassed (used when
 * a section's mere presence is already an error, e.g. ElectricTariff off-grid).
 */
export function validateModules(
  scenario: Dict,
  skip?: Set<string> | null,
): string[] {
  const skipSet = skip ?? new Set<string>();
  const errors: string[] = [];
  for (const m of SCENARIO_MODULES) {
    if (!m.validate || skipSet.has(m.key)) continue;
    const section = scenario[m.key];
    if (section !== undefined && section !== null) {
      errors.push(...m.validate(section, scenario));
    }
  }
  return errors;
}

/** Aggregate per-section advisories across all registered modules. */
export function moduleWarnings(scenario: Dict): string[] {
  const warnings: string[] = [];
  for (const m of SCENARIO_MODULES) {
    if (!m.warnings) continue;
    const section = scenario[m.key];
    if (section !== undefined && section !== null) {
      warnings.push(...m.warnings(section, scenario));
    }
  }
  return warnings;
}
