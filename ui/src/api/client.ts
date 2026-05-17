import type {
  BenchmarkReport,
  BenchmarkRunSummary,
  ConnectionTestResponse,
  ModelBackend,
  RuntimeConfig,
  TestCase
} from "./types";

export const apiBaseUrl = "/api";

export async function getResults(): Promise<BenchmarkRunSummary[]> {
  const response = await fetch(`${apiBaseUrl}/results`);
  if (!response.ok) {
    throw new Error("Unable to load results");
  }
  return (await response.json()) as BenchmarkRunSummary[];
}

export async function getResult(runId: string): Promise<BenchmarkReport> {
  const response = await fetch(`${apiBaseUrl}/results/${runId}`);
  if (!response.ok) {
    throw new Error("Unable to load result");
  }
  return (await response.json()) as BenchmarkReport;
}

export async function getCases(): Promise<TestCase[]> {
  const response = await fetch(`${apiBaseUrl}/cases`);
  if (!response.ok) {
    throw new Error("Unable to load cases");
  }
  return (await response.json()) as TestCase[];
}

export async function startBenchmark(body: {
  backend?: string | null;
  cases?: string[] | null;
}): Promise<{ run_id: string }> {
  const response = await fetch(`${apiBaseUrl}/benchmark/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error("Unable to start benchmark");
  }
  return (await response.json()) as { run_id: string };
}

export async function getConfig(): Promise<RuntimeConfig> {
  const response = await fetch(`${apiBaseUrl}/config`);
  if (!response.ok) {
    throw new Error("Unable to load config");
  }
  return (await response.json()) as RuntimeConfig;
}

export async function testConnection(body: {
  target: string;
  backend: string;
  model?: string;
  api_key?: string;
}): Promise<ConnectionTestResponse> {
  const response = await fetch(`${apiBaseUrl}/config/test-connection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error("Unable to test connection");
  }
  return (await response.json()) as ConnectionTestResponse;
}

export async function updateRuntimeConfig(body: {
  eval_judge_backend?: ModelBackend;
  eval_judge_model?: string;
  sut_backend?: ModelBackend;
  sut_model?: string;
}): Promise<RuntimeConfig> {
  const response = await fetch(`${apiBaseUrl}/config/runtime`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error("Unable to update runtime config");
  }
  return (await response.json()) as RuntimeConfig;
}
