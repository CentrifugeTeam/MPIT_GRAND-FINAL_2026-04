import { useCallback, useEffect, useRef, useState } from "react";

/** Сброс «зависшего» ожидания ответа, если chat_assistant не пришёл (сеть, рассинхрон pending). */
const NL_CHAT_BUSY_WATCHDOG_MS = 120_000;

import { ANALYTICS_MAX_ROWS_CAP } from "../config/constants";
import { fetchNlChatMessages } from "../api/analytics-api";
import type { NlChatLine } from "./nl-chat-line";
import { subscribeNlChatWs } from "./subscribe-nl-chat-ws";
import { apiNlMessageToLine } from "./nl-chat-transcript";
import { wsClient } from "@/shared/api/ws-client";
import { useWsStore } from "@/shared/lib/ws-store";

export type { NlChatLine } from "./nl-chat-line";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type NlChatSendOptions = {
  maxRows?: number | null;
  glossaryContext?: string | null;
  /** Ключ из GET /api/analytics/data-sources; схема и SELECT идут в эту БД */
  analyticsSourceKey?: string | null;
  /** Подпись для LLM (активная БД), не список всех источников */
  analyticsSourceLabel?: string | null;
  /** Первое сообщение до обновления conversationId в родителе */
  conversationIdOverride?: string | null;
};

export function useNlOrchestratorChat(t: TFn, conversationId: string | null) {
  const [lines, setLines] = useState<NlChatLine[]>([]);
  const [nlChatBusy, setNlChatBusy] = useState(false);
  const linesRef = useRef<NlChatLine[]>([]);
  const joinedRef = useRef(false);
  const transcriptLoadGen = useRef(0);
  const routingCidRef = useRef<string | null>(conversationId);
  const tRef = useRef(t);

  useEffect(() => {
    joinedRef.current = false;
  }, [conversationId]);

  useEffect(() => {
    setNlChatBusy(false);
  }, [conversationId]);

  useEffect(() => {
    if (!nlChatBusy) return;
    const id = window.setTimeout(() => {
      setNlChatBusy(false);
    }, NL_CHAT_BUSY_WATCHDOG_MS);
    return () => window.clearTimeout(id);
  }, [nlChatBusy]);

  useEffect(() => {
    routingCidRef.current = conversationId;
    tRef.current = t;
  }, [conversationId, t]);

  const ensureWsConnected = useWsStore((s) => s.ensureConnected);
  const wsStatus = useWsStore((s) => s.status);

  useEffect(() => {
    linesRef.current = lines;
  }, [lines]);

  const appendLine = useCallback((line: NlChatLine) => {
    setLines((prev) => {
      const idx = prev.findIndex((p) => p.id === line.id);
      if (line.role === "assistant" && idx >= 0) {
        const prevLine = prev[idx]!;
        const merged: NlChatLine = {
          ...prevLine,
          ...line,
          chartPayload: line.chartPayload ?? prevLine.chartPayload,
          columns: line.columns ?? prevLine.columns,
          rows: line.rows ?? prevLine.rows,
        };
        return [...prev.slice(0, idx), merged, ...prev.slice(idx + 1)];
      }
      if (idx >= 0) return prev;
      return [...prev, line];
    });
  }, []);

  useEffect(() => {
    return subscribeNlChatWs(routingCidRef, tRef, appendLine, setNlChatBusy);
  }, [appendLine]);

  const joinChatRoom = useCallback((explicitConversationId?: string | null) => {
    const cid = explicitConversationId ?? conversationId;
    if (!cid) return;
    wsClient.sendPlain({
      type: "join_chat",
      conversation_id: cid,
    });
    joinedRef.current = true;
  }, [conversationId]);

  useEffect(() => {
    if (!conversationId) return;
    const gen = ++transcriptLoadGen.current;
    let cancelled = false;
    void fetchNlChatMessages(conversationId)
      .then((data) => {
        if (cancelled || gen !== transcriptLoadGen.current) return;
        setLines(data.items.map((row) => apiNlMessageToLine(row, t)));
      })
      .catch(() => {
        if (!cancelled && gen === transcriptLoadGen.current) setLines([]);
      });
    return () => {
      cancelled = true;
    };
  }, [conversationId, t]);

  useEffect(() => {
    if (conversationId) return;
    setLines([]);
  }, [conversationId]);

  useEffect(() => {
    if (!conversationId) return;
    let cancelled = false;
    void ensureWsConnected()
      .then(() => {
        if (!cancelled) joinChatRoom();
      })
      .catch(() => {
        if (!cancelled) {
          appendLine({
            id: "err-ws",
            role: "system",
            text: tRef.current("home.analytics.chatWsError"),
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [appendLine, conversationId, ensureWsConnected, joinChatRoom]);

  useEffect(() => {
    if (!conversationId) return;
    if (wsStatus === "connected") joinChatRoom();
  }, [conversationId, joinChatRoom, wsStatus]);

  useEffect(() => {
    return () => {
      if (joinedRef.current && conversationId) {
        wsClient.sendPlain({
          type: "leave_chat",
          conversation_id: conversationId,
        });
        joinedRef.current = false;
      }
    };
  }, [conversationId]);

  const sendChat = useCallback(
    async (text: string, options?: NlChatSendOptions) => {
      const trimmed = text.trim();
      const cid =
        (options?.conversationIdOverride?.trim() || null) ?? conversationId;
      if (!trimmed || nlChatBusy || !cid) return;
      routingCidRef.current = cid;

      const userLine: NlChatLine = {
        id: crypto.randomUUID(),
        role: "user",
        text: trimmed,
      };
      const history = [...linesRef.current, userLine]
        .filter((l) => l.role === "user" || l.role === "assistant")
        .slice(-20)
        .map((l) => ({
          role: l.role === "user" ? "user" : "assistant",
          content: l.text,
        }));

      setNlChatBusy(true);
      appendLine(userLine);

      const maxRows = options?.maxRows;
      const glossaryContext = options?.glossaryContext?.trim();

      try {
        await ensureWsConnected();
        joinChatRoom(cid);
        const payload: Record<string, unknown> = {
          type: "chat_message",
          conversation_id: cid,
          content: trimmed,
          history,
        };
        if (
          maxRows != null &&
          Number.isFinite(maxRows) &&
          maxRows > 0
        ) {
          payload.max_rows = Math.min(ANALYTICS_MAX_ROWS_CAP, Math.floor(maxRows));
        }
        if (glossaryContext) {
          payload.glossary_context = glossaryContext;
        }
        const src = options?.analyticsSourceKey?.trim();
        if (src) {
          payload.analytics_source_key = src;
        }
        const sl = options?.analyticsSourceLabel?.trim();
        if (sl) {
          payload.analytics_source_label = sl;
        }
        wsClient.sendPlain(payload);
      } catch {
        setNlChatBusy(false);
        appendLine({
          id: crypto.randomUUID(),
          role: "system",
          text: tRef.current("home.analytics.chatSendError"),
        });
      }
    },
    [appendLine, conversationId, ensureWsConnected, joinChatRoom, nlChatBusy],
  );

  return { lines, nlChatBusy, sendChat };
}
