import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@heroui/react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  RadialBarChart,
  RadialBar,
  PolarRadiusAxis,
  Label,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";

import type { ChartPayloadShape } from "@/entities/analytics";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "@/shared/ui";

import {
  buildChartData,
  resolveMode,
  type VizKind,
} from "./lib/build-chart-option";

export type { VizKind };

const PALETTE = [
  "#6366f1",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f59e0b",
  "#3b82f6",
];

const KINDS: VizKind[] = ["auto", "bar", "line", "area", "pie", "scatter"];

export function AnalyticsCharts({ payload }: { payload: ChartPayloadShape }) {
  const { t } = useTranslation();
  const [kind, setKind] = useState<VizKind>("auto");

  const hasSeries =
    (payload.series?.length ?? 0) > 0 && (payload.labels?.length ?? 0) > 0;

  const mode = resolveMode(kind, payload.type);
  const chartData = useMemo(() => {
    if (!hasSeries) return null;
    try {
      return buildChartData(mode === "area" ? "area" : mode === "pie" ? "pie" : mode === "scatter" ? "scatter" : kind, payload);
    } catch {
      return null;
    }
  }, [kind, mode, payload, hasSeries]);

  if (!hasSeries || !chartData) return null;

  const { data, config, keys, total, scatterX, scatterY } = chartData;

  const rotateLabels = data.some(
    (r) => typeof r.label === "string" && r.label.length > 12,
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {KINDS.map((k) => (
          <Button
            key={k}
            size="sm"
            variant={kind === k ? "primary" : "ghost"}
            className="rounded-full capitalize"
            onPress={() => setKind(k)}
          >
            {t(`home.analytics.viz.${k}`)}
          </Button>
        ))}
      </div>

      <ChartContainer config={config} className="h-[360px] w-full min-w-0">
        {mode === "bar" && (
          <BarChart data={data} margin={{ top: 8, right: 16, bottom: rotateLabels ? 40 : 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11 }}
              angle={rotateLabels ? -30 : 0}
              textAnchor={rotateLabels ? "end" : "middle"}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 11 }} width={44} />
            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            {keys.map((key, i) => (
              <Bar
                key={key}
                dataKey={key}
                fill={PALETTE[i % PALETTE.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        )}

        {mode === "line" && (
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: rotateLabels ? 40 : 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11 }}
              angle={rotateLabels ? -30 : 0}
              textAnchor={rotateLabels ? "end" : "middle"}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 11 }} width={44} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            {keys.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={PALETTE[i % PALETTE.length]}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        )}

        {mode === "area" && (
          <AreaChart data={data} margin={{ top: 8, right: 16, bottom: rotateLabels ? 40 : 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11 }}
              angle={rotateLabels ? -30 : 0}
              textAnchor={rotateLabels ? "end" : "middle"}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 11 }} width={44} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            {keys.map((key, i) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={PALETTE[i % PALETTE.length]}
                fill={PALETTE[i % PALETTE.length]}
                fillOpacity={0.15}
                strokeWidth={2}
              />
            ))}
          </AreaChart>
        )}

        {mode === "pie" && (
          <RadialBarChart
            data={data}
            endAngle={180}
            innerRadius={80}
            outerRadius={130}
          >
            <ChartTooltip cursor={false} content={<ChartTooltipContent hideLabel />} />
            <PolarRadiusAxis tick={false} tickLine={false} axisLine={false}>
              <Label
                content={({ viewBox }) => {
                  if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                    return (
                      <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle">
                        <tspan
                          x={viewBox.cx}
                          y={(viewBox.cy ?? 0) - 16}
                          className="fill-foreground text-2xl font-bold"
                          fontSize={24}
                          fontWeight="bold"
                        >
                          {(total ?? 0).toLocaleString()}
                        </tspan>
                        <tspan
                          x={viewBox.cx}
                          y={(viewBox.cy ?? 0) + 8}
                          className="fill-muted"
                          fontSize={12}
                          fill="var(--color-muted, #888)"
                        >
                          всего
                        </tspan>
                      </text>
                    );
                  }
                }}
              />
            </PolarRadiusAxis>
            {keys.map((key, i) => (
              <RadialBar
                key={key}
                dataKey={key}
                stackId="a"
                cornerRadius={4}
                fill={PALETTE[i % PALETTE.length]}
                className="stroke-transparent stroke-2"
              />
            ))}
          </RadialBarChart>
        )}

        {mode === "scatter" && scatterX && scatterY && (
          <ScatterChart margin={{ top: 8, right: 24, bottom: 24, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
            <XAxis
              dataKey={scatterX}
              name={scatterX}
              type="number"
              tick={{ fontSize: 11 }}
              label={{ value: scatterX, position: "insideBottom", offset: -4, fontSize: 11 }}
            />
            <YAxis
              dataKey={scatterY}
              name={scatterY}
              type="number"
              tick={{ fontSize: 11 }}
              width={44}
              label={{ value: scatterY, angle: -90, position: "insideLeft", fontSize: 11 }}
            />
            <ChartTooltip cursor={{ strokeDasharray: "3 3" }} content={<ChartTooltipContent />} />
            <Scatter data={data} fill={PALETTE[0]} />
          </ScatterChart>
        )}
      </ChartContainer>

      <p className="text-muted text-xs">{t("home.analytics.chartHint")}</p>
    </div>
  );
}
