import { useEffect, useRef } from "react";
import { motion } from "motion/react";

import {
  readFaqFallbackTopics,
  type ChatSuggestionTopic,
  type FigmaTranslateFn,
} from "../../config/figma-analytics-faq";

export type FigmaSuggestionBlockProps = {
  t: FigmaTranslateFn;
  activeFaq: string | null;
  setActiveFaq: (v: string | null) => void;
  apiTopics: ChatSuggestionTopic[];
  apiLoaded: boolean;
  onPick: (text: string) => void;
};

export function FigmaSuggestionBlock({
  t,
  activeFaq,
  setActiveFaq,
  apiTopics,
  apiLoaded,
  onPick,
}: FigmaSuggestionBlockProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const fallbackTopics = readFaqFallbackTopics(t);
  const topics = (apiLoaded && apiTopics.length > 0 ? apiTopics : fallbackTopics).slice(0, 5);
  const activeTopic = activeFaq
    ? topics.find((x) => x.topic_key === activeFaq) ?? null
    : null;

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

  if (activeFaq && activeTopic) {
    const items = activeTopic.questions;
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
            className="flex min-h-9 w-full cursor-pointer items-center gap-3 rounded-xl bg-surface/40 px-3 py-1.5 text-left text-sm font-medium text-foreground transition-colors hover:bg-surface"
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
      {topics.map((topic) => (
        <motion.button
          key={topic.topic_key}
          type="button"
          whileTap={{ scale: 0.97 }}
          transition={{ duration: 0.25, ease: "easeInOut" }}
          onClick={() => setActiveFaq(topic.topic_key)}
          className="relative h-10 shrink-0 cursor-pointer rounded-3xl transition-colors duration-200 hover:bg-surface/40"
        >
          <div className="flex h-full items-center justify-center gap-2 rounded-3xl px-4 py-2">
            <span className="whitespace-nowrap text-sm font-medium text-foreground">
              {topic.topic_label}
            </span>
          </div>
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 rounded-3xl border border-border"
          />
        </motion.button>
      ))}
    </div>
  );
}
