import { api } from "@/shared/api/axios";
import { usersResponseSchema } from "../model/schema";

export async function getUsers() {
  const { data } = await api.get("/users");
  return usersResponseSchema.parse(data);
}
