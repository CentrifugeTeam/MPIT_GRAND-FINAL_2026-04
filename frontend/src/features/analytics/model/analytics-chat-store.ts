import { create } from "zustand";

import type { NlSqlWsPayload } from "@/entities/analytics";

const MAX_CHAT_ENTRIES = 80;

export type AnalyticsEntryKind = "sql_job" | "nl_chat";

/** First occurrence wins (preserves API order, e.g. newest-first). */
export function dedupeAnalyticsChatEntriesById(
  entries: AnalyticsChatEntry[],
): AnalyticsChatEntry[] {
  const seen = new Set<string>();
  const out: AnalyticsChatEntry[] = [];
  for (const e of entries) {
    if (seen.has(e.id)) continue;
    seen.add(e.id);
    out.push(e);
  }
  return out;
}

export interface AnalyticsChatEntry {
  id: string;
  kind: AnalyticsEntryKind;
  question: string;
  /** Лимит строк для guard; null = не задавать (только sql_job) */
  maxRows: number | null;
  createdAt: number;
  jobId?: string;
  conversationId?: string;
  /** nl_chat: owner — свой чат; viewer — совместный просмотр */
  accessRole?: 'owner' | 'viewer' | null;
  result: NlSqlWsPayload | null;
}

interface AnalyticsChatState {
  entries: AnalyticsChatEntry[];
  activeId: string | null;
  upsertEntry: (entry: AnalyticsChatEntry) => void;
  /** Добавить или заменить по id, без смены activeId (для клика по совместным до selectEntry) */
  mergeEntry: (entry: AnalyticsChatEntry) => void;
  updateEntry: (id: string, patch: Partial<AnalyticsChatEntry>) => void;
  setActive: (id: string | null) => void;
  removeEntry: (id: string) => void;
  setEntriesFromServer: (entries: AnalyticsChatEntry[]) => void;
}

export const useAnalyticsChatStore = create<AnalyticsChatState>()((set) => ({
  entries: [],
  activeId: null,

  upsertEntry: (entry) =>
    set((s) => {
      const rest = s.entries.filter((e) => e.id !== entry.id);
      return {
        entries: [entry, ...rest].slice(0, MAX_CHAT_ENTRIES),
        activeId: entry.id,
      };
    }),

  mergeEntry: (entry) =>
    set((s) => ({
      entries: [entry, ...s.entries.filter((e) => e.id !== entry.id)].slice(
        0,
        MAX_CHAT_ENTRIES,
      ),
    })),

  updateEntry: (id, patch) =>
    set((s) => ({
      entries: s.entries.map((e) => (e.id === id ? { ...e, ...patch } : e)),
    })),

  setActive: (id) => set({ activeId: id }),

  removeEntry: (id) =>
    set((s) => ({
      entries: s.entries.filter((e) => e.id !== id),
      activeId: s.activeId === id ? null : s.activeId,
    })),

  setEntriesFromServer: (incoming) =>
    set((s) => {
      const capped = dedupeAnalyticsChatEntriesById(incoming).slice(
        0,
        MAX_CHAT_ENTRIES,
      );
      const nextActive =
        s.activeId && capped.some((e) => e.id === s.activeId)
          ? s.activeId
          : null;
      return { entries: capped, activeId: nextActive };
    }),
}));
