/** The standard tool response envelope.
 *
 * Every MCP tool returns a single text content block whose body is JSON (or raw
 * markdown for rendered summaries). Structured responses share a predictable
 * shape:
 *   - `status`            — machine-readable outcome (e.g. "success", "error",
 *                           "validation_error", "preview_required").
 *   - `next_step`         — optional instruction to the calling agent.
 *   - `submission_status` — present on submit-related responses ("submitted" /
 *                           "not_submitted") so the agent never assumes a run
 *                           happened when it didn't.
 * Keeping this in one place means all tools stay consistent.
 */

import type { Dict } from "./guards.js";

export type ToolResult = { content: { type: "text"; text: string }[] };

/** Wrap a payload as a tool result. Objects are pretty-printed JSON; strings pass
 * through verbatim (used for already-rendered markdown). */
export function text(payload: unknown): ToolResult {
  const body =
    typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  return { content: [{ type: "text", text: body }] };
}

/** Build a standard error envelope. Defaults `status` to "invalid_request". */
export function errorResult(
  message: string,
  opts: { status?: string; next_step?: string } & Dict = {},
): ToolResult {
  const { status = "invalid_request", next_step, ...extra } = opts;
  const body: Dict = { status, error: message };
  if (next_step) body.next_step = next_step;
  Object.assign(body, extra);
  return text(body);
}
