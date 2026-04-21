/** Эвристики бэкенда: неоднозначность запроса. */
export type QueryInterpretation = {
  confidence: number;
  warnings?: string[];
  suggestions?: string[];
};

/** Результат LLM-аналитика до генерации SQL (если включён в воркере). */
export type OrchestratorPayload = {
  proceed?: boolean;
  user_message_ru?: string;
  sql_generator_hints_ru?: string;
  risks_ru?: string;
};

/** Ответ воркера / BFF по WebSocket `nl_sql_result` (плоский JSON). */
export type NlSqlWsPayload = {
  type?: string;
  job_id: string;
  user_id?: string;
  status: "done" | "error" | string;
  question?: string;
  error?: string | null;
  sql?: string | null;
  explanation?: string | null;
  columns?: string[];
  rows?: Record<string, unknown>[];
  row_count?: number;
  chart?: { type: string; x_key?: string | null; series?: { key: string }[] };
  chart_payload?: ChartPayloadShape;
  guard_warnings?: string[];
  interpretation?: QueryInterpretation;
  orchestrator?: OrchestratorPayload;
  nl_answer?: string | null;
  report?: string | null;
};

export type ChartPayloadShape = {
  type?: string;
  xKey?: string;
  labels?: unknown[];
  series?: { key: string; label?: string; data?: unknown[] }[];
  rows?: Record<string, unknown>[];
  columns?: string[];
};
