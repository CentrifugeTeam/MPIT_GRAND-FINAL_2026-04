import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "motion/react";
import { Icon } from "@iconify/react";

import type { AnalyticsChatEntry } from "@/features/analytics/model/analytics-chat-store";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type FigmaSearchModalProps = {
  t: TFn;
  entries: AnalyticsChatEntry[];
  titles: Record<string, string>;
  activeId: string | null;
  onClose: () => void;
  onSelectEntry: (id: string) => void;
  onStartNewChat: () => void;
};

export function FigmaSearchModal({
  t,
  entries,
  titles,
  activeId,
  onClose,
  onSelectEntry,
  onStartNewChat,
}: FigmaSearchModalProps) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter((e) => {
      const label = (titles[e.id] ?? e.question).toLowerCase();
      return label.includes(q);
    });
  }, [entries, query, titles]);

  return (
    <motion.div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      <motion.div
        className="absolute inset-0"
        style={{ background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)" }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.25 }}
        onClick={onClose}
      />

      <motion.div
        className="relative z-10 w-full max-w-[512px] overflow-hidden rounded-[24px] border border-solid border-[#28282c] bg-[#18181b]"
        initial={{ opacity: 0, scale: 1.05, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
      >
          <button
            type="button"
            onClick={onClose}
            className="absolute right-[16px] top-[16px] z-10 flex size-[32px] cursor-pointer items-center justify-center rounded-[24px] bg-[#27272a] transition-colors duration-150 hover:bg-[#323236] active:scale-[0.97]"
            aria-label="Close"
          >
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
              <path
                d="M1 1l8 8M9 1L1 9"
                stroke="#a1a1aa"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </button>

          <div className="relative flex items-center gap-3 border-b border-[#28282c] py-4 pl-5 pr-14">
            <Icon icon="mdi:magnify" className="shrink-0 text-[#a1a1aa]" width={18} />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("home.figma.searchPlaceholder")}
              className="relative min-w-0 flex-1 bg-transparent font-sans text-base text-[#fcfcfc] outline-none placeholder:text-[#71717a]"
            />
          </div>

          <div className="relative max-h-[400px] overflow-y-auto">
            {!query.trim() && (
              <div className="px-4 pb-1 pt-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-sans text-[12px] text-[#a1a1aa]">
                    {t("home.figma.searchModalActions")}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    void onStartNewChat();
                    onClose();
                  }}
                  className="flex w-full cursor-pointer items-center gap-3 rounded-xl bg-[#27272a] px-3 py-2.5 transition-colors duration-150 hover:bg-[#323236] active:scale-[0.97]"
                >
                  <Icon icon="mdi:message-plus-outline" className="text-[#fcfcfc]" width={18} />
                  <span className="font-medium font-sans text-[14px] text-[#fcfcfc]">
                    {t("home.figma.searchModalNewPrivate")}
                  </span>
                </button>
              </div>
            )}

            <div className="px-4 pb-1 pt-3">
              <span className="mb-2 block font-sans text-[12px] text-[#a1a1aa]">
                {t("home.figma.searchModalHistory")}
              </span>
              {filtered.length === 0 && (
                <p className="py-4 font-sans text-sm text-[#71717a]">{t("home.analytics.sidebarEmpty")}</p>
              )}
              {filtered.map((e) => {
                const label = titles[e.id] ?? e.question;
                const active = activeId === e.id;
                return (
                  <button
                    key={e.id}
                    type="button"
                    onClick={() => {
                      onSelectEntry(e.id);
                      onClose();
                    }}
                    className={`mb-1 flex w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors duration-150 active:scale-[0.97] ${
                      active ? "bg-[#27272a]" : "hover:bg-[#27272a]/60"
                    }`}
                  >
                    <Icon icon="mdi:text-box-outline" className="shrink-0 text-[#a1a1aa]" width={16} />
                    <span className="min-w-0 flex-1 truncate font-medium font-sans text-[14px] text-[#fcfcfc]">
                      {label}
                    </span>
                  </button>
                );
              })}
            </div>
            <div className="h-2" />
          </div>
      </motion.div>
    </motion.div>
  );
}
