import { ANALYTICS_MAX_ROWS_CAP } from "../config/constants";

export function parseAnalyticsMaxRows(maxRowsStr: string): number | null {
  const s = maxRowsStr.trim();
  if (!s) return null;
  const n = parseInt(s, 10);
  if (!Number.isFinite(n) || n < 1) return null;
  return Math.min(ANALYTICS_MAX_ROWS_CAP, n);
}
