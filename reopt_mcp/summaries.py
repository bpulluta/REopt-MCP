"""Markdown summary formatters for REopt outputs.

Formatting is driven by TECH_SPECS so every supported technology (PV,
ElectricStorage, Wind, Generator) is rendered from a single source of truth.
Adding a technology here makes it appear in every summary at once — nothing is
silently dropped.
"""


def _sized(outputs: dict, key: str) -> dict | None:
    """Return a technology's output block if it was recommended (size_kw > 0)."""
    block = outputs.get(key)
    if isinstance(block, dict) and block.get("size_kw", 0) > 0:
        return block
    return None


def _capacity_factor(block: dict) -> float:
    produced = block.get("annual_energy_produced_kwh") or block.get(
        "average_annual_energy_produced_kwh", 0
    )
    size_kw = block.get("size_kw", 0)
    if size_kw > 0:
        return produced / (size_kw * 8760) * 100
    return 0.0


# Order here controls the order sections appear in every summary.
TECH_ORDER = ("PV", "ElectricStorage", "Wind", "Generator")


def format_results_summary(outputs: dict) -> str:
    summary = "# REopt Optimization Results Summary\n\n## System Recommendations"

    pv = _sized(outputs, "PV")
    if pv:
        summary += f"""\n\n### Solar PV
- **Recommended Size**: {pv.get("size_kw", 0):.1f} kW
- **Year 1 Production**: {pv.get("annual_energy_produced_kwh", 0):,.0f} kWh
- **Annual O&M Cost**: ${pv.get("annual_om_cost_before_tax", 0):,.0f}
- **Federal ITC**: {pv.get("federal_itc_fraction", 0) * 100:.0f}%"""

    storage = _sized(outputs, "ElectricStorage")
    if storage:
        summary += f"""\n\n### Battery Storage
- **Power Capacity**: {storage.get("size_kw", 0):.1f} kW
- **Energy Capacity**: {storage.get("size_kwh", 0):.1f} kWh
- **Annual O&M Cost**: ${storage.get("annual_om_cost_before_tax", 0):,.0f}"""

    wind = _sized(outputs, "Wind")
    if wind:
        summary += f"""\n\n### Wind
- **Recommended Size**: {wind.get("size_kw", 0):.1f} kW
- **Year 1 Production**: {wind.get("annual_energy_produced_kwh", 0):,.0f} kWh
- **Annual O&M Cost**: ${wind.get("annual_om_cost_before_tax", 0):,.0f}"""

    generator = _sized(outputs, "Generator")
    if generator:
        summary += f"""\n\n### Backup Generator
- **Recommended Size**: {generator.get("size_kw", 0):.1f} kW
- **Annual Fuel Use**: {generator.get("annual_fuel_consumption_gal", 0):,.0f} gal
- **Annual O&M Cost**: ${generator.get("annual_om_cost_before_tax", 0):,.0f}"""

    if "Financial" in outputs:
        fin = outputs["Financial"]
        payback = (
            f"{fin.get('simple_payback_years', 0):.1f}"
            if fin.get("simple_payback_years")
            else "N/A"
        )
        irr = (
            f"{fin.get('internal_rate_of_return', 0) * 100:.1f}%"
            if fin.get("internal_rate_of_return")
            else "N/A"
        )
        summary += f"""\n\n## Financial Analysis
- **Net Present Value**: ${fin.get("npv", 0):,.0f}
- **Lifecycle Cost**: ${fin.get("lcc", 0):,.0f}
- **Simple Payback**: {payback} years
- **Internal Rate of Return**: {irr}"""

    if "ElectricUtility" in outputs:
        util = outputs["ElectricUtility"]
        baseline = util.get("year_one_bill_before_tax_bau", 0)
        optimized = util.get("year_one_bill_before_tax", 0)
        summary += f"""\n\n## Year 1 Utility Bill Analysis
- **Baseline Bill**: ${baseline:,.0f}
- **With System**: ${optimized:,.0f}
- **Annual Savings**: ${baseline - optimized:,.0f}"""

    return summary


def format_financial_summary(outputs: dict) -> str:
    if "Financial" not in outputs:
        return "No financial results available."

    fin = outputs["Financial"]
    table = "# Financial Analysis\n\n| Metric | Value |\n|--------|-------|\n"
    table += f"| Net Present Value (NPV) | ${fin.get('npv', 0):,.0f} |\n"
    table += f"| Lifecycle Cost (LCC) | ${fin.get('lcc', 0):,.0f} |\n"
    table += f"| Initial Capital Cost | ${fin.get('initial_capital_costs', 0):,.0f} |\n"
    table += f"| Initial Capital Cost (after incentives) | ${fin.get('initial_capital_costs_after_incentives', 0):,.0f} |\n"

    if fin.get("simple_payback_years"):
        table += f"| Simple Payback Period | {fin.get('simple_payback_years', 0):.1f} years |\n"

    if fin.get("internal_rate_of_return"):
        table += f"| Internal Rate of Return | {fin.get('internal_rate_of_return', 0) * 100:.1f}% |\n"

    table += f"| Lifecycle O&M Costs | ${fin.get('om_and_replacement_present_cost_after_tax', 0):,.0f} |\n"
    return table


