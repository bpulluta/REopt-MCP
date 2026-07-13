/** MCP tool definitions and handlers for the REopt server. */

// Load .env into process.env before any module reads env at import time
// (config.ts populates top-level consts from process.env). Must stay first.
import "dotenv/config";

import { McpServer } from "@modelcontextprotocol/server";
import { serveStdio } from "@modelcontextprotocol/server/stdio";
import type { ToolAnnotations } from "@modelcontextprotocol/server";
import * as z from "zod";

import { applyTlsConfig, warnIfUnconfigured } from "./config.js";
import {
  getJobData,
  pollUntilComplete,
  submitJob,
  truncateLargeArrays,
} from "./client.js";
import { HttpStatusError } from "./http.js";
import { KNOWN_TECHNOLOGIES, VALID_DOE_REFERENCE_NAMES } from "./constants.js";
import { DEFAULT_INSTRUCTIONS } from "./instructions.js";
import { getAllExamples, getBaseInputs, getTariffHelp } from "./examples.js";
import { normalizeScenario } from "./sections.js";
import {
  buildSubmitSummary,
  formatFinancialSummary,
  formatResultsSummary,
  formatSystemSummary,
} from "./summaries.js";
import { searchUrdbRates } from "./urdb.js";
import {
  guidanceForErrors,
  scenarioWarnings,
  validateScenario,
} from "./validation.js";

type Dict = Record<string, unknown>;

const READ_ONLY: ToolAnnotations = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: true,
};

const MUTATING: ToolAnnotations = {
  readOnlyHint: false,
  destructiveHint: false,
  idempotentHint: false,
  openWorldHint: true,
};

const SUMMARY_FORMATTERS: Record<string, (outputs: Dict) => string> = {
  results: formatResultsSummary,
  financial: formatFinancialSummary,
  system: formatSystemSummary,
};

type ToolResult = { content: { type: "text"; text: string }[] };

function text(payload: unknown): ToolResult {
  const body =
    typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  return { content: [{ type: "text", text: body }] };
}

function errorResult(
  message: string,
  opts: { status?: string; next_step?: string } & Dict = {},
): ToolResult {
  const { status = "invalid_request", next_step, ...extra } = opts;
  const body: Dict = { status, error: message };
  if (next_step) body.next_step = next_step;
  Object.assign(body, extra);
  return text(body);
}

