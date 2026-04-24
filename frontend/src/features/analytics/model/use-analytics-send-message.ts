import { useCallback, useState } from "react";

import { createNlAnalyticsChat, fetchInterpretQuestion } from "../api/analytics-api";
import type { InterpretationHint } from "../lib/interpretation-hint";
import { parseAnalyticsMaxRows } from "../lib/parse-analytics-max-rows";
import type { NlChatSendOptions } from "../lib/use-nl-orchestrator-chat";

type SendChatFn = (text: string, options?: NlChatSendOptions) => Promise<void>;

type Params = {
  question: string;
  setQuestion: (v: string) => void;
  nlChatBusy: boolean;
  nlConversationId: string | null;
  setNlConversationId: (id: string | null) => void;
  setPreferDraftNl: (v: boolean) => void;
  setActive: (id: string | null) => void;
  loadHistory: () => Promise<void>;
  dataSourcesLoaded: boolean;
  dataSourcesLength: number;
  selectedSourceKey: string | null;
  selectedSourceLabel: string;
  sendChat: SendChatFn;
  setInterpretationHint: (h: InterpretationHint | null) => void;
  maxRowsStr: string;
  /** Совместный просмотр — без отправки в чужой чат */
  nlReadOnly?: boolean;
};

export function useAnalyticsSendMessage({
  question,
  setQuestion,
  nlChatBusy,
  nlConversationId,
  setNlConversationId,
  setPreferDraftNl,
  setActive,
  loadHistory,
  dataSourcesLoaded,
  dataSourcesLength,
  selectedSourceKey,
  selectedSourceLabel,
  sendChat,
  setInterpretationHint,
  maxRowsStr,
  nlReadOnly = false,
}: Params) {
  const [interpretBusy, setInterpretBusy] = useState(false);

  const sendMessageWithText = useCallback(
    async (rawText: string) => {
      const q = rawText.trim();
      if (nlReadOnly || !q || nlChatBusy || interpretBusy) return;
      if (dataSourcesLoaded && dataSourcesLength > 0 && !selectedSourceKey) return;

      let cid = nlConversationId;
      if (!cid) {
        try {
          const c = await createNlAnalyticsChat();
          cid = c.conversation_id;
        } catch {
          return;
        }
        setPreferDraftNl(false);
        setNlConversationId(cid);
        setActive(cid);
        await loadHistory();
      }

      const maxRows = parseAnalyticsMaxRows(maxRowsStr);
      setInterpretBusy(true);
      let glossaryContext: string | undefined;
      try {
        try {
          const prev = await fetchInterpretQuestion(q, maxRows, selectedSourceKey);
          setInterpretationHint({
            confidence: prev.interpretation_confidence,
            warnings: prev.interpretation_warnings ?? [],
            suggestions: prev.interpretation_suggestions ?? [],
            glossaryTermsCount: prev.glossary_matches?.length ?? 0,
          });
          const gc = prev.glossary_context?.trim();
          if (gc) glossaryContext = gc;
        } catch {
          setInterpretationHint(null);
        }
        await sendChat(q, {
          maxRows,
          glossaryContext,
          analyticsSourceKey: selectedSourceKey,
          analyticsSourceLabel: selectedSourceLabel || null,
          conversationIdOverride: cid,
        });
        await loadHistory();
      } finally {
        setInterpretBusy(false);
      }
    },
    [
      dataSourcesLength,
      dataSourcesLoaded,
      interpretBusy,
      loadHistory,
      maxRowsStr,
      nlChatBusy,
      nlConversationId,
      nlReadOnly,
      selectedSourceKey,
      selectedSourceLabel,
      sendChat,
      setActive,
      setInterpretationHint,
      setNlConversationId,
      setPreferDraftNl,
    ],
  );

  const sendComposerMessage = useCallback(async () => {
    if (nlReadOnly) return;
    const q = question.trim();
    if (!q) return;
    await sendMessageWithText(q);
    setQuestion("");
  }, [nlReadOnly, question, sendMessageWithText, setQuestion]);

  return { sendComposerMessage, sendMessageWithText, interpretBusy };
}
