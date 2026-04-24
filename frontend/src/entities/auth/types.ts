import { z } from "zod";
import { authResponseSchema } from "@/shared/lib/auth-response-schema";

export { authResponseSchema };

export type AuthResponse = z.infer<typeof authResponseSchema>;

export const userCreatedResponseSchema = z.object({
  message: z.string(),
  uuid: z.string().uuid(),
});

export type UserCreatedResponse = z.infer<typeof userCreatedResponseSchema>;
