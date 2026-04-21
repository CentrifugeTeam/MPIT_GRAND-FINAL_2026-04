import { useEffect, useRef } from "react";
import { motion } from "motion/react";

import {
  FIGMA_FAQ_IDS,
  readFaqItems,
  type FigmaFaqId,
  type FigmaTranslateFn,
} from "@/features/analytics/config/figma-analytics-faq";

export type FigmaSuggestionBlockProps = {
  t: FigmaTranslateFn;
  activeFaq: FigmaFaqId | null;
  setActiveFaq: (v: FigmaFaqId | null) => void;
  onPick: (text: string) => void;
};

export function FigmaSuggestionBlock({
  t,
  activeFaq,
  setActiveFaq,
  onPick,
}: FigmaSuggestionBlockProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!activeFaq) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setActiveFaq(null);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [activeFaq, setActiveFaq]);

  if (activeFaq) {
    const items = readFaqItems(t, activeFaq);
    return (
      <div ref={containerRef} className="flex w-full flex-col items-start gap-1">
        {items.map((item, i) => (
          <motion.button
            key={item}
            type="button"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.15, delay: i * 0.03 }}
            onMouseDown={(e) => e.stopPropagation()}
            onClick={() => {
              onPick(item);
              setActiveFaq(null);
            }}
            className="flex min-h-9 w-full cursor-pointer items-center gap-3 rounded-xl bg-[#27272a]/40 px-3 py-1.5 text-left font-sans text-[14px] font-medium text-[#fcfcfc] transition-colors hover:bg-[#27272a]"
          >
            {item}
          </motion.button>
        ))}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="flex w-full flex-wrap items-center justify-center gap-2"
    >
      {FIGMA_FAQ_IDS.map((id) => (
        <motion.button
          key={id}
          type="button"
          whileTap={{ scale: 0.97 }}
          transition={{ duration: 0.25, ease: "easeInOut" }}
          onClick={() => setActiveFaq(id)}
          className="relative h-10 shrink-0 cursor-pointer rounded-[24px] transition-colors duration-200 hover:bg-[#27272a]/40"
        >
          <div className="flex h-full items-center justify-center gap-2 rounded-[24px] px-4 py-2">
            <span className="whitespace-nowrap font-sans text-[14px] font-medium text-[#fcfcfc]">
              {t(`home.figma.faq.${id}.label`)}
            </span>
          </div>
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 rounded-[24px] border border-solid border-[#28282c]"
          />
        </motion.button>
      ))}
    </div>
  );
}
