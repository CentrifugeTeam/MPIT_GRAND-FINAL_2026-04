import type { AnalyticsHistoryItem } from "@/features/analytics/api/analytics-api";
import type { AnalyticsChatEntry } from "@/features/analytics/model/analytics-chat-store";
import type { NlSqlWsPayload } from "@/entities/analytics";

function jobHistoryToNlPayload(
  item: Extract<AnalyticsHistoryItem, { entry_kind: "sql_job" }>,
): NlSqlWsPayload | null {
  const st = item.status;
  if (st === "pending" || st === "processing") return null;
  if (st === "error") {
    return {
      job_id: item.job_id,
      status: "error",
      error: item.error ?? undefined,
      question: item.question,
      sql: item.sql ?? undefined,
    };
  }
  if (st === "done") {
    const r = item.result;
    if (r && typeof r === "object") {
      return {
        type: "nl_sql_result",
        job_id: item.job_id,
        status: "done",
        question: item.question,
        ...r,
      } as NlSqlWsPayload;
    }
    return {
      job_id: item.job_id,
      status: "done",
      question: item.question,
      sql: item.sql ?? undefined,
      explanation: item.explanation ?? undefined,
    };
  }
  return null;
}

export function historyItemToChatEntry(item: AnalyticsHistoryItem): AnalyticsChatEntry {
  if (item.entry_kind === "nl_chat") {
    const label =
      (item.chat_title && item.chat_title.trim()) ||
      item.question ||
      "—";
    return {
      id: item.conversation_id,
      kind: "nl_chat",
      conversationId: item.conversation_id,
      question: label,
      maxRows: null,
      createdAt: new Date(item.created_at).getTime(),
      result: null,
    };
  }
  return {
    id: item.job_id,
    kind: "sql_job",
    jobId: item.job_id,
    question: item.question,
    maxRows: item.max_rows ?? null,
    createdAt: new Date(item.created_at).getTime(),
    result: jobHistoryToNlPayload(item),
  };
}
