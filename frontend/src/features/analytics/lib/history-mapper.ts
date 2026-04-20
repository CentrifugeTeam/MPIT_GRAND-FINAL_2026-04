import type { JobHistoryItem } from "@/features/analytics/api/analytics-api";
import type { AnalyticsChatEntry } from "@/features/analytics/model/analytics-chat-store";
import type { NlSqlWsPayload } from "@/entities/analytics/types";

function jobHistoryToNlPayload(item: JobHistoryItem): NlSqlWsPayload | null {
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

export function historyItemToChatEntry(item: JobHistoryItem): AnalyticsChatEntry {
  return {
    id: item.job_id,
    jobId: item.job_id,
    question: item.question,
    maxRows: item.max_rows ?? null,
    createdAt: new Date(item.created_at).getTime(),
    result: jobHistoryToNlPayload(item),
  };
}
