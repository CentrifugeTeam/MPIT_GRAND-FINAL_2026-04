export const FIGMA_FAQ_IDS = ["users", "budget", "trips", "performance", "sales"] as const;

export type FigmaFaqId = (typeof FIGMA_FAQ_IDS)[number];

export type ChatSuggestionTopic = {
  topic_key: string;
  topic_label: string;
  questions: string[];
};

export type FigmaTranslateFn = (
  key: string,
  opts?: Record<string, unknown>,
) => string;

export function readFaqItems(t: FigmaTranslateFn, id: FigmaFaqId): string[] {
  const v = t(`home.figma.faq.${id}.items`, { returnObjects: true });
  return Array.isArray(v) ? (v as string[]) : [];
}

export function readFaqFallbackTopics(t: FigmaTranslateFn): ChatSuggestionTopic[] {
  return FIGMA_FAQ_IDS.map((id) => ({
    topic_key: id,
    topic_label: t(`home.figma.faq.${id}.label`),
    questions: readFaqItems(t, id),
  })).filter((x) => x.questions.length >= 4);
}
