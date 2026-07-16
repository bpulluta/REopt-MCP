/** Wind technology module. */

import { type Dict } from "../guards.js";
import { comma0, fixed1, fixed2 } from "../format.js";
import { capacityFactor, techBlock } from "./helpers.js";
import type { ScenarioModule } from "./types.js";

export class WindModule implements ScenarioModule {
  readonly key = "Wind";
  readonly kind = "technology" as const;
  readonly label = "Wind";

  example(): Dict {
    return {};
  }

  summarizeResults(outputs: Dict): string {
    const wind = techBlock(outputs, this.key);
    return `\n\n### Wind
- **Recommended Size**: ${fixed1(wind.size_kw)} kW
- **Year 1 Production**: ${comma0(wind.annual_energy_produced_kwh)} kWh
- **Annual O&M Cost**: $${comma0(wind.annual_om_cost_before_tax)}`;
  }

  summarizeSystem(outputs: Dict): string {
    const wind = techBlock(outputs, this.key);
    let s = "## Wind System\n\n| Metric | Value |\n|--------|-------|\n";
    s += `| System Size | ${fixed2(wind.size_kw)} kW |\n`;
    s += `| Year 1 Production | ${comma0(wind.annual_energy_produced_kwh)} kWh |\n`;
    s += `| Capacity Factor | ${fixed1(capacityFactor(wind))}% |\n`;
    s += `| Annual O&M Cost | $${comma0(wind.annual_om_cost_before_tax)} |\n\n`;
    return s;
  }
}
