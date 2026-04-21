import { useState } from "react";
import { motion } from "motion/react";
import { Icon } from "@iconify/react";

import type { AnalyticsDataSourceItem } from "@/features/analytics/api/analytics-api";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type FigmaSourceModalProps = {
  t: TFn;
  open: boolean;
  sources: AnalyticsDataSourceItem[];
  selectedKey: string | null;
  onClose: () => void;
  onApply: (key: string) => void;
};

type BodyProps = Omit<FigmaSourceModalProps, "open">;

function FigmaSourceModalBody({
  t,
  sources,
  selectedKey,
  onClose,
  onApply,
}: BodyProps) {
  const [localKey, setLocalKey] = useState(() => selectedKey ?? sources[0]?.key ?? "");

  return (
    <motion.div
      className="fixed inset-0 z-[105] flex items-start justify-center pt-[18vh]"
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
        onClick={onClose}
      />
      <motion.div
        className="relative z-10 w-full max-w-[440px] overflow-hidden rounded-[24px] border border-solid border-[#28282c] bg-[#18181b]"
        initial={{ opacity: 0, scale: 1.03, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
      >
        <div className="flex items-center justify-between border-b border-[#28282c] px-5 py-4">
          <div className="flex items-center gap-2">
            <Icon icon="mdi:database-outline" className="text-[#a1a1aa]" width={20} />
            <span className="font-sans text-[16px] font-medium text-[#fcfcfc]">
              {t("home.figma.sourceModalTitle")}
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex size-8 cursor-pointer items-center justify-center rounded-[24px] bg-[#27272a] transition-colors hover:bg-[#323236] active:scale-[0.97]"
            aria-label={t("home.figma.sourceModalClose")}
          >
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden>
              <path
                d="M1 1l8 8M9 1L1 9"
                stroke="#a1a1aa"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>
        <p className="px-5 pt-3 font-sans text-[13px] leading-snug text-[#a1a1aa]">
          {t("home.figma.sourceModalHint")}
        </p>
        <div className="max-h-[min(52vh,360px)] overflow-y-auto px-3 py-3">
          {sources.map((s) => {
            const checked = localKey === s.key;
            return (
              <button
                key={s.key}
                type="button"
                onClick={() => setLocalKey(s.key)}
                className={`mb-1 flex w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-3 text-left transition-colors active:scale-[0.99] ${
                  checked ? "bg-[#27272a]" : "hover:bg-[#27272a]/60"
                }`}
              >
                <span
                  className={`flex size-5 shrink-0 items-center justify-center rounded-full border-2 ${
                    checked ? "border-[#fcfcfc] bg-[#fcfcfc]" : "border-[#52525b]"
                  }`}
                >
                  {checked && (
                    <span className="size-2 rounded-full bg-[#18181b]" aria-hidden />
                  )}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-sans text-[14px] font-medium text-[#fcfcfc]">
                    {s.display_name}
                  </span>
                  <span className="mt-0.5 block font-mono text-[11px] text-[#71717a]">{s.key}</span>
                </span>
                {s.is_default && (
                  <span className="shrink-0 rounded-md bg-[#3f3f46] px-2 py-0.5 font-sans text-[11px] text-[#e4e4e7]">
                    {t("home.figma.dataSourceDefault")}
                  </span>
                )}
              </button>
            );
          })}
        </div>
        <div className="flex justify-end gap-2 border-t border-[#28282c] px-5 py-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-[24px] bg-[#27272a] px-4 py-2 font-sans text-[14px] font-medium text-[#fcfcfc] transition-colors hover:bg-[#323236] active:scale-[0.97]"
          >
            {t("home.figma.sourceModalCancel")}
          </button>
          <button
            type="button"
            onClick={() => {
              if (localKey) onApply(localKey);
              onClose();
            }}
            disabled={!localKey}
            className="rounded-[24px] bg-[#fcfcfc] px-4 py-2 font-sans text-[14px] font-medium text-[#18181b] transition-colors hover:bg-[#e4e4e7] disabled:cursor-not-allowed disabled:opacity-40 active:scale-[0.97]"
          >
            {t("home.figma.sourceModalApply")}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

export function FigmaSourceModal({ open, sources, selectedKey, ...rest }: FigmaSourceModalProps) {
  if (!open) return null;
  const listKey = sources.map((s) => s.key).join("|");
  const mountKey = `${selectedKey ?? ""}|${listKey}`;
  return (
    <FigmaSourceModalBody key={mountKey} sources={sources} selectedKey={selectedKey} {...rest} />
  );
}
