/** ElectricStorage (battery) technology module. */

import { type Dict } from "../guards.js";
import { comma0, fixed1, fixed2, num } from "../format.js";
import { techBlock } from "./helpers.js";
import type { ScenarioModule } from "./types.js";

export class ElectricStorageModule implements ScenarioModule {
  readonly key = "ElectricStorage";
  readonly kind = "technology" as const;
  readonly label = "Battery Storage";

  example(): Dict {
    return {};
  }

  summarizeResults(outputs: Dict): string {
    const storage = techBlock(outputs, this.key);
    return `\n\n### Battery Storage
- **Power Capacity**: ${fixed1(storage.size_kw)} kW
- **Energy Capacity**: ${fixed1(storage.size_kwh)} kWh
- **Annual O&M Cost**: $${comma0(storage.annual_om_cost_before_tax)}`;
  }

  summarizeSystem(outputs: Dict): string {
    const storage = techBlock(outputs, this.key);
    const sizeKw = num(storage.size_kw);
    const duration = sizeKw > 0 ? num(storage.size_kwh) / sizeKw : 0;
    let s = "## Battery Energy Storage\n\n| Metric | Value |\n|--------|-------|\n";
    s += `| Power Capacity | ${fixed2(storage.size_kw)} kW |\n`;
    s += `| Energy Capacity | ${fixed2(storage.size_kwh)} kWh |\n`;
    s += `| Duration | ${fixed1(duration)} hours |\n`;
    s += `| Annual O&M Cost | $${comma0(storage.annual_om_cost_before_tax)} |\n\n`;
    return s;
  }
}
