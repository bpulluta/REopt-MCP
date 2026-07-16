/** Generator (backup) technology module. */

import { type Dict } from "../guards.js";
import { comma0, fixed1, fixed2 } from "../format.js";
import { techBlock } from "./helpers.js";
import type { ScenarioModule } from "./types.js";

export class GeneratorModule implements ScenarioModule {
  readonly key = "Generator";
  readonly kind = "technology" as const;
  readonly label = "Backup Generator";

  example(): Dict {
    return {};
  }

  summarizeResults(outputs: Dict): string {
    const generator = techBlock(outputs, this.key);
    return `\n\n### Backup Generator
- **Recommended Size**: ${fixed1(generator.size_kw)} kW
- **Annual Fuel Use**: ${comma0(generator.annual_fuel_consumption_gal)} gal
- **Annual O&M Cost**: $${comma0(generator.annual_om_cost_before_tax)}`;
  }

  summarizeSystem(outputs: Dict): string {
    const generator = techBlock(outputs, this.key);
    let s = "## Backup Generator\n\n| Metric | Value |\n|--------|-------|\n";
    s += `| System Size | ${fixed2(generator.size_kw)} kW |\n`;
    s += `| Annual Fuel Use | ${comma0(generator.annual_fuel_consumption_gal)} gal |\n`;
    s += `| Annual O&M Cost | $${comma0(generator.annual_om_cost_before_tax)} |\n\n`;
    return s;
  }
}
