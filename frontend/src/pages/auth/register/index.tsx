import { useRegister } from '@/entities/auth/hooks/use-register';
import i18n from '@/shared/lib/i18n';
import { Button, ErrorMessage, Input, Tabs } from '@heroui/react';
import { Icon } from '@iconify/react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import z from 'zod';

const registerSchema = z
  .object({
    email: z
      .string()
      .min(1, i18n.t('validation.required'))
      .refine((val) => z.email().safeParse(val).success, {
        message: i18n.t('validation.email'),
      }),
    password: z.string().min(1, i18n.t('validation.required')),
    confirmPassword: z.string().min(1, i18n.t('validation.required')),
  })
  .refine(data => data.password === data.confirmPassword, {
    message: i18n.t('auth.register.passwordsMismatch'),
    path: ['confirmPassword'],
  });

type RegisterSchemaData = z.infer<typeof registerSchema>;

const inputCn =
  'bg-surface border border-border rounded-xl h-14 px-4 text-foreground placeholder:text-muted text-sm w-full hover:border-border/60 focus-visible:border-accent outline-none';

export const RegisterPage = () => {
  const { t } = useTranslation();
  const { mutate, isPending, isError } = useRegister();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const formMethod = useForm<RegisterSchemaData>({
    resolver: zodResolver(registerSchema),
    mode: 'all',
    defaultValues: { email: '', password: '', confirmPassword: '' },
  });

  const handleClick = (data: RegisterSchemaData) => {
    mutate(
      { email: data.email, password: data.password, confirm_password: data.confirmPassword },
      { onSuccess: () => navigate('/auth/login') },
    );
  };

  return (
    <div className="min-h-screen flex">
      {/* LEFT PANEL — forced dark */}
      <div className="dark w-150 shrink-0 flex items-center justify-center bg-background">
        <div className="w-80 flex flex-col gap-8">
          {/* Heading */}
          <div className="flex flex-col gap-2">
            <h1 className="text-foreground text-4xl font-semibold leading-tight tracking-tight">
              {t('auth.register.title')}
            </h1>
            <p className="text-muted text-sm leading-5">
              {t('auth.register.subtitle')}
            </p>
          </div>

          {/* Tabs */}
          <Tabs
            selectedKey="signup"
            onSelectionChange={key => {
              if (key === 'signin') navigate('/auth/login');
            }}
          >
            <Tabs.ListContainer>
              <Tabs.List
                aria-label="Auth tabs"
                className="bg-default rounded-full p-1 gap-0 w-full"
              >
                <Tabs.Tab
                  id="signin"
                  className="rounded-full h-10 text-sm text-muted aria-selected:text-foreground flex-1"
                >
                  <span className="flex items-center gap-2">
                    <Icon icon="mdi:lock-outline" width={16} />
                    {t('auth.signIn')}
                  </span>
                  <Tabs.Indicator className="bg-surface-secondary rounded-full" />
                </Tabs.Tab>
                <Tabs.Tab
                  id="signup"
                  className="rounded-full h-10 text-sm text-muted aria-selected:text-foreground flex-1"
                >
                  <span className="flex items-center gap-2">
                    <Icon icon="mdi:account-outline" width={16} />
                    {t('auth.signUp')}
                  </span>
                  <Tabs.Indicator className="bg-surface-secondary rounded-full" />
                </Tabs.Tab>
              </Tabs.List>
            </Tabs.ListContainer>
          </Tabs>

          {/* Form */}
          <div className="flex flex-col gap-5">
            {/* Email */}
            <Controller
              name="email"
              control={formMethod.control}
              render={({ field, fieldState }) => (
                <div className="flex flex-col gap-1.5">
                  <label className="text-foreground text-sm font-medium">
                    {t('auth.emailAddress')}
                  </label>
                  <Input
                    {...field}
                    value={field.value ?? ''}
                    placeholder={t('auth.emailPlaceholder')}
                    className={inputCn}
                  />
                  <ErrorMessage>{fieldState.error?.message}</ErrorMessage>
                </div>
              )}
            />

            {/* Password */}
            <Controller
              name="password"
              control={formMethod.control}
              render={({ field, fieldState }) => (
                <div className="flex flex-col gap-1.5">
                  <label className="text-foreground text-sm font-medium">
                    {t('auth.password')}
                  </label>
                  <div className="relative">
                    <Input
                      {...field}
                      value={field.value ?? ''}
                      type={showPassword ? 'text' : 'password'}
                      className={`${inputCn} pr-12`}
                    />
                    <Button
                      isIconOnly
                      variant="ghost"
                      size="sm"
                      onPress={() => setShowPassword(p => !p)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted"
                    >
                      <Icon icon={showPassword ? 'mdi:eye-off' : 'mdi:eye'} width={18} />
                    </Button>
                  </div>
                  <ErrorMessage>{fieldState.error?.message}</ErrorMessage>
                </div>
              )}
            />

            {/* Confirm Password */}
            <Controller
              name="confirmPassword"
              control={formMethod.control}
              render={({ field, fieldState }) => (
                <div className="flex flex-col gap-1.5">
                  <label className="text-foreground text-sm font-medium">
                    {t('auth.confirmPassword')}
                  </label>
                  <div className="relative">
                    <Input
                      {...field}
                      value={field.value ?? ''}
                      type={showConfirm ? 'text' : 'password'}
                      className={`${inputCn} pr-12`}
                    />
                    <Button
                      isIconOnly
                      variant="ghost"
                      size="sm"
                      onPress={() => setShowConfirm(p => !p)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted"
                    >
                      <Icon icon={showConfirm ? 'mdi:eye-off' : 'mdi:eye'} width={18} />
                    </Button>
                  </div>
                  <ErrorMessage>{fieldState.error?.message}</ErrorMessage>
                </div>
              )}
            />

            {/* Submit */}
            <Button
              onPress={() => formMethod.handleSubmit(handleClick)()}
              isDisabled={isPending}
              className="bg-foreground text-background w-full h-14 rounded-full text-base font-medium"
              size="lg"
            >
              {isPending ? t('auth.register.loading') : t('auth.register.submit')}
            </Button>
            {isError && (
              <ErrorMessage className="text-center">{t('auth.register.error')}</ErrorMessage>
            )}
          </div>
        </div>
      </div>

      {/* RIGHT PANEL — inherits light theme */}
      <div className="flex-1 m-5 bg-surface-secondary rounded-3xl" />
    </div>
  );
};
