type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type AssistantBodyInput = {
  text: string;
  report: string;
  status: string;
  error: string;
  columns: string[] | undefined;
  rows: Record<string, unknown>[] | undefined;
  sql: string | null;
  rowCount: number | undefined;
};

/** Единая подпись для WS и для истории из API, если модель вернула пустой текст. */
export function resolveNlAssistantVisibleText(
  t: TFn,
  input: AssistantBodyInput,
): string {
  const rep = input.report.trim();
  const txt = input.text.trim();
  const body = rep ? `${txt}\n\n${rep}`.trim() : txt;
  if (body) return body;

  const hasTable =
    (input.columns?.length ?? 0) > 0 && (input.rows?.length ?? 0) > 0;
  const hasSql = Boolean(input.sql?.trim());
  const rcNum = input.rowCount;

  if (input.status === "error" && input.error) {
    return input.error;
  }
  if (hasTable) {
    return t("home.analytics.chatAssistantDataFallback");
  }
  if (hasSql) {
    return rcNum === 0
      ? t("home.analytics.chatAssistantNoRows")
      : t("home.analytics.chatAssistantSqlOnly");
  }
  if (input.status === "done" && rcNum === 0) {
    return t("home.analytics.chatAssistantNoRows");
  }
  return t("home.analytics.chatEmptyAssistant");
}
