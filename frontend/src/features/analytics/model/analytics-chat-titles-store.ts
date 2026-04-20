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
            const { [jobId]: _, ...rest } = s.titles;
            return { titles: rest };
          }
          return { titles: { ...s.titles, [jobId]: next } };
        }),
      removeTitle: (jobId) =>
        set((s) => {
          const { [jobId]: _, ...rest } = s.titles;
          return { titles: rest };
        }),
      clearAllTitles: () => set({ titles: {} }),
    }),
    { name: "analytics-chat-titles" },
  ),
);
