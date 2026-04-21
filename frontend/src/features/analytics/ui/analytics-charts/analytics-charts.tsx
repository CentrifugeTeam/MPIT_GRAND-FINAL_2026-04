import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import ReactEcharts from "echarts-for-react";
import * as echarts from "echarts";
import type { EChartsOption } from "echarts";
import { Button } from "@heroui/react";
import { Icon } from "@iconify/react";

import type { ChartPayloadShape } from "@/entities/analytics";

import {
  buildChartOption,
  chartToolbox,
  type VizKind,
} from "./lib/build-chart-option";

export type { VizKind };

export function AnalyticsCharts({ payload }: { payload: ChartPayloadShape }) {
  const { t } = useTranslation();
  const chartRef = useRef<InstanceType<typeof ReactEcharts>>(null);
  const [kind, setKind] = useState<VizKind>("auto");

  const hasSeries =
    (payload.series?.length ?? 0) > 0 && (payload.labels?.length ?? 0) > 0;

  const option = useMemo(() => {
    if (!hasSeries) return null;
    try {
      const core = buildChartOption(kind, payload);
      if (!core) return null;
      return {
        ...core,
        toolbox: chartToolbox(t),
      } as EChartsOption;
    } catch {
      return null;
    }
  }, [kind, payload, hasSeries, t]);

  const downloadExtra = () => {
    const inst = chartRef.current?.getEchartsInstance?.();
    if (!inst) return;
    const url = inst.getDataURL({
      type: "png",
      pixelRatio: 2,
      backgroundColor: "#ffffff",
    });
    const a = document.createElement("a");
    a.href = url;
    a.download = `analytics-chart-${kind}.png`;
    a.click();
  };

  if (!hasSeries || !option) {
    return null;
  }

  const kinds: VizKind[] = ["auto", "bar", "line", "area", "pie", "scatter"];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {kinds.map((k) => (
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
        <Button
          size="sm"
          variant="outline"
          className="ml-auto rounded-full"
          onPress={downloadExtra}
        >
          <Icon icon="mdi:download" className="mr-1" width={16} />
          {t("home.analytics.downloadPng")}
        </Button>
      </div>

      <div className="h-[360px] w-full min-w-0">
        <ReactEcharts
          ref={chartRef}
          echarts={echarts}
          option={option}
          style={{ height: "100%", width: "100%" }}
          notMerge
          lazyUpdate
        />
      </div>
      <p className="text-muted text-xs">{t("home.analytics.chartHint")}</p>
    </div>
  );
}
