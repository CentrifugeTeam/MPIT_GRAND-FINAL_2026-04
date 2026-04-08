import { z } from "zod";

export const userSchema = z.object({
  id: z.string(),
  createdAt: z.string(),
  name: z.string(),
  avatar: z.string(),
});

export type User = z.infer<typeof userSchema>;

export const usersResponseSchema = z.array(userSchema);
