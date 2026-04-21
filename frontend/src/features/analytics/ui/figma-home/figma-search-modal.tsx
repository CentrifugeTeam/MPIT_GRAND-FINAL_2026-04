import { useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import { Icon } from "@iconify/react";
import { Input } from "@heroui/react";

import type { AnalyticsChatEntry } from "../../model/analytics-chat-store";

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
        className="relative z-10 w-full max-w-lg overflow-hidden rounded-3xl border border-border bg-background"
        initial={{ opacity: 0, scale: 1.05, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 z-10 flex size-8 cursor-pointer items-center justify-center rounded-3xl bg-surface transition-colors hover:bg-surface-secondary active:scale-[0.97]"
          aria-label={t("common.close")}
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path
              d="M1 1l8 8M9 1L1 9"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              className="text-muted"
            />
          </svg>
        </button>

        <div className="relative flex items-center gap-3 border-b border-border py-4 pl-5 pr-14">
          <Icon icon="mdi:magnify" className="shrink-0 text-muted" width={18} />
          <Input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("home.figma.searchPlaceholder")}
            className="relative min-w-0 flex-1 border-none bg-transparent text-base text-foreground outline-none placeholder:text-muted"
          />
        </div>

        <div className="relative max-h-[400px] overflow-y-auto">
          {!query.trim() && (
            <div className="px-4 pb-1 pt-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs text-muted">{t("home.figma.searchModalActions")}</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  void onStartNewChat();
                  onClose();
                }}
                className="flex w-full cursor-pointer items-center gap-3 rounded-xl bg-surface px-3 py-2.5 transition-colors hover:bg-surface-secondary active:scale-[0.97]"
              >
                <Icon icon="mdi:message-plus-outline" className="text-foreground" width={18} />
                <span className="text-sm font-medium text-foreground">
                  {t("home.figma.searchModalNewPrivate")}
                </span>
              </button>
            </div>
          )}

          <div className="px-4 pb-1 pt-3">
            <span className="mb-2 block text-xs text-muted">
              {t("home.figma.searchModalHistory")}
            </span>
            {filtered.length === 0 && (
              <p className="py-4 text-sm text-muted">{t("home.analytics.sidebarEmpty")}</p>
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
                  className={`mb-1 flex w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors active:scale-[0.97] ${
                    active ? "bg-surface" : "hover:bg-surface/60"
                  }`}
                >
                  <Icon icon="mdi:text-box-outline" className="shrink-0 text-muted" width={16} />
                  <span className="min-w-0 flex-1 truncate text-sm font-medium text-foreground">
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
