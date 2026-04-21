import type { EChartsOption } from "echarts";

import type { ChartPayloadShape } from "@/entities/analytics";

export type VizKind = "auto" | "bar" | "line" | "pie" | "scatter" | "area";

const COLORS = ["#6366f1", "#8b5cf6", "#ec4899", "#14b8a6", "#f59e0b", "#3b82f6"];

function toNum(v: unknown): number {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  const n = parseFloat(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : 0;
}

export function chartToolbox(
  t: (k: string) => string,
): EChartsOption["toolbox"] {
  return {
    right: 12,
    top: 0,
    feature: {
      saveAsImage: {
        type: "png",
        pixelRatio: 2,
        name: "chart",
        title: t("home.analytics.downloadPng"),
        backgroundColor: "rgba(255,255,255,0.96)",
      },
      dataZoom: {},
      restore: {},
    },
  };
}

export function buildChartOption(
  kind: VizKind,
  payload: ChartPayloadShape,
): EChartsOption | null {
  const labels = (payload.labels ?? []).map((x) =>
    x === null || x === undefined ? "—" : String(x),
  );
  const seriesMeta = payload.series ?? [];
  if (!labels.length || !seriesMeta.length) return null;

  const keys = seriesMeta.map((s) => s.key);
  const backendType = payload.type ?? "bar";

  let mode: "bar" | "line" | "pie" | "scatter" | "area";
  if (kind === "auto") {
    mode = backendType === "line" ? "line" : "bar";
  } else if (kind === "area") {
    mode = "area";
  } else {
    mode = kind;
  }

  if (mode === "pie") {
    const values = seriesMeta[0]?.data ?? [];
    const data = labels.map((name, i) => ({
      name,
      value: toNum(values[i]),
    }));
    return {
      backgroundColor: "transparent",
      color: COLORS,
      tooltip: { trigger: "item" },
      legend: { bottom: 0, type: "scroll" },
      series: [
        {
          type: "pie",
          radius: ["38%", "68%"],
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 6 },
          label: { fontSize: 11 },
          data,
        },
      ],
    };
  }

  if (mode === "scatter" && payload.rows?.length && payload.columns?.length) {
    const cols = payload.columns;
    const numericCols = cols.filter((c) =>
      payload.rows!.some((r) => Number.isFinite(toNum(r[c]))),
    );
    if (numericCols.length >= 2) {
      const [cx, cy] = numericCols.slice(0, 2);
      const data = payload.rows
        .map((r) => [toNum(r[cx]), toNum(r[cy])] as [number, number])
        .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
      return {
        backgroundColor: "transparent",
        color: COLORS,
        tooltip: { trigger: "item" },
        grid: { left: 52, right: 24, bottom: 48, top: 48 },
        xAxis: {
          type: "value",
          name: cx,
          splitLine: { lineStyle: { opacity: 0.2 } },
        },
        yAxis: {
          type: "value",
          name: cy,
          splitLine: { lineStyle: { opacity: 0.2 } },
        },
        series: [{ type: "scatter", symbolSize: 12, data }],
      };
    }
    return null;
  }

  const series = keys.map((k) => {
    const s = seriesMeta.find((x) => x.key === k);
    const data = (s?.data ?? []).map((v) => toNum(v));
    if (mode === "line" || mode === "area") {
      return {
        name: k,
        type: "line" as const,
        smooth: true,
        areaStyle: mode === "area" ? { opacity: 0.15 } : undefined,
        emphasis: { focus: "series" as const },
        data,
      };
    }
    return {
      name: k,
      type: "bar" as const,
      emphasis: { focus: "series" as const },
      itemStyle: { borderRadius: [4, 4, 0, 0] },
      data,
    };
  });

  return {
    backgroundColor: "transparent",
    color: COLORS,
    tooltip: { trigger: "axis" },
    legend: { bottom: 0, type: "scroll" },
    grid: { left: 44, right: 16, bottom: 56, top: 32 },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: {
        rotate: labels.some((c) => c.length > 12) ? 30 : 0,
        fontSize: 11,
      },
    },
    yAxis: { type: "value", splitLine: { lineStyle: { opacity: 0.25 } } },
    series,
  };
}
