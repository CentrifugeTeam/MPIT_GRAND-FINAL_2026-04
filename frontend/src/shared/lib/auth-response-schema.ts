import { z } from "zod";
import type { AuthSessionPayload } from "@/shared/types/auth-session";

export const authResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  expires_in: z.number(),
  user_uuid: z.string(),
}) satisfies z.ZodType<AuthSessionPayload>;
