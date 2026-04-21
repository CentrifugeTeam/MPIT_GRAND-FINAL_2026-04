import type { MutableRefObject } from "react";

import {
  pickChartPayload,
  pickRows,
  pickStringArray,
} from "@/features/analytics/lib/nl-chat-ws-payload";
import type { NlChatLine } from "@/features/analytics/lib/nl-chat-line";
import { wsClient } from "@/shared/api/ws-client";

type TRef = MutableRefObject<(key: string, opts?: Record<string, unknown>) => string>;

/** Подписка на события чата; отписка в возвращаемой функции. */
export function subscribeNlChatWs(
  routingCidRef: MutableRefObject<string | null>,
  tRef: TRef,
  appendLine: (line: NlChatLine) => void,
  setNlChatBusy: (v: boolean) => void,
): () => void {
  const unsubs: Array<() => void> = [];
  unsubs.push(
    wsClient.on("chat_assistant", (payload: Record<string, unknown>) => {
      if (String(payload.conversation_id ?? "") !== String(routingCidRef.current ?? ""))
        return;
      const text = String(payload.text ?? "");
      const rep = payload.report ? String(payload.report) : "";
      const sql = payload.sql != null ? String(payload.sql) : null;
      const body = rep ? `${text}\n\n${rep}`.trim() : text;
      const rc = payload.row_count;
      appendLine({
        id: String(payload.message_id ?? crypto.randomUUID()),
        role: "assistant",
        text: body || tRef.current("home.analytics.chatEmptyAssistant"),
        sql,
        chartPayload: pickChartPayload(payload.chart_payload),
        columns: pickStringArray(payload.columns),
        rows: pickRows(payload.rows),
        rowCount: typeof rc === "number" ? rc : undefined,
      });
      setNlChatBusy(false);
    }),
  );
  unsubs.push(
    wsClient.on("chat_sql_queued", (payload: Record<string, unknown>) => {
      if (String(payload.conversation_id ?? "") !== String(routingCidRef.current ?? ""))
        return;
      const pre = String(payload.preface ?? "").trim();
      appendLine({
        id: `q-${String(payload.sql_turn_id ?? "")}`,
        role: "system",
        text: pre || tRef.current("home.analytics.chatSqlQueued"),
      });
    }),
  );
  return () => {
    unsubs.forEach((u) => u());
  };
}
