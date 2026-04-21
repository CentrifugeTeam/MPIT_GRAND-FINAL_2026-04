import type { ChartPayloadShape } from "@/entities/analytics";

export type NlChatLine = {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
  sql?: string | null;
  chartPayload?: ChartPayloadShape;
  columns?: string[];
  rows?: Record<string, unknown>[];
  rowCount?: number;
};
