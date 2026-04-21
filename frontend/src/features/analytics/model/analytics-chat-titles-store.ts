import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AnalyticsChatTitlesState {
  titles: Record<string, string>;
  setTitle: (jobId: string, title: string) => void;
  removeTitle: (jobId: string) => void;
  clearAllTitles: () => void;
}

export const useAnalyticsChatTitlesStore = create<AnalyticsChatTitlesState>()(
  persist(
    (set) => ({
      titles: {},
      setTitle: (jobId, title) =>
        set((s) => {
          const next = title.trim();
          if (!next) {
            const copy = { ...s.titles };
            delete copy[jobId];
            return { titles: copy };
          }
          return { titles: { ...s.titles, [jobId]: next } };
        }),
      removeTitle: (jobId) =>
        set((s) => {
          const copy = { ...s.titles };
          delete copy[jobId];
          return { titles: copy };
        }),
      clearAllTitles: () => set({ titles: {} }),
    }),
    { name: "analytics-chat-titles" },
  ),
);
