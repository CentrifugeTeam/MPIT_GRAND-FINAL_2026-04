import { useQuery } from "@tanstack/react-query";
import { getUsers } from "../api/get-users";

export function useUsers() {
  return useQuery({
    queryKey: ["users"],
    queryFn: getUsers,
  });
}
