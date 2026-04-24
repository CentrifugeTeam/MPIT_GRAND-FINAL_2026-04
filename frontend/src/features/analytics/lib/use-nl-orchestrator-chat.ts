import { useCallback, useEffect, useRef, useState } from "react";

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

export function useNlOrchestratorChat(
  t: TFn,
  conversationId: string | null,
  readOnly: boolean = false,
) {
  const [lines, setLines] = useState<NlChatLine[]>([]);
  const [nlChatBusy, setNlChatBusy] = useState(false);
  const linesRef = useRef<NlChatLine[]>([]);
  const joinedRef = useRef(false);
  const transcriptLoadGen = useRef(0);
  const routingCidRef = useRef<string | null>(conversationId);
  const tRef = useRef(t);
  /** Оптимистичное user-сообщение, если GET /messages ещё без записи в БД (гонка с sync). */
  const pendingUserLineRef = useRef<{
    conversationId: string;
    clientMessageId: string;
    line: NlChatLine;
  } | null>(null);

  useEffect(() => {
    joinedRef.current = false;
  }, [conversationId]);

  useEffect(() => {
    if (readOnly) setNlChatBusy(false);
  }, [readOnly]);

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

  const removeLinesByIds = useCallback((ids: string[]) => {
    if (!ids.length) return;
    const del = new Set(ids);
    setLines((prev) => {
      const next = prev.filter((l) => !del.has(l.id));
      linesRef.current = next;
      return next;
    });
  }, []);

  const appendLine = useCallback((line: NlChatLine) => {
    setLines((prev) => {
      const idx = prev.findIndex((p) => p.id === line.id);
      if (line.role === "assistant" && idx >= 0) {
        const prevLine = prev[idx]!;
        if (prevLine.role === "assistant") {
          const merged: NlChatLine = {
            ...prevLine,
            ...line,
            chartPayload: line.chartPayload ?? prevLine.chartPayload,
            columns: line.columns ?? prevLine.columns,
            rows: line.rows ?? prevLine.rows,
          };
          const next = prev.slice();
          next[idx] = merged;
          return next;
        }
        // Старый воркер: тот же message_id у user и assistant — не затирать вопрос.
        const altId = `${line.id}-a`;
        const j = prev.findIndex((p) => p.id === altId);
        if (j >= 0 && prev[j]!.role === "assistant") {
          const prevA = prev[j]!;
          const merged: NlChatLine = {
            ...prevA,
            ...line,
            id: altId,
            chartPayload: line.chartPayload ?? prevA.chartPayload,
            columns: line.columns ?? prevA.columns,
            rows: line.rows ?? prevA.rows,
          };
          const next = prev.slice();
          next[j] = merged;
          return next;
        }
        return prev.concat({ ...line, id: altId });
      }
      if (idx >= 0) return prev;
      return prev.concat(line);
    });
  }, []);

  useEffect(() => {
    return subscribeNlChatWs(
      routingCidRef,
      tRef,
      appendLine,
      setNlChatBusy,
      removeLinesByIds,
    );
  }, [appendLine, removeLinesByIds]);

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
    return () => {
      pendingUserLineRef.current = null;
    };
  }, [conversationId]);

  useEffect(() => {
    if (!conversationId) return;
    const gen = ++transcriptLoadGen.current;
    let cancelled = false;
    void fetchNlChatMessages(conversationId)
      .then((data) => {
        if (cancelled || gen !== transcriptLoadGen.current) return;
        const pend = pendingUserLineRef.current;
        let present = false;
        if (pend && pend.conversationId === conversationId) {
          const mid = pend.clientMessageId;
          present = data.items.some(
            (r) =>
              String(r.client_message_id || "").trim() === mid ||
              String(r.id) === mid,
          );
          if (present) pendingUserLineRef.current = null;
        }
        const mapped = data.items.map((row) => apiNlMessageToLine(row, tRef.current));
        if (pend && pend.conversationId === conversationId && !present) {
          setLines([...mapped, pend.line]);
          pendingUserLineRef.current = null;
        } else {
          setLines(mapped);
        }
      })
      .catch(() => {
        if (!cancelled && gen === transcriptLoadGen.current) setLines([]);
      });
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  useEffect(() => {
    if (conversationId) return;
    pendingUserLineRef.current = null;
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

  /** Удалить пару user+assistant (или только assistant) для повтора из композера; linesRef синхронно. */
  const requestDeleteChatMessages = useCallback(
    async (messageIds: string[]) => {
      const cid = conversationId;
      const ids = [...new Set(messageIds.map((s) => s.trim()).filter(Boolean))];
      if (!cid || !ids.length) return;
      try {
        await ensureWsConnected();
        joinChatRoom(cid);
        wsClient.sendPlain({
          type: "delete_chat_messages",
          conversation_id: cid,
          message_ids: ids,
        });
      } catch {
        /* локальная лента уже подрезана */
      }
    },
    [conversationId, ensureWsConnected, joinChatRoom],
  );

  /** Первый id в локальной ленте, с которого нужно срезать при retry (как в trimForRetry). */
  const getRetryTailAnchorId = useCallback((assistantLineId: string): string | null => {
    const prev = linesRef.current;
    const idx = prev.findIndex((row) => row.id === assistantLineId);
    if (idx < 0) return null;
    let start = idx;
    if (idx > 0 && prev[idx - 1]!.role === "user") {
      start = idx - 1;
    }
    return prev[start]?.id ?? null;
  }, []);

  /** Удалить на сервере якорь и все сообщения после него в сессии (синхрон с trimForRetry). */
  const requestDeleteChatTailFrom = useCallback(
    async (fromMessageId: string) => {
      const cid = conversationId;
      const anchor = fromMessageId.trim();
      if (!cid || !anchor) return;
      try {
        await ensureWsConnected();
        joinChatRoom(cid);
        wsClient.sendPlain({
          type: "delete_chat_messages",
          conversation_id: cid,
          from_message_id: anchor,
        });
      } catch {
        /* локальная лента уже подрезана */
      }
    },
    [conversationId, ensureWsConnected, joinChatRoom],
  );

  const trimForRetry = useCallback((assistantLineId: string) => {
    setLines((prev) => {
      const idx = prev.findIndex((row) => row.id === assistantLineId);
      if (idx < 0) return prev;
      let start = idx;
      if (idx > 0 && prev[idx - 1]!.role === "user") {
        start = idx - 1;
      }
      const next = prev.slice(0, start);
      linesRef.current = next;
      return next;
    });
  }, []);

  const sendChat = useCallback(
    async (text: string, options?: NlChatSendOptions) => {
      const trimmed = text.trim();
      const cid =
        (options?.conversationIdOverride?.trim() || null) ?? conversationId;
      if (!trimmed || nlChatBusy || !cid) return;
      routingCidRef.current = cid;

      const mid = crypto.randomUUID();
      const userLine: NlChatLine = {
        id: mid,
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
      pendingUserLineRef.current = {
        conversationId: cid,
        clientMessageId: mid,
        line: userLine,
      };

      const maxRows = options?.maxRows;
      const glossaryContext = options?.glossaryContext?.trim();

      try {
        await ensureWsConnected();
        joinChatRoom(cid);
        const payload: Record<string, unknown> = {
          type: "chat_message",
          conversation_id: cid,
          message_id: mid,
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
        pendingUserLineRef.current = null;
        setNlChatBusy(false);
        appendLine({
          id: crypto.randomUUID(),
          role: "system",
          text: tRef.current("home.analytics.chatSendError"),
        });
      }
    },
    [
      appendLine,
      conversationId,
      ensureWsConnected,
      joinChatRoom,
      nlChatBusy,
      readOnly,
    ],
  );

  return {
    lines,
    nlChatBusy,
    sendChat,
    trimForRetry,
    requestDeleteChatMessages,
    getRetryTailAnchorId,
    requestDeleteChatTailFrom,
  };
}
