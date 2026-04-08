import { http, HttpResponse } from "msw";
import { env } from "@/shared/config/env";

export const authHandlers = [
  http.post(`${env.apiUrl}/auth/login`, async ({ request }) => {
    const { email } = (await request.json()) as { email: string; password: string };
    return HttpResponse.json({ token: "mock-token", email });
  }),

  http.post(`${env.apiUrl}/auth/register`, async ({ request }) => {
    const { email } = (await request.json()) as { email: string; password: string };
    return HttpResponse.json({ token: "mock-token", email });
  }),
];
