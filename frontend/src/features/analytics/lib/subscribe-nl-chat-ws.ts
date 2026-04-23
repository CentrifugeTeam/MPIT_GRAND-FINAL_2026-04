import type { MutableRefObject } from "react";

import { resolveNlAssistantVisibleText } from "./nl-chat-assistant-body";
import {
  pickChartPayload,
  pickRows,
  pickStringArray,
} from "./nl-chat-ws-payload";
import type { NlChatLine } from "./nl-chat-line";
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
    wsClient.on("chat_thinking", (payload: Record<string, unknown>) => {
      if (String(payload.conversation_id ?? "") !== String(routingCidRef.current ?? "")) return;
      const rs = String(payload.reasoning ?? "").trim();
      appendLine({
        id: String(payload.message_id ?? crypto.randomUUID()),
        role: "assistant",
        text: "",
        reasoning: rs,
        answerPending: true,
      });
    }),
  );
  unsubs.push(
    wsClient.on("chat_assistant", (payload: Record<string, unknown>) => {
      if (String(payload.conversation_id ?? "") !== String(routingCidRef.current ?? ""))
        return;
      const text = String(payload.text ?? "");
      const rep = payload.report ? String(payload.report) : "";
      const reasoningRaw = String(payload.reasoning ?? "").trim();
      const sql = payload.sql != null ? String(payload.sql) : null;
      const status = String(payload.status ?? "");
      const err = payload.error != null ? String(payload.error).trim() : "";
      const cols = pickStringArray(payload.columns);
      const rowObjs = pickRows(payload.rows);
      const rc = payload.row_count;
      const rcNum = typeof rc === "number" ? rc : undefined;

      const body = resolveNlAssistantVisibleText(tRef.current, {
        text,
        report: rep,
        status,
        error: err,
        columns: cols,
        rows: rowObjs,
        sql,
        rowCount: rcNum,
      });
      appendLine({
        id: String(payload.message_id ?? crypto.randomUUID()),
        role: "assistant",
        text: body,
        reasoning: reasoningRaw || undefined,
        answerPending: false,
        sql,
        chartPayload: pickChartPayload(payload.chart_payload),
        columns: cols,
        rows: rowObjs,
        rowCount: rcNum,
      });
      setNlChatBusy(false);
    }),
  );
  unsubs.push(
    wsClient.on("chat_sql_queued", (payload: Record<string, unknown>) => {
      if (String(payload.conversation_id ?? "") !== String(routingCidRef.current ?? ""))
        return;
      const pre = String(payload.preface ?? "").trim();
      const qReasoning = String(payload.reasoning ?? "").trim();
      appendLine({
        id: `q-${String(payload.sql_turn_id ?? "")}`,
        role: "system",
        text: pre || tRef.current("home.analytics.chatSqlQueued"),
        reasoning: qReasoning || undefined,
      });
    }),
  );
  return () => {
    unsubs.forEach((u) => u());
  };
}
