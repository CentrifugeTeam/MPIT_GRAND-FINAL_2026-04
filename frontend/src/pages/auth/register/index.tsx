import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router';
import {
  Button,
  Card,
  TextField,
  Input,
  FieldError,
  toast,
} from '@heroui/react';
import { useTranslation } from 'react-i18next';
import {
  registerSchema,
  type RegisterFormData,
} from '@/features/auth/model/schema';
import { registerRequest } from '@/features/auth/api/auth';
import { useAuthStore } from '@/shared/lib/auth-store';
import { zodResolver } from '@hookform/resolvers/zod';

export function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const setToken = useAuthStore(s => s.setToken);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({ resolver: zodResolver(registerSchema) });

  const { mutate, isPending } = useMutation({
    mutationFn: ({ email, password }: RegisterFormData) =>
      registerRequest({ email, password }),
    onSuccess: ({ token }) => {
      setToken(token);
      navigate('/home');
    },
    onError: () => {
      toast.danger(t('auth.register.error'));
    },
  });

  return (
    <div className='min-h-screen flex items-center justify-center bg-background'>
      <Card className='w-full max-w-sm'>
        <Card.Header>
          <Card.Title>{t('auth.register.title')}</Card.Title>
        </Card.Header>
        <Card.Content>
          <form
            onSubmit={handleSubmit(data => mutate(data))}
            className='flex flex-col gap-4'
          >
            <TextField isInvalid={!!errors.email}>
              <Input
                {...register('email')}
                type='email'
                placeholder='example@mail.com'
              />
              <FieldError>{errors.email?.message}</FieldError>
            </TextField>

            <TextField isInvalid={!!errors.password}>
              <Input
                {...register('password')}
                type='password'
                placeholder='••••••••'
              />
              <FieldError>{errors.password?.message}</FieldError>
            </TextField>

            <TextField isInvalid={!!errors.confirmPassword}>
              <Input
                {...register('confirmPassword')}
                type='password'
                placeholder='••••••••'
              />
              <FieldError>{errors.confirmPassword?.message}</FieldError>
            </TextField>

            <Button
              type='submit'
              variant='primary'
              isPending={isPending}
              fullWidth
            >
              {t('auth.register.submit')}
            </Button>
          </form>
        </Card.Content>
        <Card.Footer>
          <p className='text-sm text-muted text-center w-full'>
            {t('auth.register.hasAccount')}{' '}
            <Link
              to='/auth/login'
              className='text-accent hover:underline'
            >
              {t('auth.register.login')}
            </Link>
          </p>
        </Card.Footer>
      </Card>
    </div>
  );
}
