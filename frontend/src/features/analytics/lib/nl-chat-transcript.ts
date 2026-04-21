import type { ChartPayloadShape } from "@/entities/analytics";

import type { NlChatLine } from "@/features/analytics/lib/nl-chat-line";

export type NlChatMessageApiRow = {
  id: string;
  role: string;
  payload: Record<string, unknown>;
  created_at: string;
};

function pickChartPayload(raw: unknown): ChartPayloadShape | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const o = raw as Record<string, unknown>;
  if (Object.keys(o).length === 0) return undefined;
  return raw as ChartPayloadShape;
}

function pickStringArray(raw: unknown): string[] | undefined {
  if (!Array.isArray(raw)) return undefined;
  return raw.map((x) => String(x));
}

function pickRows(raw: unknown): Record<string, unknown>[] | undefined {
  if (!Array.isArray(raw)) return undefined;
  const out: Record<string, unknown>[] = [];
  for (const r of raw) {
    if (r && typeof r === "object" && !Array.isArray(r)) {
      out.push(r as Record<string, unknown>);
    }
  }
  return out.length ? out : undefined;
}

/** Строка из GET /api/analytics/chats/:id/messages → лента UI. */
export function apiNlMessageToLine(row: NlChatMessageApiRow): NlChatLine {
  const pl = row.payload;
  const text = String(pl.text ?? "");
  const report = pl.report != null ? String(pl.report) : "";
  const body =
    row.role === "assistant" && report
      ? `${text}\n\n${report}`.trim()
      : text;
  const sql = pl.sql != null ? String(pl.sql) : null;
  const rc = pl.row_count;
  return {
    id: row.id,
    role: row.role as NlChatLine["role"],
    text: body || " ",
    sql,
    chartPayload: pickChartPayload(pl.chart_payload),
    columns: pickStringArray(pl.columns),
    rows: pickRows(pl.rows),
    rowCount: typeof rc === "number" ? rc : undefined,
  };
}
