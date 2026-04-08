import { api } from "@/shared/api/axios";
import { z } from "zod";

const authResponseSchema = z.object({
  token: z.string(),
});

export type AuthCredentials = {
  email: string;
  password: string;
};

export async function loginRequest(credentials: AuthCredentials) {
  const { data } = await api.post("/auth/login", credentials);
  return authResponseSchema.parse(data);
}

export async function registerRequest(credentials: AuthCredentials) {
  const { data } = await api.post("/auth/register", credentials);
  return authResponseSchema.parse(data);
}
