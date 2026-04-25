import * as React from "react";
import * as RechartsPrimitive from "recharts";

function usePositiveChartLayout(ref: React.RefObject<HTMLElement | null>) {
  const [ready, setReady] = React.useState(false);

  React.useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;

    const update = () => {
      const { width, height } = el.getBoundingClientRect();
      setReady(width > 0 && height > 0);
    };

    update();

    const ro = new ResizeObserver(() => {
      update();
    });
    ro.observe(el);

    const id = requestAnimationFrame(update);
    return () => {
      cancelAnimationFrame(id);
      ro.disconnect();
    };
  }, [ref]);

  return ready;
}

const THEMES = { light: "", dark: ".dark" } as const;

export type ChartConfig = {
  [k in string]: {
    label?: React.ReactNode;
    icon?: React.ComponentType;
    color?: string;
    theme?: Record<keyof typeof THEMES, string>;
  };
};

type ChartContextProps = {
  config: ChartConfig;
};

const ChartContext = React.createContext<ChartContextProps | null>(null);

export function useChart() {
  const context = React.useContext(ChartContext);
  if (!context) {
    throw new Error("useChart must be used within a <ChartContainer />");
  }
  return context;
}

export function ChartContainer({
  id,
  className,
  children,
  config,
  ...props
}: React.ComponentProps<"div"> & {
  config: ChartConfig;
  children: React.ComponentProps<
    typeof RechartsPrimitive.ResponsiveContainer
  >["children"];
}) {
  const uniqueId = React.useId();
  const chartId = `chart-${id || uniqueId.replace(/:/g, "")}`;
  const containerRef = React.useRef<HTMLDivElement>(null);
  const layoutReady = usePositiveChartLayout(containerRef);

  const mergedClassName = ["relative w-full min-h-0", className]
    .filter(Boolean)
    .join(" ");

  return (
    <ChartContext.Provider value={{ config }}>
      <div
        ref={containerRef}
        data-slot="chart"
        data-chart={chartId}
        className={mergedClassName}
        {...props}
      >
        <ChartStyle id={chartId} config={config} />
        {layoutReady ? (
          <RechartsPrimitive.ResponsiveContainer
            width="100%"
            height="100%"
            minWidth={0}
          >
            {children}
          </RechartsPrimitive.ResponsiveContainer>
        ) : null}
      </div>
    </ChartContext.Provider>
  );
}

export function ChartStyle({ id, config }: { id: string; config: ChartConfig }) {
  const colorConfig = Object.entries(config).filter(
    ([, cfg]) => cfg.theme || cfg.color,
  );

  if (!colorConfig.length) return null;

  return (
    <style
      dangerouslySetInnerHTML={{
        __html: Object.entries(THEMES)
          .map(([theme, prefix]) => {
            const vars = colorConfig
              .map(([key, itemConfig]) => {
                const color =
                  itemConfig.theme?.[theme as keyof typeof itemConfig.theme] ||
                  itemConfig.color;
                return color ? `  --color-${key}: ${color};` : null;
              })
              .filter(Boolean)
              .join("\n");
            return `${prefix} [data-chart=${id}] {\n${vars}\n}`;
          })
          .join("\n"),
      }}
    />
  );
}

export const ChartTooltip = RechartsPrimitive.Tooltip;

type TooltipPayloadItem = {
  dataKey?: string | number;
  name?: string | number;
  value?: number | string;
  color?: string;
  payload?: Record<string, unknown>;
  fill?: string;
};

type ChartTooltipContentProps = {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string | number;
  className?: string;
  indicator?: "line" | "dot" | "dashed";
  hideLabel?: boolean;
  hideIndicator?: boolean;
  labelFormatter?: (label: unknown, payload: TooltipPayloadItem[]) => React.ReactNode;
  labelClassName?: string;
  formatter?: (
    value: unknown,
    name: unknown,
    item: TooltipPayloadItem,
    index: number,
    payload: unknown,
  ) => React.ReactNode;
  color?: string;
  nameKey?: string;
  labelKey?: string;
};

