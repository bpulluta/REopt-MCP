# Contributing

Thanks for helping build this out. The aim is a modular REopt MCP server that grows
to cover the full REopt API — one small, well-tested module at a time.

Read [ARCHITECTURE.md](ARCHITECTURE.md) first; it explains the module registry that
this guide's recipe plugs into.

## Dev setup

```bash
npm install
export NLR_API_KEY=your_key   # or a .env at repo root (see .env.example)
npm run server                # start the MCP server on stdio
npm test                      # vitest (no API key needed)
npm run typecheck             # tsc --noEmit
```

There is no build step — the server runs directly with `tsx`.

**Both `npm test` and `npm run typecheck` must pass before you open a PR.** Tests run
fully offline (network clients are unit-tested against fixtures).

## The golden rule: never invent REopt fields

REopt.jl defines every input/output key, its units, and its defaults. Guessing a name
or a default silently produces wrong scenarios. Ground truth is bundled at
[dev-docs/reoptjl_docs/bundles/](dev-docs/reoptjl_docs/bundles/):

- `inputs.md` — every input section, valid keys, units, defaults
- `outputs.md` — result field names and meanings

Before adding any key, `grep` it there and cite it in your PR. The `reopt-reference`
skill exists to enforce this — use it. If a field isn't in the docs, don't add it.

## Recipe: add a technology or section (one file, not four)

Every scenario piece is a [`ScenarioModule`](src/modules/types.ts). Adding coverage is:

1. **Write `src/modules/<name>.ts`** implementing `ScenarioModule`. Use the closest
   existing module as a template:
   - a technology → copy [src/modules/pv.ts](src/modules/pv.ts) (validate is
     optional; implement `summarizeResults` / `summarizeSystem` with output field
     names verified in `outputs.md`).
   - a rich input section with shorthands → study
     [src/modules/electric-tariff.ts](src/modules/electric-tariff.ts) (the reference
     `expand` + `validate` + `warnings` implementation).
   - a simple required section → copy [src/modules/site.ts](src/modules/site.ts).
2. **Register it** in [src/modules/index.ts](src/modules/index.ts) by adding one entry
   to `SCENARIO_MODULES` (technologies in the order they should appear in summaries).
   `KNOWN_TECHNOLOGIES`, `TECH_ORDER`, validation, normalization, warnings, and
   summaries all pick it up automatically — no other file changes.
3. **Add an example** via the module's `example()` and, if useful, a named scenario in
   [src/examples.ts](src/examples.ts).
4. **Add tests** mirroring [test/modules.test.ts](test/modules.test.ts) and
   [test/tariff.test.ts](test/tariff.test.ts). The registry round-trip test already
   asserts every bundled example validates, so a broken example fails CI. Add a
   fixture under `test/fixtures/` if a summary needs sample output.

That's it — no edits to `validation.ts`, `summaries.ts`, or `constants.ts` for a
standard technology. Those files consume the registry; they don't enumerate members.

## Conventions

- **Type guards**: import `isDict` / `isNumber` / `isNonEmptyString` / `isTruthy` from
  [src/guards.ts](src/guards.ts) — don't redefine them.
- **Responses**: build tool results with `text` / `errorResult` from
  [src/responses.ts](src/responses.ts) so every tool returns the same envelope
  (`status`, optional `next_step`, `submission_status`).
- **Determinism**: `expand` must be pure and deterministic — the preview and the
  confirmed submission are normalized the same way and must match byte-for-byte.
- **Keep `index.ts` thin**: it wires MCP tools to handlers; logic belongs in modules.
- Match the surrounding code's style, comment density, and naming.

## PR checklist

- [ ] `npm test` and `npm run typecheck` pass
- [ ] New/changed REopt keys are cited from `dev-docs/reoptjl_docs/bundles/`
- [ ] New module registered in `SCENARIO_MODULES`; example + tests added
- [ ] User-facing behavior changes reflected in `instructions.ts` / `README.md`
