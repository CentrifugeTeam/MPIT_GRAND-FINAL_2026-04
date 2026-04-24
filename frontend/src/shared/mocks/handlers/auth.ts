import { http, HttpResponse } from "msw";

/** Как у реального BFF → совпадает с authResponseSchema (иначе zod падает и форма показывает «неверный пароль»). */
const mockLoginBody = {
  access_token: "mock-access-token",
  refresh_token: "mock-refresh-token",
  expires_in: 3600,
  user_uuid: "99066868-74e6-4941-b2c9-e518748d0882",
};

export const authHandlers = [
  http.post("/api/auth/login", async () =>
    HttpResponse.json(mockLoginBody),
  ),

  http.post("/api/auth/refresh", async () =>
    HttpResponse.json(mockLoginBody),
  ),

  http.post("/api/auth/create", async () => {
    return HttpResponse.json({
      message: "User created successfully",
      uuid: "550e8400-e29b-41d4-a716-446655440000",
    });
  }),
];
