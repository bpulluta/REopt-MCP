/** REopt API client and polling helpers. */

import { NLR_API_KEY, REOPT_API_BASE_URL } from "./config.js";
import { httpGetJson, httpPostJson } from "./http.js";
import { roundTo } from "./format.js";

export interface PollComplete {
  status: "complete";
  job_status: string;
  result: Record<string, unknown>;
  run_uuid: string;
  elapsed_seconds: number;
  poll_count: number;
}

export interface PollTimeout {
  status: "timeout";
  message: string;
  run_uuid: string;
  elapsed_seconds: number;
}

export interface PollError {
  status: "error";
  error: string;
  run_uuid: string;
  elapsed_seconds: number;
  poll_count: number;
}

export type PollResult = PollComplete | PollTimeout | PollError;

/** Recursively truncate 8760+ timeseries arrays to summary statistics. */
export function truncateLargeArrays(data: unknown): unknown {
  if (Array.isArray(data)) {
    if (data.length >= 8760) {
      const isNumeric = data.every((x) => typeof x === "number");
      if (isNumeric) {
        const nums = data as number[];
        let sum = 0;
        let min = Infinity;
        let max = -Infinity;
        for (const x of nums) {
          sum += x;
          if (x < min) min = x;
          if (x > max) max = x;
        }
        return {
          _truncated: true,
          _type: "timeseries",
          _length: nums.length,
          _sum: roundTo(sum, 2),
          _mean: roundTo(sum / nums.length, 4),
          _min: roundTo(min, 4),
          _max: roundTo(max, 4),
        };
      }
    }
    return data.map((item) => truncateLargeArrays(item));
  }
  if (data !== null && typeof data === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(data as Record<string, unknown>)) {
      out[k] = truncateLargeArrays(v);
    }
    return out;
  }
  return data;
}

/** POST a scenario to the REopt API and return the run UUID. */
export async function submitJob(scenario: unknown): Promise<string | undefined> {
  const payload = (await httpPostJson(
    `${REOPT_API_BASE_URL}/job`,
    { api_key: NLR_API_KEY },
    scenario,
    "REopt API",
    "REOPT_API_BASE_URL",
  )) as Record<string, unknown>;
  const runUuid = payload?.run_uuid;
  return typeof runUuid === "string" ? runUuid : undefined;
}

/** GET full results for a completed REopt run. */
export async function getJobData(runUuid: string): Promise<Record<string, unknown>> {
  const payload = (await httpGetJson(
    `${REOPT_API_BASE_URL}/job/${runUuid}/results`,
    { api_key: NLR_API_KEY },
    "REopt API",
    "REOPT_API_BASE_URL",
  )) as Record<string, unknown>;
  return payload;
}

export async function getJobDataTruncated(
  runUuid: string,
): Promise<Record<string, unknown>> {
  const result = await getJobData(runUuid);
  return truncateLargeArrays(result) as Record<string, unknown>;
}

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export async function pollUntilComplete(
  runUuid: string,
  maxWaitSeconds = 300,
): Promise<PollResult> {
  const startTime = Date.now() / 1000;
  let pollInterval = 3;
  const maxInterval = 15;
  let pollCount = 0;

  for (;;) {
    pollCount += 1;
    const elapsed = Date.now() / 1000 - startTime;

    if (elapsed > maxWaitSeconds) {
      return {
        status: "timeout",
        message: `Job did not complete within ${maxWaitSeconds} seconds (polled ${pollCount} times)`,
        run_uuid: runUuid,
        elapsed_seconds: Math.trunc(elapsed),
      };
    }

    try {
      const result = await getJobDataTruncated(runUuid);
      const jobStatus =
        typeof result.status === "string" ? result.status : "Unknown";

      if (jobStatus === "optimal" || jobStatus === "not optimal") {
        return {
          status: "complete",
          job_status: jobStatus,
          result,
          run_uuid: runUuid,
          elapsed_seconds: Math.trunc(elapsed),
          poll_count: pollCount,
        };
      }

      await sleep(pollInterval * 1000);
      pollInterval = Math.min(pollInterval * 1.3, maxInterval);
    } catch (error) {
      return {
        status: "error",
        error: error instanceof Error ? error.message : String(error),
        run_uuid: runUuid,
        elapsed_seconds: Math.trunc(elapsed),
        poll_count: pollCount,
      };
    }
  }
}
