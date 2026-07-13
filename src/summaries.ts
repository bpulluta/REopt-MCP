/** Markdown summary formatters for REopt outputs.
 *
 * Every supported technology (PV, ElectricStorage, Wind, Generator) is rendered so
 * nothing is silently dropped.
 */

import { comma0, fixed1, fixed2, num } from "./format.js";

type Dict = Record<string, unknown>;

function isDict(value: unknown): value is Dict {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Return a technology's output block if it was recommended (size_kw > 0). */
function sized(outputs: Dict, key: string): Dict | null {
  const block = outputs[key];
  if (isDict(block) && num(block.size_kw) > 0) return block;
  return null;
}

function capacityFactor(block: Dict): number {
  const produced =
    num(block.annual_energy_produced_kwh) ||
    num(block.average_annual_energy_produced_kwh);
  const sizeKw = num(block.size_kw);
  if (sizeKw > 0) return (produced / (sizeKw * 8760)) * 100;
  return 0.0;
}

// Order here controls the order sections appear in every summary.
export const TECH_ORDER = ["PV", "ElectricStorage", "Wind", "Generator"] as const;

export function formatResultsSummary(outputs: Dict): string {
  let summary =
    "# REopt Optimization Results Summary\n\n## System Recommendations";

  const pv = sized(outputs, "PV");
  if (pv) {
    summary += `\n\n### Solar PV
- **Recommended Size**: ${fixed1(pv.size_kw)} kW
- **Year 1 Production**: ${comma0(pv.annual_energy_produced_kwh)} kWh
- **Annual O&M Cost**: $${comma0(pv.annual_om_cost_before_tax)}
- **Federal ITC**: ${(num(pv.federal_itc_fraction) * 100).toFixed(0)}%`;
  }

  const storage = sized(outputs, "ElectricStorage");
  if (storage) {
    summary += `\n\n### Battery Storage
- **Power Capacity**: ${fixed1(storage.size_kw)} kW
- **Energy Capacity**: ${fixed1(storage.size_kwh)} kWh
- **Annual O&M Cost**: $${comma0(storage.annual_om_cost_before_tax)}`;
  }

  const wind = sized(outputs, "Wind");
  if (wind) {
    summary += `\n\n### Wind
- **Recommended Size**: ${fixed1(wind.size_kw)} kW
- **Year 1 Production**: ${comma0(wind.annual_energy_produced_kwh)} kWh
- **Annual O&M Cost**: $${comma0(wind.annual_om_cost_before_tax)}`;
  }

  const generator = sized(outputs, "Generator");
  if (generator) {
    summary += `\n\n### Backup Generator
- **Recommended Size**: ${fixed1(generator.size_kw)} kW
- **Annual Fuel Use**: ${comma0(generator.annual_fuel_consumption_gal)} gal
- **Annual O&M Cost**: $${comma0(generator.annual_om_cost_before_tax)}`;
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

  const pv = sized(outputs, "PV");
  if (pv) {
    summary += "## Solar PV System\n\n| Metric | Value |\n|--------|-------|\n";
    summary += `| System Size | ${fixed2(pv.size_kw)} kW |\n`;
    summary += `| Year 1 Production | ${comma0(pv.annual_energy_produced_kwh)} kWh |\n`;
    summary += `| Capacity Factor | ${fixed1(capacityFactor(pv))}% |\n`;
    summary += `| Annual O&M Cost | $${comma0(pv.annual_om_cost_before_tax)} |\n`;
    summary += `| Lifecycle O&M Cost | $${comma0(pv.lifecycle_om_cost_after_tax)} |\n\n`;
  }

  const storage = sized(outputs, "ElectricStorage");
  if (storage) {
    const sizeKw = num(storage.size_kw);
    const duration = sizeKw > 0 ? num(storage.size_kwh) / sizeKw : 0;
    summary +=
      "## Battery Energy Storage\n\n| Metric | Value |\n|--------|-------|\n";
    summary += `| Power Capacity | ${fixed2(storage.size_kw)} kW |\n`;
    summary += `| Energy Capacity | ${fixed2(storage.size_kwh)} kWh |\n`;
    summary += `| Duration | ${fixed1(duration)} hours |\n`;
    summary += `| Annual O&M Cost | $${comma0(storage.annual_om_cost_before_tax)} |\n\n`;
  }

  const wind = sized(outputs, "Wind");
  if (wind) {
    summary += "## Wind System\n\n| Metric | Value |\n|--------|-------|\n";
    summary += `| System Size | ${fixed2(wind.size_kw)} kW |\n`;
    summary += `| Year 1 Production | ${comma0(wind.annual_energy_produced_kwh)} kWh |\n`;
    summary += `| Capacity Factor | ${fixed1(capacityFactor(wind))}% |\n`;
    summary += `| Annual O&M Cost | $${comma0(wind.annual_om_cost_before_tax)} |\n\n`;
  }

  const generator = sized(outputs, "Generator");
  if (generator) {
    summary += "## Backup Generator\n\n| Metric | Value |\n|--------|-------|\n";
    summary += `| System Size | ${fixed2(generator.size_kw)} kW |\n`;
    summary += `| Annual Fuel Use | ${comma0(
      generator.annual_fuel_consumption_gal,
    )} gal |\n`;
    summary += `| Annual O&M Cost | $${comma0(generator.annual_om_cost_before_tax)} |\n\n`;
  }

  if (!TECH_ORDER.some((tech) => sized(outputs, tech))) {
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

export function buildSubmitSummary(
  runUuid: string,
  elapsedSeconds: number,
  jobStatus: string,
  outputs: Dict,
): string {
  const parts: string[] = [
    `✓ Optimization completed successfully in ${elapsedSeconds} seconds`,
    `  Run UUID: ${runUuid}`,
    `  Status: ${jobStatus}`,
    "",
  ];

  const pv = sized(outputs, "PV");
  if (pv) parts.push(`  Solar PV: ${fixed1(pv.size_kw)} kW`);

  const storage = sized(outputs, "ElectricStorage");
  if (storage) {
    parts.push(
      `  Battery: ${fixed1(storage.size_kw)} kW / ${fixed1(storage.size_kwh)} kWh`,
    );
  }

  const wind = sized(outputs, "Wind");
  if (wind) parts.push(`  Wind: ${fixed1(wind.size_kw)} kW`);

  const generator = sized(outputs, "Generator");
  if (generator) parts.push(`  Generator: ${fixed1(generator.size_kw)} kW`);

  const fin = outputs.Financial;
  if (isDict(fin) && fin.npv !== null && fin.npv !== undefined) {
    parts.push(`  NPV: $${comma0(fin.npv)}`);
  }

  return parts.join("\n");
}
