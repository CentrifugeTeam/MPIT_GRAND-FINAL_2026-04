import { api } from "@/shared/api/axios";
import { useAuthStore } from "@/shared/lib/auth-store";
import { useMutation } from "@tanstack/react-query";
import { authResponseSchema } from "../types";

type Payload = {
  email: string;
  password: string;
  confirm_password: string;
};

export const useRegister = () => {
  const setSession = useAuthStore((s) => s.setSession);

  return useMutation({
    mutationFn: async ({ email, password, confirm_password }: Payload) => {
      const { data } = await api.post("/api/auth/create", {
        email,
        password,
        confirm_password,
      });
      return authResponseSchema.parse(data);
    },
    onSuccess: (data) => setSession(data),
  });
};
