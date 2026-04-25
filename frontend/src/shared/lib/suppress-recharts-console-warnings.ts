/**
 * Recharts ResponsiveContainer иногда логирует предупреждение при измерении 0×0
 * (Virtuoso, flex и т.д.). Пока upstream не стабилен — глушим только этот текст.
 */
const RECHARTS_LAYOUT_SNIPPET =
  "width(-1) and height(-1) of chart should be greater than 0";

function shouldSuppress(args: unknown[]): boolean {
  const first = args[0];
  if (typeof first !== "string") return false;
  return first.includes(RECHARTS_LAYOUT_SNIPPET);
}

const origWarn = console.warn.bind(console);
const origError = console.error.bind(console);

console.warn = (...args: unknown[]) => {
  if (shouldSuppress(args)) return;
  origWarn(...args);
};

console.error = (...args: unknown[]) => {
  if (shouldSuppress(args)) return;
  origError(...args);
};
