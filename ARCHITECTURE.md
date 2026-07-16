# Architecture

This MCP server exposes NLR's REopt energy-optimization API as a small set of MCP
tools. Its design goal is to stay a thin, honest layer over REopt: gather inputs,
validate them, show the user exactly what will be submitted, run the job, and render
results — without inventing keys, units, or defaults that REopt does not define.

## Directory map

```
src/
  index.ts          MCP tool definitions + handlers (the only file that talks to the SDK)
  responses.ts      the standard tool response envelope (text / errorResult)
  guards.ts         shared runtime type guards (isDict, isNumber, …)
  config.ts         env + TLS configuration
  http.ts           minimal fetch wrapper (shared by REopt + URDB clients)
  client.ts         REopt API client: submit, poll, truncate large arrays
  urdb.ts           URDB (OpenEI) rate search
  validation.ts     top-level scenario validation orchestrator + guidance
  summaries.ts      markdown summary composers (stitch module output blocks together)
  examples.ts       example scenarios (assembled from module fragments)
  constants.ts      constants shared by more than one module
  instructions.ts   the server-level instructions shown to the calling agent
  modules/          ← the scalable core: one file per scenario section/technology
    types.ts        the ScenarioModule contract
    index.ts        the registry + normalize/validate/warn helpers
    site.ts electric-load.ts settings.ts electric-tariff.ts
    pv.ts wind.ts electric-storage.ts generator.ts
    helpers.ts      shared summary helpers (capacityFactor, techBlock, …)
```

## The module registry (the important part)

Every top-level REopt scenario key — a section like `ElectricTariff` or a technology
like `PV` — is a **module** implementing one contract, [`ScenarioModule`](src/modules/types.ts):

| Hook | Purpose |
|------|---------|
| `key` / `kind` / `label` | identity; `kind` ∈ `core` \| `section` \| `technology` |
| `required` | if true, the validator errors when the section is absent |
| `expand(section, scenario)` | compile human shorthands → canonical REopt keys (deterministic) |
| `validate(section, scenario)` | return content error strings |
| `warnings(section, scenario)` | return non-blocking advisories |
| `example()` | a canonical fragment used to assemble examples |
| `isPresent` / `summarizeResults` / `summarizeSystem` | technology output rendering |

The registry in [src/modules/index.ts](src/modules/index.ts) holds the ordered list and
derives everything else from it: `KNOWN_TECHNOLOGIES`, `TECH_ORDER`, the
`normalizeScenario` / `validateModules` / `moduleWarnings` passes. Because these are
**derived**, they can never drift from what is actually implemented.

Cross-section rules that don't belong to any single module (required sections; the
"on-grid needs ElectricTariff, off-grid forbids it" rule) live in
[src/validation.ts](src/validation.ts). Everything section-specific lives in the module.

## Data flow

```
agent gathers inputs (guided by instructions.ts)
        │
        ▼
validateScenario ──► cross-section invariants + validateModules()  → errors + guidance
        │
        ▼
normalizeScenario ──► each module.expand()  (e.g. TOU schedule → 8760-hour array)
        │
        ▼
submitAndWait (confirm=false) ──► PREVIEW: normalized payload + warnings + URDB link
        │  (human approves)
        ▼
submitAndWait (confirm=true) ──► client.submitJob() → pollUntilComplete()
        │                          (truncateLargeArrays collapses 8760+ series)
        ▼
summaries.ts ──► formatResultsSummary() stitches each recommended tech's block
        │        + Financial + ElectricUtility
        ▼
results_markdown returned for the agent to show verbatim
```

The **two-step submit gate** (preview, then confirm) is the core safety property:
`submitAndWait` never submits until called with `confirm=true`, and the preview shows
the exact normalized payload so the user approves what REopt will actually receive.

## Grounding: never invent REopt fields

REopt.jl has hundreds of input/output keys with specific names, units, and defaults.
The authoritative reference is bundled at
[dev-docs/reoptjl_docs/bundles/](dev-docs/reoptjl_docs/bundles/) (`inputs.md`,
`outputs.md`, …). The `reopt-reference` skill enforces the rule: verify every key
against those docs; do not fall back to memory. See [CONTRIBUTING.md](CONTRIBUTING.md).
