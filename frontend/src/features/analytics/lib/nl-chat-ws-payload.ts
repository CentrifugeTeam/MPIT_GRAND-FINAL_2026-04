import type { ChartPayloadShape } from "@/entities/analytics";

export function pickChartPayload(raw: unknown): ChartPayloadShape | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const o = raw as Record<string, unknown>;
  if (Object.keys(o).length === 0) return undefined;
  return raw as ChartPayloadShape;
}

export function pickStringArray(raw: unknown): string[] | undefined {
  if (!Array.isArray(raw)) return undefined;
  return raw.map((x) => String(x));
}

export function pickRows(raw: unknown): Record<string, unknown>[] | undefined {
  if (!Array.isArray(raw)) return undefined;
  const out: Record<string, unknown>[] = [];
  for (const r of raw) {
    if (r && typeof r === "object" && !Array.isArray(r)) {
      out.push(r as Record<string, unknown>);
    }
  }
  return out.length ? out : undefined;
}
