import { useCallback, useEffect, useRef, useState } from "react";

import { patchNlChatTitle } from "@/features/analytics/api/analytics-api";
import type { AnalyticsChatEntry } from "@/features/analytics/model/analytics-chat-store";
import { useAnalyticsChatStore } from "@/features/analytics/model/analytics-chat-store";
import { useAnalyticsChatTitlesStore } from "@/features/analytics/model/analytics-chat-titles-store";

export function useAnalyticsRenameRow() {
  const [editingRowId, setEditingRowId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [renameFieldFocused, setRenameFieldFocused] = useState(false);
  const renameInputRef = useRef<HTMLInputElement>(null);
  const titles = useAnalyticsChatTitlesStore((s) => s.titles);
  const setChatTitle = useAnalyticsChatTitlesStore((s) => s.setTitle);

  useEffect(() => {
    if (editingRowId) {
      requestAnimationFrame(() => renameInputRef.current?.focus());
    }
  }, [editingRowId]);

  const startEditingRow = useCallback(
    (e: AnalyticsChatEntry) => {
      setEditingRowId(e.id);
      setRenameDraft(titles[e.id] ?? e.question);
    },
    [titles],
  );

  const cancelRename = useCallback(() => {
    setRenameFieldFocused(false);
    setEditingRowId(null);
    setRenameDraft("");
  }, []);

  const commitRename = useCallback(async () => {
    if (!editingRowId) return;
    const e = useAnalyticsChatStore.getState().entries.find((x) => x.id === editingRowId);
    if (e?.kind === "nl_chat") {
      const cid = e.conversationId ?? e.id;
      try {
        await patchNlChatTitle(cid, renameDraft.trim());
      } catch {
        /* ignore */
      }
    }
    setChatTitle(editingRowId, renameDraft);
    setRenameFieldFocused(false);
    setEditingRowId(null);
    setRenameDraft("");
  }, [renameDraft, editingRowId, setChatTitle]);

  return {
    editingRowId,
    renameDraft,
    renameFieldFocused,
    renameInputRef,
    setRenameDraft,
    setRenameFieldFocused,
    startEditingRow,
    cancelRename,
    commitRename,
  };
}
