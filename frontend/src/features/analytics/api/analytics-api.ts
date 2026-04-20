import { api } from "@/shared/api/axios";

export type GlossaryMatchApi = {
  id: string;
  title?: string | null;
  category?: string | null;
  definition: string;
};

export type AskAsyncResponse = {
  job_id: string;
  status: string;
  template_key?: string;
  message?: string;
  interpretation_confidence: number;
  interpretation_warnings: string[];
  interpretation_suggestions: string[];
  glossary_matches: GlossaryMatchApi[];
};

export type JobHistoryItem = {
  job_id: string;
  user_id: string;
  question: string;
  max_rows: number | null;
  template_key: string | null;
  status: string;
  sql: string | null;
  explanation: string | null;
  error: string | null;
  result: Record<string, unknown> | null;
  created_at: string;
  updated_at: string | null;
};

export type JobHistoryResponse = {
  items: JobHistoryItem[];
  total: number;
};

export type WebSocketTokenResponse = {
  ws_url: string;
  token: string;
  expires_in: number;
  message?: string;
};

export async function askAnalyticsAsync(
  question: string,
  maxRows?: number | null,
) {
  const body: { question: string; max_rows?: number } = { question };
  if (
    maxRows != null &&
    Number.isFinite(maxRows) &&
    maxRows > 0
  ) {
    body.max_rows = Math.min(50_000_000, Math.floor(maxRows));
  }
  const { data } = await api.post<AskAsyncResponse>(
    "/api/analytics/ask-async",
    body,
  );
  return data;
}

export async function rerunAnalyticsJobAsync(
  jobId: string,
  question: string,
  maxRows?: number | null,
) {
  const body: { question: string; max_rows?: number } = { question };
  if (maxRows != null && Number.isFinite(maxRows) && maxRows > 0) {
    body.max_rows = Math.min(50_000_000, Math.floor(maxRows));
  }
  const { data } = await api.post<AskAsyncResponse>(
    `/api/analytics/jobs/${jobId}/rerun`,
    body,
  );
  return data;
}

export async function fetchWebSocketToken() {
  const { data } = await api.post<WebSocketTokenResponse>("/api/websocket/token");
  return data;
}

export async function fetchAnalyticsHistory(limit = 50, offset = 0) {
  const { data } = await api.get<JobHistoryResponse>("/api/analytics/history", {
    params: { limit, offset },
  });
  return data;
}

export async function deleteAnalyticsJob(jobId: string) {
  await api.delete(`/api/analytics/jobs/${jobId}`);
}

export async function deleteAllAnalyticsHistory() {
  await api.delete("/api/analytics/history");
}

export type GlossaryListResponse = {
  version: number;
  total: number;
  entries: Record<string, unknown>[];
};

export async function fetchAnalyticsGlossary(q?: string, limit = 500) {
  const { data } = await api.get<GlossaryListResponse>("/api/analytics/glossary", {
    params: { q, limit },
  });
  return data;
}
