import { z } from "zod";

export const glossaryMatchApiSchema = z.object({
  id: z.string(),
  title: z.string().nullable().optional(),
  category: z.string().nullable().optional(),
  definition: z.string(),
});

export const interpretQuestionResponseSchema = z.object({
  interpretation_confidence: z.number(),
  interpretation_warnings: z.array(z.string()),
  interpretation_suggestions: z.array(z.string()),
  glossary_matches: z.array(glossaryMatchApiSchema),
  glossary_context: z.string().nullable(),
});

export const analyticsDataSourceItemSchema = z.object({
  key: z.string(),
  display_name: z.string(),
  is_default: z.boolean(),
});

export const analyticsDataSourcesResponseSchema = z.object({
  items: z.array(analyticsDataSourceItemSchema),
  default_key: z.string().nullable(),
});

export const websocketTokenResponseSchema = z.object({
  ws_url: z.string(),
  token: z.string(),
  expires_in: z.number(),
  message: z.string().optional(),
});

export const createNlChatResponseSchema = z.object({
  conversation_id: z.string(),
  created_at: z.string(),
});

export const nlChatMessageSchema = z.object({
  id: z.string(),
  role: z.string(),
  payload: z.record(z.string(), z.unknown()),
  created_at: z.string(),
  client_message_id: z.string().nullable().optional(),
});

export const nlChatMessagesResponseSchema = z.object({
  items: z.array(nlChatMessageSchema),
});

export const sqlJobHistoryRowSchema = z.object({
  entry_kind: z.literal("sql_job"),
  sort_at: z.string(),
  job_id: z.string(),
  user_id: z.string(),
  question: z.string(),
  max_rows: z.number().nullable(),
  template_key: z.string().nullable(),
  status: z.string(),
  sql: z.string().nullable(),
  explanation: z.string().nullable(),
  error: z.string().nullable(),
  result: z.record(z.string(), z.unknown()).nullable(),
  created_at: z.string(),
  updated_at: z.string().nullable(),
});

export const nlChatHistoryRowSchema = z.object({
  entry_kind: z.literal("nl_chat"),
  sort_at: z.string(),
  conversation_id: z.string(),
  user_id: z.string(),
  question: z.string(),
  chat_title: z.string().nullable(),
  message_count: z.number(),
  created_at: z.string(),
  updated_at: z.string().nullable(),
  access_role: z.enum(["owner", "viewer"]).optional(),
});

export const analyticsHistoryItemSchema = z.discriminatedUnion("entry_kind", [
  sqlJobHistoryRowSchema,
  nlChatHistoryRowSchema,
]);

export const analyticsHistoryResponseSchema = z.object({
  items: z.array(analyticsHistoryItemSchema),
  total: z.number(),
});
