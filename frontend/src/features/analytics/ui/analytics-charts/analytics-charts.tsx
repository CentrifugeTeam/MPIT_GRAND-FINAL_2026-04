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
  PieChart,
  Pie,
  Cell,
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

const KINDS: VizKind[] = ["auto", "bar", "line", "area", "pie"];

export function AnalyticsCharts({ payload }: { payload: ChartPayloadShape }) {
  const { t } = useTranslation();
  const [kind, setKind] = useState<VizKind>("auto");

  const hasSeries =
    (payload.series?.length ?? 0) > 0 && (payload.labels?.length ?? 0) > 0;

  const mode = resolveMode(kind, payload.type);
  const chartData = useMemo(() => {
    if (!hasSeries) return null;
    try {
      return buildChartData(mode === "area" ? "area" : mode === "pie" ? "pie" : kind, payload);
    } catch {
      return null;
    }
  }, [kind, mode, payload, hasSeries]);

  if (!hasSeries || !chartData) return null;

  const { data, config, keys, total } = chartData;

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

      <ChartContainer config={config} className={`${mode === 'pie' ? 'h-[260px]' : 'h-[360px]'} w-full min-w-0 [&_svg]:outline-none`}>
        {mode === "bar" && (
          <BarChart data={data} margin={{ top: 8, right: 16, bottom: rotateLabels ? 40 : 8, left: 0 }} style={{ outline: "none" }}>
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
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: rotateLabels ? 40 : 8, left: 0 }} style={{ outline: "none" }}>
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
          <AreaChart data={data} margin={{ top: 8, right: 16, bottom: rotateLabels ? 40 : 8, left: 0 }} style={{ outline: "none" }}>
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
          <PieChart style={{ outline: "none" }}>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={data.length > 1 ? 2 : 0}
              strokeWidth={0}
              style={{ outline: "none" }}
            >
              {data.map((_, i) => (
                <Cell
                  key={i}
                  fill={PALETTE[i % PALETTE.length]}
                  stroke="none"
                  style={{ outline: "none" }}
                />
              ))}
            </Pie>
            <ChartTooltip
              cursor={false}
              isAnimationActive={false}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const item = payload[0];
                if (!item) return null;
                const pct = total ? Math.round((Number(item.value) / total) * 100) : 0;
                return (
                  <div className="rounded-lg border border-border bg-background px-3 py-2 text-xs shadow-md">
                    <p className="font-medium">{String(item.name)}</p>
                    <p className="text-muted-foreground">
                      {Number(item.value).toLocaleString()} ({pct}%)
                    </p>
                  </div>
                );
              }}
            />
          </PieChart>
        )}


      </ChartContainer>

      {mode === "pie" && (
        <ul className="flex flex-wrap justify-center gap-x-4 gap-y-1.5 pt-1">
          {data.map((entry, i) => (
            <li key={i} className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span
                className="inline-block size-2.5 shrink-0 rounded-[2px]"
                style={{ background: PALETTE[i % PALETTE.length] }}
              />
              {String(entry.name)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