function isDict(value: unknown): value is Dict {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function requestedTechnologies(scenario: Dict): string[] {
  return [...KNOWN_TECHNOLOGIES].sort().filter((tech) => tech in scenario);
}

// --- Tool handlers ---------------------------------------------------------

async function submitAndWait(args: {
  scenario?: Dict;
  confirm?: boolean;
  max_wait_seconds?: number;
}): Promise<ToolResult> {
  const scenario = args.scenario;
  const maxWaitSeconds = args.max_wait_seconds ?? 300;
  const confirm = args.confirm ?? false;

  if (!isDict(scenario)) {
    return errorResult("'scenario' is required and must be an object.", {
      submission_status: "not_submitted",
      next_step: "Call getScenarioHelp, gather user inputs, then retry.",
    });
  }
  if (!Number.isInteger(maxWaitSeconds) || maxWaitSeconds <= 0) {
    return errorResult("'max_wait_seconds' must be a positive integer.", {
      next_step: "Use a positive integer such as 300.",
    });
  }

  const [isValid, errors] = validateScenario(scenario);
  if (!isValid) {
    return text({
      status: "validation_error",
      submission_status: "not_submitted",
      errors,
      guidance: guidanceForErrors(errors),
      scenario_received: scenario,
    });
  }

  const warnings = scenarioWarnings(scenario);

  // Compile any human-friendly shorthands into the canonical REopt payload.
  // Deterministic, so preview and confirmed submission always match.
  const normalized = normalizeScenario(scenario);

  // Human-in-the-loop gate: never submit until the user has confirmed the exact
  // inputs. Without confirm=true we return a preview and stop here.
  if (confirm !== true) {
    const preview: Dict = {
      status: "preview_required",
      submission_status: "not_submitted",
      scenario,
      technologies: requestedTechnologies(scenario),
      warnings,
      next_step:
        "Show this scenario to the user and confirm the inputs are " +
        "correct. Once approved, call submitAndWait again with the same " +
        "scenario and confirm=true to run the optimization.",
    };
    if (JSON.stringify(normalized) !== JSON.stringify(scenario)) {
      // Shorthand was expanded; show the compiled payload with large arrays
      // collapsed to summary stats so the user sees exactly what REopt receives.
      preview.normalized_preview = truncateLargeArrays(normalized);
    }
    return text(preview);
  }

  try {
    const runUuid = await submitJob(normalized);
    if (!isNonEmptyString(runUuid)) {
      return errorResult("REopt API did not return a valid run_uuid.", {
        status: "error",
        submission_status: "not_submitted",
        next_step: "Check NLR_API_KEY and retry.",
      });
    }

    const pollResult = await pollUntilComplete(runUuid, maxWaitSeconds);
    if (pollResult.status !== "complete") {
      return text(pollResult);
    }

    const outputs = (pollResult.result.outputs as Dict) ?? {};
    return text({
      status: "success",
      submission_status: "submitted",
      run_uuid: runUuid,
      elapsed_seconds: pollResult.elapsed_seconds,
      warnings,
      summary: buildSubmitSummary(
        runUuid,
        pollResult.elapsed_seconds,
        pollResult.job_status,
        outputs,
      ),
      outputs,
      messages: pollResult.result.messages ?? {},
    });
  } catch (error) {
    if (error instanceof HttpStatusError) {
      return errorResult(`HTTP ${error.status}`, {
        status: "error",
        detail: error.body,
      });
    }
    return errorResult(error instanceof Error ? error.message : String(error), {
      status: "error",
    });
  }
}

function validateScenarioTool(scenario: unknown): ToolResult {
  if (!isDict(scenario)) {
    return errorResult("'scenario' is required and must be an object.", {
      next_step: "Provide a scenario object to validate.",
    });
  }

  const [isValid, errors] = validateScenario(scenario);
  if (isValid) {
    return text({
      status: "valid",
      message: "Scenario is valid and ready for submission.",
      scenario,
    });
  }

  return text({
    status: "invalid",
    errors,
    guidance: guidanceForErrors(errors),
    message: "Scenario needs more information before submission.",
  });
}

function getScenarioHelp(name: string): ToolResult {
  const allExamples = getAllExamples();
  const validNames = ["minimal", "tariff", "all", ...Object.keys(allExamples).sort()];

  if (name === "minimal") {
    return text({
      status: "success",
      name: "minimal",
      scenario: getBaseInputs(),
      building_types: [...VALID_DOE_REFERENCE_NAMES].sort(),
      supported_technologies: [...KNOWN_TECHNOLOGIES].sort(),
      notes: [
        "ElectricLoad needs both doe_reference_name and annual_kwh.",
        "Add empty {} for each technology to evaluate (PV, ElectricStorage, Wind, Generator).",
        "On-grid scenarios require ElectricTariff. Rate modes: blended annual, monthly, time-of-use (tou_energy_schedule), or a URDB label. See getScenarioHelp('tariff').",
        "Don't know the URDB label? Use searchUrdbRates with the utility name or ZIP.",
        "Off-grid: set Settings.off_grid_flag=true and omit ElectricTariff.",
        "submitAndWait previews first; call again with confirm=true after the user approves.",
      ],
    });
  }

  if (name === "tariff") {
    return text(getTariffHelp());
  }

  if (name === "all") {
    const examples: Dict = {};
    for (const [key, item] of Object.entries(allExamples)) {
      examples[key] = {
        name: item.name,
        description: item.description,
        scenario: item.scenario,
      };
    }
    return text({ status: "success", examples });
  }

  if (name in allExamples) {
    const item = allExamples[name];
    return text({
      status: "success",
      name,
      title: item.name,
      description: item.description,
      scenario: item.scenario,
    });
  }

  return errorResult(`Unknown example '${name}'.`, {
    next_step: `Use one of: ${validNames.join(", ")}`,
  });
}

async function getSummary(runUuid: unknown, kind: string): Promise<ToolResult> {
  if (!isNonEmptyString(runUuid)) {
    return errorResult("'run_uuid' is required and must be a non-empty string.", {
      next_step: "Call submitAndWait first, then pass the returned run_uuid.",
    });
  }

  if (!(kind in SUMMARY_FORMATTERS) && kind !== "all") {
    return errorResult(`Unknown kind '${kind}'.`, {
      next_step: `Use one of: ${[...Object.keys(SUMMARY_FORMATTERS), "all"].join(", ")}`,
    });
  }

  let result: Dict;
  try {
    result = await getJobData(runUuid);
  } catch (error) {
    if (error instanceof HttpStatusError) {
      return errorResult(
        `HTTP ${error.status} fetching results for '${runUuid}'.`,
        {
          status: "error",
          detail: error.body,
          next_step: "Verify the run_uuid and NLR_API_KEY, then retry.",
        },
      );
    }
    return errorResult(
      `Could not fetch results for '${runUuid}': ${
        error instanceof Error ? error.message : String(error)
      }`,
      {
        status: "error",
        next_step: "Verify the run_uuid from submitAndWait and retry.",
      },
    );
  }

  const outputs = result.outputs;
  if (!isDict(outputs) || Object.keys(outputs).length === 0) {
    return errorResult(`No results available for run '${runUuid}'.`, {
      status: "error",
      job_status: result.status,
      next_step:
        "The job may still be running or may have failed; check submitAndWait output.",
    });
  }

  if (kind === "all") {
    const sections = [
      formatResultsSummary(outputs),
      formatFinancialSummary(outputs),
      formatSystemSummary(outputs),
    ];
    return { content: [{ type: "text", text: sections.join("\n\n---\n\n") }] };
  }

  return {
    content: [{ type: "text", text: SUMMARY_FORMATTERS[kind](outputs) }],
  };
}

async function searchUrdbRatesTool(args: {
  utility?: string;
  address?: string;
  sector?: string;
  rate_name?: string;
  limit?: number;
}): Promise<ToolResult> {
  const { utility, address } = args;
  if (!isNonEmptyString(utility) && !isNonEmptyString(address)) {
    return errorResult("Provide 'utility' and/or 'address' to search URDB.", {
      next_step: "Ask the user for their utility company name or ZIP code.",
    });
  }

  let limit = args.limit ?? 10;
  if (!Number.isInteger(limit) || limit <= 0) limit = 10;

  try {
    const results = await searchUrdbRates({
      utility: isNonEmptyString(utility) ? utility : null,
      address: isNonEmptyString(address) ? address : null,
      sector: isNonEmptyString(args.sector) ? args.sector : null,
      rate_name: isNonEmptyString(args.rate_name) ? args.rate_name : null,
      limit,
    });

    return text({
      status: "success",
      count: results.length,
      rates: results,
      next_step:
        results.length > 0
          ? "Show these to the user. Once they choose one, set " +
            "ElectricTariff.urdb_label to its 'label' value."
          : "No rates found. Try a different utility name or ZIP code.",
    });
  } catch (error) {
    if (error instanceof HttpStatusError) {
      return errorResult(`HTTP ${error.status} from URDB.`, {
        status: "error",
        detail: error.body,
      });
    }
    return errorResult(error instanceof Error ? error.message : String(error), {
      status: "error",
    });
  }
}

// --- Server wiring ---------------------------------------------------------

const scenarioSchema = z.record(z.string(), z.unknown());

function createServer(): McpServer {
  const server = new McpServer(
    { name: "reopt-mcp", version: "0.4.0" },
    { instructions: DEFAULT_INSTRUCTIONS },
  );

  server.registerTool(
    "submitAndWait",
    {
      description:
        "Validate and (once confirmed) submit a REopt scenario, poll until " +
        "complete, and return results. Requires Site (lat/lon), ElectricLoad " +
        "(doe_reference_name + annual_kwh), ElectricTariff (blended rates or " +
        "urdb_label), and empty {} for each requested technology (PV, " +
        "ElectricStorage, Wind, Generator). TWO-STEP GATE: call first WITHOUT " +
        "confirm to get a preview of the exact scenario for the user to review; " +
        "only after the user approves, call again with confirm=true to actually " +
        "submit. Ask the user for missing values before calling.",
      inputSchema: z.object({
        scenario: scenarioSchema.optional().describe("Complete REopt scenario JSON."),
        confirm: z
          .boolean()
          .optional()
          .describe(
            "Must be true to actually submit. When false/omitted, the tool " +
              "validates and returns a preview WITHOUT submitting so the user " +
              "can confirm inputs first.",
          ),
        max_wait_seconds: z
          .number()
          .optional()
          .describe("Max poll time in seconds (default 300)."),
      }),
      annotations: MUTATING,
    },
    async (args) => submitAndWait(args),
  );

  server.registerTool(
    "validateScenario",
    {
      description:
        "Check a scenario for missing or invalid fields before submission. " +
        "Returns errors and guidance on what to ask the user.",
      inputSchema: z.object({
        scenario: scenarioSchema.optional(),
      }),
      annotations: READ_ONLY,
    },
    async (args) => validateScenarioTool(args.scenario),
  );

  server.registerTool(
    "getScenarioHelp",
    {
      description:
        "Show scenario structure and examples. Use name='minimal' for required " +
        "fields, 'tariff' for the electricity rate guide (blended / monthly / " +
        "time-of-use / URDB), 'all' for every example, or a key like 'solar' or " +
        "'solar_battery'.",
      inputSchema: z.object({
        name: z
          .string()
          .optional()
          .describe(
            "minimal | tariff | all | solar | solar_battery | monthly_rates | tou_rates | urdb | pv_and_storage | resilience | wind",
          ),
      }),
      annotations: READ_ONLY,
    },
    async (args) => getScenarioHelp(args.name ?? "minimal"),
  );

  server.registerTool(
    "getSummary",
    {
      description:
        "Format optimization results as markdown. kind: results (default), " +
        "financial, system, or all.",
      inputSchema: z.object({
        run_uuid: z.string().optional().describe("Run UUID from submitAndWait."),
        kind: z.enum(["results", "financial", "system", "all"]).optional(),
      }),
      annotations: READ_ONLY,
    },
    async (args) => getSummary(args.run_uuid, args.kind ?? "results"),
  );

  server.registerTool(
    "searchUrdbRates",
    {
      description:
        "Search the Utility Rate Database (URDB) for a utility's published " +
        "rates. Provide 'utility' (name) and/or 'address' (address or ZIP); " +
        "returns candidate rates with their urdb_label. Show the options to the " +
        "user, then put the chosen label in ElectricTariff.urdb_label.",
      inputSchema: z.object({
        utility: z
          .string()
          .optional()
          .describe("Utility company name, e.g. 'Pacific Gas & Electric Co'."),
        address: z
          .string()
          .optional()
          .describe("Address or ZIP code to search near."),
        sector: z
          .string()
          .optional()
          .describe("Residential | Commercial | Industrial | Lighting."),
        rate_name: z
          .string()
          .optional()
          .describe("Optional substring filter on the rate name."),
        limit: z
          .number()
          .optional()
          .describe("Max candidates to return (default 10)."),
      }),
      annotations: READ_ONLY,
    },
    async (args) => searchUrdbRatesTool(args),
  );

  return server;
}

applyTlsConfig();
warnIfUnconfigured();
void serveStdio(createServer);
console.error("reopt-mcp MCP server running on stdio");
