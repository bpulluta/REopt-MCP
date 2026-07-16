/** PV (solar) technology module. */

import { type Dict } from "../guards.js";
import { comma0, fixed1, fixed2, num } from "../format.js";
import { capacityFactor, techBlock } from "./helpers.js";
import type { ScenarioModule } from "./types.js";

export class PvModule implements ScenarioModule {
  readonly key = "PV";
  readonly kind = "technology" as const;
  readonly label = "Solar PV";

  example(): Dict {
    return {};
  }

  summarizeResults(outputs: Dict): string {
    const pv = techBlock(outputs, this.key);
    return `\n\n### Solar PV
- **Recommended Size**: ${fixed1(pv.size_kw)} kW
- **Year 1 Production**: ${comma0(pv.annual_energy_produced_kwh)} kWh
- **Annual O&M Cost**: $${comma0(pv.annual_om_cost_before_tax)}
- **Federal ITC**: ${(num(pv.federal_itc_fraction) * 100).toFixed(0)}%`;
  }

  summarizeSystem(outputs: Dict): string {
    const pv = techBlock(outputs, this.key);
    let s = "## Solar PV System\n\n| Metric | Value |\n|--------|-------|\n";
    s += `| System Size | ${fixed2(pv.size_kw)} kW |\n`;
    s += `| Year 1 Production | ${comma0(pv.annual_energy_produced_kwh)} kWh |\n`;
    s += `| Capacity Factor | ${fixed1(capacityFactor(pv))}% |\n`;
    s += `| Annual O&M Cost | $${comma0(pv.annual_om_cost_before_tax)} |\n`;
    s += `| Lifecycle O&M Cost | $${comma0(pv.lifecycle_om_cost_after_tax)} |\n\n`;
    return s;
  }
}