export function ChartTooltipContent({
  active,
  payload,
  className,
  indicator = "dot",
  hideLabel = false,
  hideIndicator = false,
  label,
  labelFormatter,
  labelClassName,
  formatter,
  color,
  nameKey,
  labelKey,
}: ChartTooltipContentProps) {
  const { config } = useChart();

  const tooltipLabel = React.useMemo(() => {
    if (hideLabel || !payload?.length) return null;

    const [item] = payload;
    const key = `${labelKey || item?.dataKey || item?.name || "value"}`;
    const itemConfig = getPayloadConfigFromPayload(config, item, key);
    const value =
      !labelKey && typeof label === "string"
        ? (config[label]?.label ?? label)
        : itemConfig?.label;

    if (labelFormatter) {
      return (
        <div className={`font-medium ${labelClassName ?? ""}`}>
          {labelFormatter(value, payload)}
        </div>
      );
    }

    if (!value) return null;

    return (
      <div className={`font-medium ${labelClassName ?? ""}`}>{value}</div>
    );
  }, [label, labelFormatter, payload, hideLabel, labelClassName, config, labelKey]);

  if (!active || !payload?.length) return null;

  const nestLabel = payload.length === 1 && indicator !== "dot";

  return (
    <div
      className={`border-border/50 bg-background grid min-w-32 items-start gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs shadow-xl ${className ?? ""}`}
    >
      {!nestLabel ? tooltipLabel : null}
      <div className="grid gap-1.5">
        {payload.map((item, index) => {
          const key = `${nameKey || item.name || item.dataKey || "value"}`;
          const itemConfig = getPayloadConfigFromPayload(config, item, key);
          const indicatorColor = color || item.payload?.fill || item.color;

          return (
            <div
              key={`${item.dataKey}-${index}`}
              className={`flex w-full flex-wrap items-stretch gap-2 ${indicator === "dot" ? "items-center" : ""}`}
            >
              {formatter && item.value !== undefined && item.name ? (
                formatter(item.value, item.name, item, index, item.payload)
              ) : (
                <>
                  {itemConfig?.icon ? (
                    <itemConfig.icon />
                  ) : (
                    !hideIndicator && (
                      <div
                        className={`shrink-0 rounded-[2px] border-(--color-border) bg-(--color-bg) ${
                          indicator === "dot"
                            ? "size-2.5 rounded-full border-[.5px]"
                            : indicator === "line"
                              ? "w-1"
                              : "w-0 border-[1.5px] border-dashed bg-transparent"
                        } ${nestLabel ? "translate-y-[2px]" : ""}`}
                        style={
                          {
                            "--color-bg": indicatorColor,
                            "--color-border": indicatorColor,
                          } as React.CSSProperties
                        }
                      />
                    )
                  )}
                  <div
                    className={`flex flex-1 justify-between leading-none ${nestLabel ? "items-end" : "items-center"}`}
                  >
                    <div className="grid gap-1.5">
                      {nestLabel ? tooltipLabel : null}
                      <span className="text-muted-foreground">
                        {itemConfig?.label || item.name}
                      </span>
                    </div>
                    {item.value !== undefined && (
                      <span className="text-foreground font-mono font-medium tabular-nums">
                        {typeof item.value === "number"
                          ? item.value.toLocaleString()
                          : item.value}
                      </span>
                    )}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export const ChartLegend = RechartsPrimitive.Legend;

type LegendPayloadItem = {
  value?: string | number;
  dataKey?: string | number;
  color?: string;
};

type ChartLegendContentProps = {
  className?: string;
  hideIcon?: boolean;
  payload?: LegendPayloadItem[];
  verticalAlign?: "top" | "bottom" | "middle";
  nameKey?: string;
};

export function ChartLegendContent({
  className,
  hideIcon = false,
  payload,
  verticalAlign = "bottom",
  nameKey,
}: ChartLegendContentProps) {
  const { config } = useChart();

  if (!payload?.length) return null;

  return (
    <div
      className={`flex items-center justify-center gap-4 ${
        verticalAlign === "top" ? "pb-3" : "pt-3"
      } ${className ?? ""}`}
    >
      {payload.map((item, i) => {
        const key = `${nameKey || item.dataKey || "value"}`;
        const itemConfig = getPayloadConfigFromPayload(config, item, key);

        return (
          <div key={`${item.value}-${i}`} className="flex items-center gap-1.5">
            {itemConfig?.icon && !hideIcon ? (
              <itemConfig.icon />
            ) : (
              <div
                className="size-2 shrink-0 rounded-[2px]"
                style={{ backgroundColor: item.color }}
              />
            )}
            <span className="text-xs">{itemConfig?.label ?? item.value}</span>
          </div>
        );
      })}
    </div>
  );
}

function getPayloadConfigFromPayload(
  config: ChartConfig,
  payload: unknown,
  key: string,
): ChartConfig[string] | undefined {
  if (typeof payload !== "object" || payload === null) return undefined;

  const payloadRecord = payload as Record<string, unknown>;
  const payloadPayload =
    "payload" in payloadRecord &&
    typeof payloadRecord.payload === "object" &&
    payloadRecord.payload !== null
      ? (payloadRecord.payload as Record<string, unknown>)
      : undefined;

  let configLabelKey = key;

  if (key in config) {
    configLabelKey = key;
  } else if (
    payloadPayload &&
    key in payloadPayload &&
    typeof payloadPayload[key] === "string" &&
    (payloadPayload[key] as string) in config
  ) {
    configLabelKey = payloadPayload[key] as string;
  }

  return configLabelKey in config ? config[configLabelKey] : config[key];
}
