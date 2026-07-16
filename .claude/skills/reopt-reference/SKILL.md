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

## Extending the server (add a technology or section)

Every scenario section and technology is now a single `ScenarioModule`
(`src/modules/types.ts`) in one registry — adding coverage is **one new file plus one
line**, not a four-file edit. `PV`/`ElectricStorage`/`Wind`/`Generator` and
`Site`/`ElectricLoad`/`Settings`/`ElectricTariff` all follow the same contract.

To add a technology (e.g. `CHP`) or section:

1. **Write `src/modules/<name>.ts`** implementing `ScenarioModule`
   (`key`, `kind`, optional `expand`/`validate`/`warnings`/`example`, and for
   technologies `summarizeResults`/`summarizeSystem`). Copy the closest existing
   module: `src/modules/pv.ts` (technology), `src/modules/electric-tariff.ts` (rich
   section with shorthands), or `src/modules/site.ts` (simple required section). Use
   input keys from `inputs.md` and output field names from `outputs.md`.
2. **Register it** in `src/modules/index.ts` by adding one entry to
   `SCENARIO_MODULES`. `KNOWN_TECHNOLOGIES`, `TECH_ORDER`, `validateModules`,
   `normalizeScenario`, `moduleWarnings`, and the summary composers all pick it up
   automatically — no edits to `validation.ts`, `summaries.ts`, or `constants.ts`.
3. **Add an example** via the module's `example()` (and a named scenario in
   `src/examples.ts` if useful).
4. **Add tests** mirroring `test/modules.test.ts` / `test/tariff.test.ts`, plus a
   `test/fixtures/` sample if a summary needs output. Run `npm test && npm run typecheck`.

Cross-section rules that belong to no single module (required sections; the
on-grid/off-grid ElectricTariff rule) live in `src/validation.ts`. See
`CONTRIBUTING.md` and `ARCHITECTURE.md` for the full recipe and data flow.

## Contract reminders (already enforced in code)

- On-grid requires `ElectricTariff`; off-grid sets `Settings.off_grid_flag=true` and
  omits it.
- `ElectricLoad` needs a load *source* — `doe_reference_name`, `blended_doe_reference_names`,
  `loads_kw` (8760/17520/35040 values), or the server-side `loads_csv` shorthand (a file
  path the server reads into `loads_kw`; REopt.jl's `path_to_csv` does NOT work via the
  hosted API) — plus, usually, a *scaler* (`annual_kwh`, `monthly_totals_kwh`, or
  `monthly_peaks_kw`). See `src/modules/electric-load.ts`.
- `Site` accepts only `latitude` (-90..90) and `longitude` (-180..180) — never
  address/city fields.
- `submitAndWait` previews first; it only submits when called with `confirm=true`.
