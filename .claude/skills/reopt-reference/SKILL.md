---
name: reopt-reference
description: >-
  Authoritative REopt.jl input/output reference and safe scenario-extension guide
  for this MCP server, grounded in the bundled NLR docs at
  dev-docs/reoptjl_docs/bundles/. Use whenever a task involves REopt scenario keys,
  defaults, units, or output field meanings — e.g. "what fields does CHP/Wind/PV
  take", "is <key> valid", "why did REopt reject this", "add support for a new
  technology", or interpreting an optimization result. ALWAYS verify against the
  docs; never invent input keys, defaults, or output names from memory.
---

# REopt Reference & Extension Guide

This server's core promise is that it **does not make things up**. REopt.jl has
hundreds of input/output keys with specific names, units, and defaults. Guessing a
key name or default silently produces wrong scenarios. This skill points you at the
authoritative bundled docs and to the exact places in the code that must stay in
sync when you extend coverage.

## Ground truth: the bundled docs

Location: `dev-docs/reoptjl_docs/bundles/` (crawled from NLR's REopt.jl site).

| File | Use it for |
|------|-----------|
| `inputs.md` (~90 KB) | Every input section (Site, ElectricLoad, ElectricTariff, PV, Wind, ElectricStorage, Generator, CHP, GHP, thermal, emissions, outages…), valid keys, units, and default values |
| `outputs.md` | Result field names and meanings per technology + Financial/ElectricUtility |
| `examples.md` | Canonical end-to-end scenario JSON |
| `methods.md` | How REopt formulates and solves the optimization |
| `tech-models.md` / `developer.md` | Technology model internals; how REopt is structured |

**Lookup workflow — do this before answering any REopt field question:**

1. `grep -n "<key_or_section>" dev-docs/reoptjl_docs/bundles/inputs.md` (or `outputs.md`).
2. Read the surrounding lines for the exact name, unit, and default.
3. Answer with the value **and** cite the file. If it is not in the docs, say so —
   do not fall back to memory.

## Never do

- Invent an input key (e.g. unit-suffixed aliases like
  `blended_annual_rates_us_dollars_per_kwh` — REopt uses `blended_annual_energy_rate`).
- Assume a default value; quote the default from `inputs.md`.
- Report an output field the docs don't list. If a summary needs a metric, confirm
  the field name in `outputs.md` first.

## Extending the server (add a technology or input)

The server intentionally supports a **curated** subset (`PV`, `ElectricStorage`,
`Wind`, `Generator`). To add another technology (e.g. `CHP`), keep these four places
in sync so nothing is validated-but-not-summarized or shipped-but-not-validated:

1. **`src/constants.ts`** — add the tech name to `KNOWN_TECHNOLOGIES`. Add any
   new valid-key sets (mirror `VALID_ELECTRIC_TARIFF_KEYS`) using names verified in
   `inputs.md`.
2. **`src/validation.ts`** — the `KNOWN_TECHNOLOGIES` object-type check applies
   automatically; add value/range checks for any required numeric inputs (follow the
   `validateCoordinate` / blended-rate patterns, and `isNumber`).
3. **`src/summaries.ts`** — add a `sized(outputs, "<Tech>")` block in
   `formatResultsSummary`, `formatSystemSummary`, and `buildSubmitSummary`, and
   add the tech to `TECH_ORDER`. Use output field names verified in `outputs.md`.
4. **`src/examples.ts`** — add a canonical example scenario; it must pass
   `validateScenario` (covered by the validation/summary tests).

Then add tests mirroring `test/validation.test.ts` and `test/summaries.test.ts`,
and a fixture under `test/fixtures/` if a summary needs sample output. Run
`npm test && npm run typecheck`.

### Adding richer support for a scenario section (shorthands + validation)

Section handling is modular via `src/sections.ts`: each section gets a handler
with `expand` (compile human-friendly shorthands into canonical REopt keys),
`validate`, and `warnings`. `ElectricTariff` is the reference implementation in
`src/tariff.ts` (blended / monthly / TOU-schedule / URDB). To give another
section the same treatment (e.g. `ElectricLoad` blended DOE profiles), write a handler
and append it to `SECTION_HANDLERS` — `validateSections`, `sectionWarnings`, and the
submit-time normalization step pick it up automatically.

## Contract reminders (already enforced in code)

- On-grid requires `ElectricTariff`; off-grid sets `Settings.off_grid_flag=true` and
  omits it.
- `ElectricLoad` needs both `doe_reference_name` (valid DOE profile) and `annual_kwh`.
- `Site` accepts only `latitude` (-90..90) and `longitude` (-180..180) — never
  address/city fields.
- `submitAndWait` previews first; it only submits when called with `confirm=true`.
