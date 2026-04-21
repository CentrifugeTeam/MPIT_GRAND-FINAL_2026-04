import type { ChartPayloadShape } from "@/entities/analytics";

/** Bar/line из chart_payload — как в классическом результате аналитики. */
export function nlChatHasSeriesChart(
  cp: ChartPayloadShape | null | undefined,
): boolean {
  if (!cp) return false;
  return (
    (cp.type === "bar" || cp.type === "line") &&
    (cp.labels?.length ?? 0) > 0 &&
    (cp.series?.length ?? 0) > 0
  );
}

export function nlChatHasTablePreview(
  columns: string[] | undefined,
  rows: Record<string, unknown>[] | undefined,
): boolean {
  return (columns?.length ?? 0) > 0 && (rows?.length ?? 0) > 0;
}
