export const FIGMA_FAQ_IDS = ["users", "budget", "trips", "performance", "sales"] as const;

export type FigmaFaqId = (typeof FIGMA_FAQ_IDS)[number];

export type FigmaTranslateFn = (
  key: string,
  opts?: Record<string, unknown>,
) => string;

export function readFaqItems(t: FigmaTranslateFn, id: FigmaFaqId): string[] {
  const v = t(`home.figma.faq.${id}.items`, { returnObjects: true });
  return Array.isArray(v) ? (v as string[]) : [];
}
