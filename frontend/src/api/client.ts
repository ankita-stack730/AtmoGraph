import { MOCK_GRAPH, MOCK_HEALTH, mockDisruption, mockNlp, mockNodeDetail } from "./mock";
import type {
  DisruptionResponse,
  GraphResponse,
  HealthResponse,
  NlpAnalyzeResponse,
  NodeDetail,
} from "./types";

export const API_BASE_URL =
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "http://127.0.0.1:8000";

export type SourceMode = "live" | "demo";

export interface ApiResult<T> {
  data: T;
  source: SourceMode;
  error?: string;
}

const TIMEOUT_MS = 4000;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

async function withFallback<T>(path: string, fallback: () => T, init?: RequestInit): Promise<ApiResult<T>> {
  if (typeof window === "undefined") {
    return { data: fallback(), source: "demo", error: "server-render" };
  }
  try {
    const data = await request<T>(path, init);
    return { data, source: "live" };
  } catch (err) {
    return {
      data: fallback(),
      source: "demo",
      error: err instanceof Error ? err.message : "unreachable",
    };
  }
}

export const api = {
  health: () => withFallback<HealthResponse>("/health", () => MOCK_HEALTH),

  graph: () => withFallback<GraphResponse>("/graph", () => MOCK_GRAPH),

  node: (nodeId: string) =>
    withFallback<NodeDetail>(`/graph/node/${encodeURIComponent(nodeId)}`, () =>
      mockNodeDetail(nodeId),
    ),

  nlpAnalyze: (text: string) =>
    withFallback<NlpAnalyzeResponse>("/nlp/analyze", () => mockNlp(text), {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  disruptionAnalyze: (text: string) =>
    withFallback<DisruptionResponse>("/disruption/analyze", () => mockDisruption(text), {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
};

export const SAMPLE_DISRUPTION = "Rotterdam port strike causes major shipping delays.";
