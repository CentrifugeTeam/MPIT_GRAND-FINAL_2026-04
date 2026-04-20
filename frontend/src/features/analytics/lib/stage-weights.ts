/** Веса этапов для прогресс-бара запроса аналитики. */
export const ANALYTICS_STAGE_WEIGHT = {
  idle: 0,
  ask: 18,
  token: 28,
  ws_connect: 42,
  watch_sent: 58,
  ack: 72,
  result: 88,
  done: 100,
} as const;

export type AnalyticsStageKey = keyof typeof ANALYTICS_STAGE_WEIGHT;
