import { useState } from "react";
import { Button } from "@heroui/react";

import { AnalyticsCharts } from "@/features/analytics";
import type { ChartPayloadShape } from "@/entities/analytics";

/* ─── Мок-датасеты ────────────────────────────────────────── */

const MOCKS: Record<string, { label: string; payload: ChartPayloadShape }> = {
  sales: {
    label: "Продажи по месяцам",
    payload: {
      type: "bar",
      labels: ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"],
      series: [
        { key: "Продажи", label: "Продажи", data: [42, 58, 75, 61, 90, 103, 87, 95, 110, 99, 120, 145] },
        { key: "Расходы", label: "Расходы", data: [30, 40, 55, 48, 65, 72, 60, 68, 80, 74, 88, 100] },
      ],
    },
  },
  pie: {
    label: "Доля регионов",
    payload: {
      type: "pie",
      labels: ["Москва", "СПб", "Новосибирск", "Екатеринбург", "Казань", "Другие"],
      series: [{ key: "Доля", label: "Доля", data: [38, 22, 12, 10, 8, 10] }],
    },
  },
  scatter: {
    label: "Цена / рейтинг",
    payload: {
      type: "scatter",
      labels: ["price", "rating"],
      series: [{ key: "price" }, { key: "rating" }],
      columns: ["price", "rating", "name"],
      rows: [
        { price: 150, rating: 4.2, name: "A" },
        { price: 240, rating: 4.7, name: "B" },
        { price: 90,  rating: 3.8, name: "C" },
        { price: 320, rating: 4.9, name: "D" },
        { price: 180, rating: 4.1, name: "E" },
        { price: 260, rating: 4.5, name: "F" },
        { price: 400, rating: 5.0, name: "G" },
        { price: 110, rating: 3.9, name: "H" },
      ],
    },
  },
  multiline: {
    label: "Трафик сайта",
    payload: {
      type: "line",
      labels: ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
      series: [
        { key: "Органика", label: "Органика", data: [1200, 1500, 1350, 1700, 1600, 900, 700] },
        { key: "Реклама",  label: "Реклама",  data: [400,  600,  550,  700,  680,  300, 200] },
        { key: "Соцсети",  label: "Соцсети",  data: [300,  350,  400,  380,  450,  600, 550] },
      ],
    },
  },
};

/* ─── Мок-диалог ──────────────────────────────────────────── */

type MockLine =
  | { role: "user"; text: string }
  | { role: "assistant"; text: string; chartPayload?: ChartPayloadShape };

function buildMockLines(payload: ChartPayloadShape, label: string): MockLine[] {
  return [
    { role: "user", text: `Покажи данные: ${label}` },
    {
      role: "assistant",
      text: "Вот результат по вашему запросу. Вы можете переключать тип визуализации кнопками под заголовком.",
      chartPayload: payload,
    },
    { role: "user", text: "Спасибо! Можешь подвести итог?" },
    {
      role: "assistant",
      text: "Конечно. Данные показывают устойчивую динамику на протяжении всего периода. Если хотите детальный анализ — уточните запрос.",
    },
  ];
}

/* ─── Пузырь чата (grok-стиль) ───────────────────────────── */

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <div className="ml-auto w-fit max-w-[min(85%,520px)] min-w-0 rounded-[22px] bg-[#27272a] px-4 py-3 text-left font-sans text-[15px] font-normal leading-relaxed text-[#fafafa] wrap-break-word">
        {text}
      </div>
    </div>
  );
}

function AssistantBubble({ text, chartPayload }: { text: string; chartPayload?: ChartPayloadShape }) {
  return (
    <div className="w-full max-w-[min(720px,100%)] font-sans text-[15px] font-normal leading-relaxed text-[#e4e4e7]">
      <p className="whitespace-pre-wrap">{text}</p>
      {chartPayload && (
        <div className="mt-4 rounded-2xl border border-[#28282c] bg-[#09090b] p-4 shadow-none">
          <p className="mb-3 text-xs font-medium uppercase tracking-wide text-[#71717a]">
            График
          </p>
          <AnalyticsCharts payload={chartPayload} />
        </div>
      )}
    </div>
  );
}

/* ─── Страница ────────────────────────────────────────────── */

export function DevChartsPage() {
  const [active, setActive] = useState<keyof typeof MOCKS>("sales");

  const { label, payload } = MOCKS[active];
  const mockLines = buildMockLines(payload, label);

  return (
    <div className="min-h-screen bg-[#060607] py-10 px-4">
      <div className="mx-auto w-full" style={{ maxWidth: 760 }}>

        {/* Заголовок */}
        <div className="mb-6">
          <h1 className="text-[#fafafa] text-xl font-semibold">Chart Preview</h1>
          <p className="mt-1 text-sm text-[#71717a]">
            Мок-чат — так график выглядит прямо в диалоге
          </p>
        </div>

        {/* Переключатель датасетов */}
        <div className="mb-8 flex flex-wrap gap-2">
          {Object.entries(MOCKS).map(([key, { label: l }]) => (
            <Button
              key={key}
              size="sm"
              variant={active === key ? "primary" : "ghost"}
              className="rounded-full text-[#fafafa]"
              onPress={() => setActive(key as keyof typeof MOCKS)}
            >
              {l}
            </Button>
          ))}
        </div>

        {/* Мок-чат */}
        <div className="flex flex-col gap-8">
          {mockLines.map((line, i) =>
            line.role === "user" ? (
              <UserBubble key={i} text={line.text} />
            ) : (
              <AssistantBubble
                key={i}
                text={line.text}
                chartPayload={line.chartPayload}
              />
            ),
          )}
        </div>

        <p className="mt-12 text-center text-xs text-[#52525b]">
          /dev/charts — только для разработки
        </p>
      </div>
    </div>
  );
}
