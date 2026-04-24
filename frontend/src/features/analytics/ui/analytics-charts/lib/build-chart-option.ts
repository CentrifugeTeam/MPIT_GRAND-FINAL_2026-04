import type { ChartConfig } from "@/shared/ui";
import type { ChartPayloadShape } from "@/entities/analytics";

export type VizKind = "auto" | "bar" | "line" | "pie" | "area";

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

function formatLabel(label: string): string {
  const m = label.match(/^(\d{4})-(\d{2})-(\d{2})(?:T|$)/);
  if (m) return `${m[3]}.${m[2]}.${m[1]}`;
  return label;
}

const MAX_PIE_SLICES = 12;

/** Плоский объект для Recharts: { label: string, key1: number, key2: number, … } */
export type ChartRow = Record<string, string | number>;

/** Результат трансформации payload → данные для Recharts */
export type ChartData = {
  data: ChartRow[];
  config: ChartConfig;
  keys: string[];
  /** Сумма значений (для центрального лейбла radial chart) */
  total?: number;
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

  if (kind === "pie") {
    const values = seriesMeta[0]?.data ?? [];
    const rawNums = labels.map((_, i) => toNum(values[i]));
    const total = rawNums.reduce((s, v) => s + v, 0);

    // Сортируем по убыванию, берём топ-(MAX_PIE_SLICES-1), остаток → "Другие"
    const indexed = rawNums
      .map((v, i) => ({ v, label: formatLabel(labels[i] ?? "") }))
      .sort((a, b) => b.v - a.v);

    let slices: { label: string; value: number }[];
    if (indexed.length > MAX_PIE_SLICES) {
      const top = indexed.slice(0, MAX_PIE_SLICES - 1);
      const restSum = indexed.slice(MAX_PIE_SLICES - 1).reduce((s, x) => s + x.v, 0);
      slices = [...top.map((x) => ({ label: x.label, value: x.v })), { label: "Другие", value: restSum }];
    } else {
      slices = indexed.map((x) => ({ label: x.label, value: x.v }));
    }

    const pieData: ChartRow[] = slices.map((s) => ({ name: s.label, value: s.value }));

    const pieConfig: ChartConfig = Object.fromEntries(
      slices.map((s, i) => [s.label, { label: s.label, color: PALETTE[i % PALETTE.length] }]),
    );
    return { data: pieData, config: pieConfig, keys: ["value"], total };
  }

  const data: ChartRow[] = labels.map((label, i) => {
    const row: ChartRow = { label: formatLabel(label) };
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
): "bar" | "line" | "area" | "pie" {
  if (kind === "auto") {
    return backendType === "line" ? "line" : "bar";
  }
  if (kind === "area") return "area";
  if (kind === "pie") return "pie";
  if (kind === "line") return "line";
  return "bar";
}
