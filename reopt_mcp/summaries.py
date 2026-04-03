"""Markdown summary formatters for REopt outputs."""


def format_results_summary(outputs: dict) -> str:
    summary = "# REopt Optimization Results Summary\n\n## System Recommendations"

    if "PV" in outputs and outputs["PV"].get("size_kw", 0) > 0:
        pv = outputs["PV"]
        summary += f"""\n\n### Solar PV
- **Recommended Size**: {pv.get('size_kw', 0):.1f} kW
- **Year 1 Production**: {pv.get('annual_energy_produced_kwh', 0):,.0f} kWh
- **Annual O&M Cost**: ${pv.get('annual_om_cost_before_tax', 0):,.0f}
- **Federal ITC**: {pv.get('federal_itc_fraction', 0)*100:.0f}%"""

    if (
        "ElectricStorage" in outputs
        and outputs["ElectricStorage"].get("size_kw", 0) > 0
    ):
        storage = outputs["ElectricStorage"]
        summary += f"""\n\n### Battery Storage
- **Power Capacity**: {storage.get('size_kw', 0):.1f} kW
- **Energy Capacity**: {storage.get('size_kwh', 0):.1f} kWh
- **Annual O&M Cost**: ${storage.get('annual_om_cost_before_tax', 0):,.0f}"""

    if "Financial" in outputs:
        fin = outputs["Financial"]
        payback = (
            f"{fin.get('simple_payback_years', 0):.1f}"
            if fin.get("simple_payback_years")
            else "N/A"
        )
        irr = (
            f"{fin.get('internal_rate_of_return', 0)*100:.1f}%"
            if fin.get("internal_rate_of_return")
            else "N/A"
        )
        summary += f"""\n\n## Financial Analysis
- **Net Present Value**: ${fin.get('npv', 0):,.0f}
- **Lifecycle Cost**: ${fin.get('lcc', 0):,.0f}
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
        table += f"| Internal Rate of Return | {fin.get('internal_rate_of_return', 0)*100:.1f}% |\n"

    table += f"| Lifecycle O&M Costs | ${fin.get('om_and_replacement_present_cost_after_tax', 0):,.0f} |\n"
    return table


def format_system_summary(outputs: dict) -> str:
    summary = "# System Technology Summary\n\n"

    if "PV" in outputs and outputs["PV"].get("size_kw", 0) > 0:
        pv = outputs["PV"]
        cf = (
            pv.get("average_annual_energy_produced_kwh", 0)
            / (pv.get("size_kw", 1) * 8760)
            * 100
            if pv.get("size_kw", 0) > 0
            else 0
        )
        summary += """## Solar PV System

| Metric | Value |
|--------|-------|
"""
        summary += f"| System Size | {pv.get('size_kw', 0):.2f} kW |\n"
        summary += f"| Year 1 Production | {pv.get('annual_energy_produced_kwh', 0):,.0f} kWh |\n"
        summary += f"| Capacity Factor | {cf:.1f}% |\n"
        summary += (
            f"| Annual O&M Cost | ${pv.get('annual_om_cost_before_tax', 0):,.0f} |\n"
        )
        summary += f"| Lifecycle O&M Cost | ${pv.get('lifecycle_om_cost_after_tax', 0):,.0f} |\n\n"

    if (
        "ElectricStorage" in outputs
        and outputs["ElectricStorage"].get("size_kw", 0) > 0
    ):
        storage = outputs["ElectricStorage"]
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

    if "PV" not in outputs and "ElectricStorage" not in outputs:
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

    if "PV" in outputs and outputs["PV"].get("size_kw", 0) > 0:
        parts.append(f"  Solar PV: {outputs['PV']['size_kw']:.1f} kW")

    if (
        "ElectricStorage" in outputs
        and outputs["ElectricStorage"].get("size_kw", 0) > 0
    ):
        storage = outputs["ElectricStorage"]
        parts.append(
            f"  Battery: {storage['size_kw']:.1f} kW / {storage['size_kwh']:.1f} kWh"
        )

    if "Financial" in outputs:
        parts.append(f"  NPV: ${outputs['Financial']['npv']:,.0f}")

    return "\n".join(parts)
