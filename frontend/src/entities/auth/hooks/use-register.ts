import { api } from "@/shared/api/axios";
import { useMutation } from "@tanstack/react-query";
import { userCreatedResponseSchema } from "../types";

type Payload = {
  email: string;
  password: string;
  confirm_password: string;
};

export const useRegister = () =>
  useMutation({
    mutationFn: async ({ email, password, confirm_password }: Payload) => {
      const { data } = await api.post("/api/auth/create", {
        email,
        password,
        confirm_password,
      });
      return userCreatedResponseSchema.parse(data);
    },
  });
