import type { ChartConfig } from "@/shared/ui";
import type { ChartPayloadShape } from "@/entities/analytics";

export type VizKind = "auto" | "bar" | "line" | "pie" | "scatter" | "area";

const PALETTE = [
  "#6366f1",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f59e0b",
  "#3b82f6",
];

function toNum(v: unknown): number {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  const n = parseFloat(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : 0;
}

/** Плоский объект для Recharts: { label: string, key1: number, key2: number, … } */
export type ChartRow = Record<string, string | number>;

/** Результат трансформации payload → данные для Recharts */
export type ChartData = {
  data: ChartRow[];
  config: ChartConfig;
  keys: string[];
  /** Сумма значений (для центрального лейбла radial chart) */
  total?: number;
  /** Колонки для scatter (x и y) */
  scatterX?: string;
  scatterY?: string;
};

export function buildChartData(
  kind: VizKind,
  payload: ChartPayloadShape,
): ChartData | null {
  const labels = (payload.labels ?? []).map((x) =>
    x === null || x === undefined ? "—" : String(x),
  );
  const seriesMeta = payload.series ?? [];

  if (!labels.length || !seriesMeta.length) return null;

  const keys = seriesMeta.map((s) => s.key);

  const config: ChartConfig = Object.fromEntries(
    keys.map((key, i) => [
      key,
      {
        label: seriesMeta.find((s) => s.key === key)?.label ?? key,
        color: PALETTE[i % PALETTE.length],
      },
    ]),
  );

  if (kind === "scatter" && payload.rows?.length && payload.columns?.length) {
    const cols = payload.columns;
    const numericCols = cols.filter((c) =>
      payload.rows!.some((r) => Number.isFinite(toNum(r[c]))),
    );
    if (numericCols.length < 2) return null;
    const [scatterX, scatterY] = numericCols.slice(0, 2);
    const data: ChartRow[] = payload.rows
      .map((r) => ({
        label: String(r[cols[0]] ?? ""),
        [scatterX]: toNum(r[scatterX]),
        [scatterY]: toNum(r[scatterY]),
      }))
      .filter((r) => Number.isFinite(r[scatterX]) && Number.isFinite(r[scatterY]));

    const scatterConfig: ChartConfig = {
      [scatterX]: { label: scatterX, color: PALETTE[0] },
      [scatterY]: { label: scatterY, color: PALETTE[1] },
    };

    return { data, config: scatterConfig, keys: [scatterX, scatterY], scatterX, scatterY };
  }

  if (kind === "pie") {
    const values = seriesMeta[0]?.data ?? [];
    const nums = labels.map((_, i) => toNum(values[i]));
    const total = nums.reduce((s, v) => s + v, 0);

    // Один объект, где каждый лейбл — это ключ (формат для Radial Stacked)
    const row: ChartRow = {};
    labels.forEach((label, i) => {
      row[label] = nums[i];
    });

    const pieConfig: ChartConfig = Object.fromEntries(
      labels.map((label, i) => [
        label,
        { label, color: PALETTE[i % PALETTE.length] },
      ]),
    );
    return { data: [row], config: pieConfig, keys: labels, total };
  }

  const data: ChartRow[] = labels.map((label, i) => {
    const row: ChartRow = { label };
    for (const s of seriesMeta) {
      row[s.key] = toNum((s.data ?? [])[i]);
    }
    return row;
  });

  return { data, config, keys };
}

/** Определяет эффективный режим отрисовки из VizKind + backend type */
export function resolveMode(
  kind: VizKind,
  backendType?: string,
): "bar" | "line" | "area" | "pie" | "scatter" {
  if (kind === "auto") {
    return backendType === "line" ? "line" : "bar";
  }
  if (kind === "area") return "area";
  if (kind === "pie") return "pie";
  if (kind === "scatter") return "scatter";
  if (kind === "line") return "line";
  return "bar";
}
