/** Markdown summary composers for REopt outputs.
 *
 * These stitch together each technology module's own summary blocks (in registry
 * order) plus the fixed Financial and ElectricUtility sections. Per-technology
 * rendering lives in the modules (src/modules/*), so nothing is silently dropped
 * and adding a technology needs no change here.
 */

import { type Dict } from "./guards.js";
import { comma0, fixed1, num } from "./format.js";
import { TECHNOLOGY_MODULES } from "./modules/index.js";
import { defaultIsPresent } from "./modules/helpers.js";

/** Technology modules recommended in these outputs, in registry order. */
function recommendedTech(outputs: Dict) {
  return TECHNOLOGY_MODULES.filter((m) =>
    m.isPresent ? m.isPresent(outputs) : defaultIsPresent(outputs, m.key),
  );
}

/**
 * Inspect outputs for results that signal a modeling problem rather than a real
 * recommendation, and return human-readable warnings (empty when all is well).
 *
 * Currently flags a $0 baseline utility bill: an on-grid building always has a
 * positive bill before any system is added, so exactly $0 means REopt produced
 * no energy charges — almost always an unparseable or demand-only URDB tariff.
 * When that happens the bill-savings figures and the storage sizing (storage has
 * nothing to arbitrage against) are unreliable, so we surface it instead of
 * silently reporting $0. The warning names the exact input to change so the
 * caller can re-run without guessing.
 */
export function detectResultAnomalies(outputs: Dict): string[] {
  const warnings: string[] = [];

  if ("ElectricUtility" in outputs) {
    const util = outputs.ElectricUtility as Dict;
    if (num(util.year_one_bill_before_tax_bau) === 0) {
      warnings.push(
        "Baseline utility bill is $0, which is impossible for an on-grid " +
          "building with load. REopt could not compute energy charges from " +
          "the electricity rate — the URDB tariff is likely unparseable or " +
          "demand-only. Bill savings and any battery sizing from this run are " +
          "unreliable. Re-run with a blended rate (set " +
          "ElectricTariff.blended_annual_energy_rate, plus " +
          "blended_annual_demand_rate for demand charges) or a different " +
          "urdb_label.",
      );
    }
  }

  return warnings;
}

export function formatResultsSummary(outputs: Dict): string {
  let summary =
    "# REopt Optimization Results Summary\n\n## System Recommendations";

  for (const m of recommendedTech(outputs)) {
    if (m.summarizeResults) summary += m.summarizeResults(outputs);
  }

  if ("Financial" in outputs) {
    const fin = outputs.Financial as Dict;
    const payback = num(fin.simple_payback_years)
      ? fixed1(fin.simple_payback_years)
      : "N/A";
    const irr = num(fin.internal_rate_of_return)
      ? `${(num(fin.internal_rate_of_return) * 100).toFixed(1)}%`
      : "N/A";
    summary += `\n\n## Financial Analysis
- **Net Present Value**: $${comma0(fin.npv)}
- **Lifecycle Cost**: $${comma0(fin.lcc)}
- **Simple Payback**: ${payback} years
- **Internal Rate of Return**: ${irr}`;
  }

  if ("ElectricUtility" in outputs) {
    const util = outputs.ElectricUtility as Dict;
    const baseline = num(util.year_one_bill_before_tax_bau);
    const optimized = num(util.year_one_bill_before_tax);
    summary += `\n\n## Year 1 Utility Bill Analysis
- **Baseline Bill**: $${comma0(baseline)}
- **With System**: $${comma0(optimized)}
- **Annual Savings**: $${comma0(baseline - optimized)}`;
  }

  const anomalies = detectResultAnomalies(outputs);
  if (anomalies.length > 0) {
    summary += "\n\n## ⚠️ Warnings";
    for (const w of anomalies) summary += `\n- ${w}`;
  }

  return summary;
}

export function formatFinancialSummary(outputs: Dict): string {
  if (!("Financial" in outputs)) return "No financial results available.";

  const fin = outputs.Financial as Dict;
  let table = "# Financial Analysis\n\n| Metric | Value |\n|--------|-------|\n";
  table += `| Net Present Value (NPV) | $${comma0(fin.npv)} |\n`;
  table += `| Lifecycle Cost (LCC) | $${comma0(fin.lcc)} |\n`;
  table += `| Initial Capital Cost | $${comma0(fin.initial_capital_costs)} |\n`;
  table += `| Initial Capital Cost (after incentives) | $${comma0(
    fin.initial_capital_costs_after_incentives,
  )} |\n`;

  if (num(fin.simple_payback_years)) {
    table += `| Simple Payback Period | ${fixed1(fin.simple_payback_years)} years |\n`;
  }

  if (num(fin.internal_rate_of_return)) {
    table += `| Internal Rate of Return | ${(
      num(fin.internal_rate_of_return) * 100
    ).toFixed(1)}% |\n`;
  }

  table += `| Lifecycle O&M Costs | $${comma0(
    fin.om_and_replacement_present_cost_after_tax,
  )} |\n`;
  return table;
}

export function formatSystemSummary(outputs: Dict): string {
  let summary = "# System Technology Summary\n\n";

  const recommended = recommendedTech(outputs);
  for (const m of recommended) {
    if (m.summarizeSystem) summary += m.summarizeSystem(outputs);
  }

  if (recommended.length === 0) {
    summary += `No distributed energy systems recommended.

This typically means the economics don't favor installing solar or storage
under current assumptions (tariff, load, costs).

Consider:
- Verifying utility rate accuracy (blended rates or validated utility tariff inputs)
- Reviewing technology cost assumptions
- Adjusting financial parameters
- Exploring different technologies
`;
  }

  return summary;
}
