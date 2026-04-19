import { api } from '@/shared/api/axios';
import { useMutation } from '@tanstack/react-query';

type Payload = {
  email: string;
  password: string;
  confirm_password: string;
};

export const useRegister = () => {
  return useMutation({
    mutationFn: ({ email, password, confirm_password }: Payload) => {
      const res = api.post('/api/auth/create', {
        email,
        password,
        confirm_password,
      });

      return res;
    },
  });
};
