import { useRegister } from '@/entities/auth/hooks/use-register';
import { InputWithHelper } from '@/shared/ui/molecules/input-with-helper';
import { Button, Card, Input } from '@heroui/react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Controller, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router';
import z from 'zod';

const mandatoryField = 'Поле обязательно';

const registerSchema = z
  .object({
    email: z.email().min(1),
    password: z.string(mandatoryField).min(1),
    confirmPassword: z.string(mandatoryField).min(1),
  })
  .refine(data => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

type RegisterSchemaData = z.infer<typeof registerSchema>;

export type Props = {};

export const RegisterPage = ({}: Props) => {
  const { mutate } = useRegister();
  const navigate = useNavigate();

  const formMethod = useForm<RegisterSchemaData>({
    resolver: zodResolver(registerSchema),
    mode: 'all',
  });

  const handleClick = (data: RegisterSchemaData) => {
    mutate(
      {
        email: data.email,
        password: data.password,
        confirm_password: data.confirmPassword,
      },
      {
        onSuccess: () => {
          navigate('/auth/login');
        },
      },
    );
  };

  return (
    <Card className='flex items-center justify-center'>
      <Card className='bg-white p-5 rounded-2xl flex items-start justify-between'>
        <Controller
          name='email'
          control={formMethod.control}
          render={({ field, fieldState }) => (
            <InputWithHelper
              {...field}
              placeholder='email'
              helperText={fieldState.error?.message || undefined}
            />
          )}
        />
        <Controller
          name='password'
          control={formMethod.control}
          render={({ field, fieldState }) => (
            <InputWithHelper
              {...field}
              placeholder='Пароль'
              helperText={fieldState.error?.message || undefined}
            />
          )}
        />
        <Controller
          name='confirmPassword'
          control={formMethod.control}
          render={({ field, fieldState }) => (
            <InputWithHelper
              {...field}
              placeholder='Подтвердите пароль'
              helperText={fieldState.error?.message || undefined}
            />
          )}
        />
      </Card>
      <Button onClick={formMethod.handleSubmit(handleClick)}>test</Button>
    </Card>
  );
};
