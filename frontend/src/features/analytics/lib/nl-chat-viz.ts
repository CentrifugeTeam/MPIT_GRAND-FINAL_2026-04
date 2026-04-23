import type { ChartPayloadShape } from "@/entities/analytics";

/** Любой chart_payload с данными — bar, line, area, pie, scatter и т.д. */
export function nlChatHasSeriesChart(
  cp: ChartPayloadShape | null | undefined,
): boolean {
  if (!cp) return false;
  if (cp.type === "scatter") {
    return (cp.rows?.length ?? 0) > 0 && (cp.columns?.length ?? 0) >= 2;
  }
  return (cp.labels?.length ?? 0) > 0 && (cp.series?.length ?? 0) > 0;
}

export function nlChatHasTablePreview(
  columns: string[] | undefined,
  rows: Record<string, unknown>[] | undefined,
): boolean {
  return (columns?.length ?? 0) > 0 && (rows?.length ?? 0) > 0;
}
