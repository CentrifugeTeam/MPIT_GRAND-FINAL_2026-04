import { api } from "./axios";

export type UserSearchItem = {
  uuid: string;
  email: string;
  role: string;
};

type UserListResponse = {
  users: UserSearchItem[];
};

export type SearchUsersByEmailParams = {
  query: string;
  limit?: number;
  signal?: AbortSignal;
};

export async function searchUsersByEmail(
  params: SearchUsersByEmailParams,
): Promise<UserSearchItem[]> {
  const q = params.query.trim();
  if (q.length < 1) {
    return [];
  }
  const { data } = await api.get<UserListResponse>("/api/auth/users/search", {
    params: { query: q, limit: params.limit ?? 20 },
    signal: params.signal,
  });
  return Array.isArray(data?.users) ? data.users : [];
}
