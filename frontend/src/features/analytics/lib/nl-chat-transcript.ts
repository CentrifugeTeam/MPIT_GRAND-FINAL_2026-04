import { resolveNlAssistantVisibleText } from "./nl-chat-assistant-body";
import type { NlChatLine } from "./nl-chat-line";
import { pickChartPayload, pickRows, pickStringArray } from "./nl-chat-ws-payload";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type NlChatMessageApiRow = {
  id: string;
  role: string;
  payload: Record<string, unknown>;
  created_at: string;
};

/** Строка из GET /api/analytics/chats/:id/messages → лента UI. */
export function apiNlMessageToLine(row: NlChatMessageApiRow, t: TFn): NlChatLine {
  const pl = row.payload;
  const text = String(pl.text ?? "");
  const report = pl.report != null ? String(pl.report) : "";
  const sql = pl.sql != null ? String(pl.sql) : null;
  const rc = pl.row_count;
  const rcNum = typeof rc === "number" ? rc : undefined;
  const cols = pickStringArray(pl.columns);
  const rowObjs = pickRows(pl.rows);
  const status = String(pl.status ?? "");
  const err = pl.error != null ? String(pl.error).trim() : "";
  const reasoning =
    pl.reasoning != null ? String(pl.reasoning).trim() : "";
  const role = row.role as NlChatLine["role"];

  const body =
    role === "assistant"
      ? resolveNlAssistantVisibleText(t, {
          text,
          report,
          status,
          error: err,
          columns: cols,
          rows: rowObjs,
          sql,
          rowCount: rcNum,
        })
      : text;

  return {
    id: row.id,
    role,
    text: body.trim() || text,
    reasoning: reasoning || undefined,
    sql,
    chartPayload: pickChartPayload(pl.chart_payload),
    columns: cols,
    rows: rowObjs,
    rowCount: rcNum,
  };
}
