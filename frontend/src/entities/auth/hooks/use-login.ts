import { api } from "@/shared/api/axios";
import { useAuthStore } from "@/shared/lib/auth-store";
import { authResponseSchema } from "../types";
import { useMutation } from "@tanstack/react-query";

type Payload = {
  email: string;
  password: string;
};

/** Навигацию после входа делайте в компоненте (useNavigate в mutate), чтобы не ломать порядок хуков при HMR. */
export const useLogin = () => {
  const setSession = useAuthStore((s) => s.setSession);

  return useMutation({
    mutationFn: async ({ email, password }: Payload) => {
      const { data } = await api.post("/api/auth/login", { email, password });
      return authResponseSchema.parse(data);
    },
    onSuccess: (data) => setSession(data),
  });
};
