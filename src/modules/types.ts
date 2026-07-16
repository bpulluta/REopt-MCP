/** The one contract every scenario piece implements.
 *
 * A `ScenarioModule` owns a single top-level REopt scenario key (a section like
 * `ElectricTariff`, or a technology like `PV`). The registry in
 * `src/modules/index.ts` drives all of validation, normalization (shorthand
 * expansion), warnings, output summaries, and examples off this contract — so
 * adding coverage for a new section or technology is one new file plus one line
 * in the registry, never a four-file edit.
 *
 * Every method except `key`/`kind` is optional; simple modules stay tiny.
 */

import type { Dict } from "../guards.js";

export type ModuleKind = "core" | "section" | "technology";

export interface ScenarioModule {
  /** Top-level scenario key this module owns, e.g. "Site" or "PV". */
  readonly key: string;

  /**
   * - `core`     — always-relevant input section (Site, ElectricLoad, Settings).
   * - `section`  — optional input section with rich shorthand/validation (ElectricTariff).
   * - `technology` — a generation/storage option added as `{}` and sized by REopt.
   */
  readonly kind: ModuleKind;

  /** Human-facing label for messages and summary headings. */
  readonly label?: string;

  /** When true, the top-level validator reports an error if this section is
   * absent from the scenario (used for Site and ElectricLoad). */
  readonly required?: boolean;

  /**
   * Compile human-friendly shorthand keys into the canonical REopt keys that get
   * sent to the API. Must be deterministic and pass-through for everything it does
   * not recognize. Default (when omitted): identity.
   */
  expand?(section: Dict, scenario: Dict): Dict;

  /** Return a list of error strings for this section's content. */
  validate?(section: unknown, scenario: Dict): string[];

  /** Return non-blocking advisories to surface before submission. */
  warnings?(section: unknown, scenario: Dict): string[];

  /** A canonical example fragment for this section, used to assemble examples. */
  example?(): Dict;

  // --- Technology-only hooks (kind === "technology") ------------------------

  /**
   * True when this technology was recommended in the outputs. Default heuristic
   * (applied by the summary composer when omitted): `size_kw > 0`.
   */
  isPresent?(outputs: Dict): boolean;

  /** Compact markdown block for the high-level "results" summary. */
  summarizeResults?(outputs: Dict): string;

  /** Detailed markdown table for the "system" summary. */
  summarizeSystem?(outputs: Dict): string;
}
