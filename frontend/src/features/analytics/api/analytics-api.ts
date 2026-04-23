import { api } from '@/shared/api/axios';
import {
  analyticsDataSourcesResponseSchema,
  analyticsHistoryResponseSchema,
  createNlChatResponseSchema,
  interpretQuestionResponseSchema,
  nlChatMessagesResponseSchema,
  websocketTokenResponseSchema,
} from '@/entities/analytics';

export type GlossaryMatchApi = {
  id: string;
  title?: string | null;
  category?: string | null;
  definition: string;
};

export type InterpretQuestionResponse = {
  interpretation_confidence: number;
  interpretation_warnings: string[];
  interpretation_suggestions: string[];
  glossary_matches: GlossaryMatchApi[];
  glossary_context: string | null;
};

export type SqlJobHistoryRow = {
  entry_kind: 'sql_job';
  sort_at: string;
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

export type NlChatHistoryRow = {
  entry_kind: 'nl_chat';
  sort_at: string;
  conversation_id: string;
  user_id: string;
  question: string;
  chat_title: string | null;
  message_count: number;
  created_at: string;
  updated_at: string | null;
};

export type AnalyticsHistoryItem = SqlJobHistoryRow | NlChatHistoryRow;

export type AnalyticsHistoryResponse = {
  items: AnalyticsHistoryItem[];
  total: number;
};

export type WebSocketTokenResponse = {
  ws_url: string;
  token: string;
  expires_in: number;
  message?: string;
};

export async function fetchInterpretQuestion(
  question: string,
  maxRows?: number | null,
  analyticsSourceKey?: string | null,
) {
  const body: {
    question: string;
    max_rows?: number;
    analytics_source_key?: string;
  } = { question };
  if (maxRows != null && Number.isFinite(maxRows) && maxRows > 0) {
    body.max_rows = Math.min(50_000_000, Math.floor(maxRows));
  }
  const sk = analyticsSourceKey?.trim();
  if (sk) body.analytics_source_key = sk;
  const { data } = await api.post<InterpretQuestionResponse>(
    '/api/analytics/interpret-question',
    body,
  );
  return interpretQuestionResponseSchema.parse(data);
}

export async function fetchWebSocketToken() {
  const { data } = await api.post<WebSocketTokenResponse>(
    '/api/websocket/token',
  );
  return websocketTokenResponseSchema.parse(data);
}

export type AnalyticsDataSourceItem = {
  key: string;
  display_name: string;
  is_default: boolean;
};

export type AnalyticsDataSourcesResponse = {
  items: AnalyticsDataSourceItem[];
  default_key: string | null;
};

export async function fetchAnalyticsDataSources() {
  const { data } = await api.get<AnalyticsDataSourcesResponse>(
    '/api/analytics/data-sources',
  );
  return analyticsDataSourcesResponseSchema.parse(data);
}

export async function fetchAnalyticsHistory(limit = 50, offset = 0) {
  const { data } = await api.get<AnalyticsHistoryResponse>(
    '/api/analytics/history',
    {
      params: { limit, offset },
    },
  );
  return analyticsHistoryResponseSchema.parse(data);
}

export async function deleteAnalyticsJob(jobId: string) {
  await api.delete(`/api/analytics/jobs/${jobId}`);
}

export async function deleteAllAnalyticsHistory() {
  await api.delete('/api/analytics/history');
}

export type CreateNlChatResponse = {
  conversation_id: string;
  created_at: string;
};

export async function createNlAnalyticsChat() {
  const { data } = await api.post<CreateNlChatResponse>('/api/analytics/chats');
  return createNlChatResponseSchema.parse(data);
}

export type NlChatMessagesResponse = {
  items: Array<{
    id: string;
    role: string;
    payload: Record<string, unknown>;
    created_at: string;
  }>;
};

export async function fetchNlChatMessages(conversationId: string) {
  const { data } = await api.get<NlChatMessagesResponse>(
    `/api/analytics/chats/${conversationId}/messages`,
  );
  return nlChatMessagesResponseSchema.parse(data);
}

export async function deleteNlChat(conversationId: string) {
  await api.delete(`/api/analytics/chats/${conversationId}`);
}

export async function patchNlChatTitle(conversationId: string, title: string) {
  await api.patch(`/api/analytics/chats/${conversationId}`, { title });
}

export type ReportTaskScheduleType =
  | 'once'
  | 'daily'
  | 'weekly'
  | 'monthly'
  | 'yearly';

export type ReportTaskSchedule = {
  schedule_type: ReportTaskScheduleType;
  timezone: string;
  once_at?: string | null;
  daily_time?: string | null;
  weekly_day?: number | null;
  weekly_time?: string | null;
  monthly_day?: number | null;
  monthly_time?: string | null;
  yearly_date_ddmm?: string | null;
  yearly_time?: string | null;
};

export type ReportTask = {
  id: string;
  title: string;
  instruction: string;
  user_id: string;
  analytics_source_key: string;
  schedule_type: ReportTaskScheduleType;
  timezone: string;
  once_at: string | null;
  daily_time: string | null;
  weekly_day: number | null;
  weekly_time: string | null;
  monthly_day: number | null;
  monthly_time: string | null;
  yearly_date_ddmm: string | null;
  yearly_time: string | null;
  is_active: boolean;
  next_run_at: string | null;
  last_run_at: string | null;
  runs_count: number;
  created_at: string;
  updated_at: string;
  last_report_sentence?: string | null;
  reports: ReportRun[];
};

export type ReportTaskListResponse = {
  items: ReportTask[];
  total: number;
};

export type ReportRun = {
  id: string;
  task_id: string | null;
  user_id: string;
  status: 'pending' | 'running' | 'done' | 'failed';
  query_text: string;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
  result_summary: string | null;
  result_payload: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type ReportRunListResponse = {
  items: ReportRun[];
  total: number;
};

export type CreateReportTaskBody = {
  title: string;
  instruction: string;
  analytics_source_key: string;
  is_active?: boolean;
  schedule: ReportTaskSchedule;
};

export type CreateReportBody = {
  task_id?: string | null;
  status?: ReportRun['status'];
  query_text: string;
  result_summary?: string | null;
  result_payload?: Record<string, unknown> | null;
  error?: string | null;
};

export async function createReportTask(body: CreateReportTaskBody) {
  const { data } = await api.post<ReportTask>('/api/analytics/tasks', body);
  return data;
}

export async function fetchReportTasks(limit = 50, offset = 0) {
  const { data } = await api.get<ReportTaskListResponse>(
    '/api/analytics/tasks',
    {
      params: { limit, offset },
    },
  );
  return data;
}

export async function fetchReportTaskById(taskId: string) {
  const { data } = await api.get<ReportTask>(`/api/analytics/tasks/${taskId}`);
  return data;
}

export async function dispatchReportTask(taskId: string) {
  const { data } = await api.post<ReportRun>(
    `/api/analytics/tasks/${taskId}/dispatch`,
  );
  return data;
}

export async function patchReportTask(
  taskId: string,
  body: Partial<CreateReportTaskBody>,
) {
  await api.post(`/api/analytics/tasks/${taskId}`, body);
}

export async function deleteReportTask(taskId: string) {
  await api.delete(`/api/analytics/tasks/${taskId}`);
}

export async function fetchReports(limit = 50, offset = 0) {
  const { data } = await api.get<ReportRunListResponse>(
    '/api/analytics/reports',
    {
      params: { limit, offset },
    },
  );
  return data;
}

export async function createReport(body: CreateReportBody) {
  const { data } = await api.post<ReportRun>('/api/analytics/reports', body);
  return data;
}

export async function fetchReportById(reportId: string) {
  const { data } = await api.get<ReportRun>(
    `/api/analytics/reports/${reportId}`,
  );
  return data;
}

export async function patchReport(
  reportId: string,
  body: Partial<CreateReportBody>,
) {
  await api.patch(`/api/analytics/reports/${reportId}`, body);
}

export async function deleteReport(reportId: string) {
  await api.delete(`/api/analytics/reports/${reportId}`);
}