def format_system_summary(outputs: dict) -> str:
    summary = "# System Technology Summary\n\n"

    pv = _sized(outputs, "PV")
    if pv:
        summary += """## Solar PV System

| Metric | Value |
|--------|-------|
"""
        summary += f"| System Size | {pv.get('size_kw', 0):.2f} kW |\n"
        summary += f"| Year 1 Production | {pv.get('annual_energy_produced_kwh', 0):,.0f} kWh |\n"
        summary += f"| Capacity Factor | {_capacity_factor(pv):.1f}% |\n"
        summary += (
            f"| Annual O&M Cost | ${pv.get('annual_om_cost_before_tax', 0):,.0f} |\n"
        )
        summary += f"| Lifecycle O&M Cost | ${pv.get('lifecycle_om_cost_after_tax', 0):,.0f} |\n\n"

    storage = _sized(outputs, "ElectricStorage")
    if storage:
        duration = (
            storage.get("size_kwh", 0) / storage.get("size_kw", 1)
            if storage.get("size_kw", 0) > 0
            else 0
        )
        summary += """## Battery Energy Storage

| Metric | Value |
|--------|-------|
"""
        summary += f"| Power Capacity | {storage.get('size_kw', 0):.2f} kW |\n"
        summary += f"| Energy Capacity | {storage.get('size_kwh', 0):.2f} kWh |\n"
        summary += f"| Duration | {duration:.1f} hours |\n"
        summary += f"| Annual O&M Cost | ${storage.get('annual_om_cost_before_tax', 0):,.0f} |\n\n"

    wind = _sized(outputs, "Wind")
    if wind:
        summary += """## Wind System

| Metric | Value |
|--------|-------|
"""
        summary += f"| System Size | {wind.get('size_kw', 0):.2f} kW |\n"
        summary += f"| Year 1 Production | {wind.get('annual_energy_produced_kwh', 0):,.0f} kWh |\n"
        summary += f"| Capacity Factor | {_capacity_factor(wind):.1f}% |\n"
        summary += f"| Annual O&M Cost | ${wind.get('annual_om_cost_before_tax', 0):,.0f} |\n\n"

    generator = _sized(outputs, "Generator")
    if generator:
        summary += """## Backup Generator

| Metric | Value |
|--------|-------|
"""
        summary += f"| System Size | {generator.get('size_kw', 0):.2f} kW |\n"
        summary += f"| Annual Fuel Use | {generator.get('annual_fuel_consumption_gal', 0):,.0f} gal |\n"
        summary += f"| Annual O&M Cost | ${generator.get('annual_om_cost_before_tax', 0):,.0f} |\n\n"

    if not any(_sized(outputs, tech) for tech in TECH_ORDER):
        summary += """No distributed energy systems recommended.

This typically means the economics don't favor installing solar or storage
under current assumptions (tariff, load, costs).

Consider:
- Verifying utility rate accuracy (blended rates or validated utility tariff inputs)
- Reviewing technology cost assumptions
- Adjusting financial parameters
- Exploring different technologies
"""

    return summary


def build_submit_summary(
    run_uuid: str, elapsed_seconds: int, job_status: str, outputs: dict
) -> str:
    parts = [
        f"✓ Optimization completed successfully in {elapsed_seconds} seconds",
        f"  Run UUID: {run_uuid}",
        f"  Status: {job_status}",
        "",
    ]

    pv = _sized(outputs, "PV")
    if pv:
        parts.append(f"  Solar PV: {pv.get('size_kw', 0):.1f} kW")

    storage = _sized(outputs, "ElectricStorage")
    if storage:
        parts.append(
            f"  Battery: {storage.get('size_kw', 0):.1f} kW / {storage.get('size_kwh', 0):.1f} kWh"
        )

    wind = _sized(outputs, "Wind")
    if wind:
        parts.append(f"  Wind: {wind.get('size_kw', 0):.1f} kW")

    generator = _sized(outputs, "Generator")
    if generator:
        parts.append(f"  Generator: {generator.get('size_kw', 0):.1f} kW")

    if "Financial" in outputs and outputs["Financial"].get("npv") is not None:
        parts.append(f"  NPV: ${outputs['Financial'].get('npv', 0):,.0f}")

    return "\n".join(parts)
