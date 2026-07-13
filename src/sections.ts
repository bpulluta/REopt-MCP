/** Modular scenario section-handler framework.
 *
 * Each handler owns one scenario section (e.g. `ElectricTariff`) and implements a
 * uniform contract:
 *
 * - `expand(section, scenario)` compiles human-friendly *shorthand* keys into the
 *   canonical REopt keys that get sent to the API (pass-through for everything else).
 * - `validate(section, scenario)` returns a list of error strings for that section.
 * - `warnings(section, scenario)` returns non-blocking advisories.
 *
 * Adding richer support for another section is a matter of writing one handler and
 * appending it to `SECTION_HANDLERS` — no changes to the submit/validate plumbing.
 */

import { ElectricTariffHandler } from "./tariff.js";

type Dict = Record<string, unknown>;

/** Structural contract every section handler must satisfy. */
export interface SectionHandler {
  readonly key: string;
  expand(section: Dict, scenario: Dict): Dict;
  validate(section: unknown, scenario: Dict): string[];
  warnings(section: unknown, scenario: Dict): string[];
}

// Ordered registry of section handlers. Append new handlers here.
export const SECTION_HANDLERS: SectionHandler[] = [new ElectricTariffHandler()];

function isDict(value: unknown): value is Dict {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Return a deep copy of the scenario with all shorthands compiled to REopt keys.
 *
 * Deterministic: re-normalizing the same input always yields the same payload, so
 * the two-step submit gate (preview, then confirm) stays consistent.
 */
export function normalizeScenario(scenario: unknown): unknown {
  if (!isDict(scenario)) return scenario;

  const normalized = structuredClone(scenario);
  for (const handler of SECTION_HANDLERS) {
    const section = normalized[handler.key];
    if (isDict(section)) {
      normalized[handler.key] = handler.expand(section, normalized);
    }
  }
  return normalized;
}

/** Aggregate per-section validation errors across all registered handlers.
 *
 * `skip` names section keys whose content validation should be bypassed (used when a
 * section's mere presence is already an error, e.g. ElectricTariff off-grid).
 */
export function validateSections(
  scenario: Dict,
  skip?: Set<string> | null,
): string[] {
  const skipSet = skip ?? new Set<string>();
  const errors: string[] = [];
  for (const handler of SECTION_HANDLERS) {
    if (skipSet.has(handler.key)) continue;
    const section = scenario[handler.key];
    if (section !== undefined && section !== null) {
      errors.push(...handler.validate(section, scenario));
    }
  }
  return errors;
}

/** Aggregate per-section advisories across all registered handlers. */
export function sectionWarnings(scenario: Dict): string[] {
  const warnings: string[] = [];
  for (const handler of SECTION_HANDLERS) {
    const section = scenario[handler.key];
    if (section !== undefined && section !== null) {
      warnings.push(...handler.warnings(section, scenario));
    }
  }
  return warnings;
}
