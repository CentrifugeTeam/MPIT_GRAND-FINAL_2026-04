import { zodResolver } from '@hookform/resolvers/zod';
import { Icon } from '@iconify/react';
import { Button, Checkbox, ErrorMessage, Input, Tabs } from '@heroui/react';
import { useEffect, useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router';
import z from 'zod';

import { useLogin } from '@/entities/auth';
import i18n from '@/shared/lib/i18n';

const loginSchema = z.object({
  email: z
    .string()
    .min(1, i18n.t('validation.required'))
    .refine(val => z.email().safeParse(val).success, {
      message: i18n.t('validation.email'),
    }),
  password: z.string().min(1, i18n.t('validation.required')),
});

type LoginSchemaData = z.infer<typeof loginSchema>;

const inputCn =
  'bg-zinc-900 border-transparent rounded-xl h-11 px-3 text-zinc-50 placeholder:text-zinc-400 text-sm w-full focus-visible:ring-1 focus-visible:ring-zinc-600 outline-none';

type LoginLocationState = { registeredEmail?: string };

export function AuthLoginForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { mutateAsync, isPending, isError } = useLogin();
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const formMethod = useForm<LoginSchemaData>({
    resolver: zodResolver(loginSchema),
    mode: 'all',
    defaultValues: { email: '', password: '' },
  });

  useEffect(() => {
    const registeredEmail = (location.state as LoginLocationState | null)
      ?.registeredEmail;
    if (!registeredEmail?.trim()) return;
    formMethod.setValue('email', registeredEmail.trim(), {
      shouldValidate: true,
      shouldDirty: true,
    });
    navigate(`${location.pathname}${location.search}`, {
      replace: true,
      state: {},
    });
  }, [location.state, location.pathname, location.search, navigate, formMethod]);

  const handleClick = async (data: LoginSchemaData) => {
    try {
      await mutateAsync({ email: data.email, password: data.password });
      navigate('/home', { replace: true });
    } catch {
      /* ошибка парсинга / сети — isError */
    }
  };

  return (
    <div className='dark min-h-screen flex bg-background'>
      <div className='w-1/2 shrink-0 flex items-center justify-center'>
        <div className='w-96 flex flex-col gap-8'>
          <div className='flex flex-col gap-3'>
            <h1 className='text-foreground text-3xl font-medium leading-9'>
              {t('auth.login.title')}
            </h1>
            <p className='text-foreground/80 text-base leading-relaxed'>
              {t('auth.login.subtitle')}
            </p>
          </div>

          <Tabs
            selectedKey='signin'
            onSelectionChange={key => {
              if (key === 'signup') navigate('/auth/register');
            }}
          >
            <Tabs.ListContainer>
              <Tabs.List
                aria-label={t('auth.tabs.ariaLabel')}
                className='bg-zinc-800 rounded-full py-1 gap-0.5 w-full'
              >
                <Tabs.Tab
                  id='signin'
                  className='rounded-full h-9 text-sm text-zinc-400 aria-selected:text-zinc-50 flex-1'
                >
                  <span className='flex items-center gap-1.5'>
                    <Icon
                      icon='mdi:lock-outline'
                      width={16}
                    />
                    {t('auth.signIn')}
                  </span>
                  <Tabs.Indicator className='bg-zinc-700 rounded-full shadow-sm' />
                </Tabs.Tab>
                <Tabs.Tab
                  id='signup'
                  className='rounded-full h-9 text-sm text-zinc-400 aria-selected:text-zinc-50 flex-1'
                >
                  <span className='flex items-center gap-1.5'>
                    <Icon
                      icon='mdi:account-outline'
                      width={16}
                    />
                    {t('auth.signUp')}
                  </span>
                  <Tabs.Indicator className='bg-zinc-700 rounded-full shadow-sm' />
                </Tabs.Tab>
              </Tabs.List>
            </Tabs.ListContainer>
          </Tabs>

          <div className='flex flex-col gap-7'>
            <div className='flex flex-col gap-5'>
              <Controller
                name='email'
                control={formMethod.control}
                render={({ field, fieldState }) => (
                  <div className='flex flex-col gap-1'>
                    <label className='text-zinc-50 text-sm font-medium'>
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

              <Controller
                name='password'
                control={formMethod.control}
                render={({ field, fieldState }) => (
                  <div className='flex flex-col gap-1'>
                    <label className='text-zinc-50 text-sm font-medium'>
                      {t('auth.password')}
                    </label>
                    <div className='relative'>
                      <Input
                        {...field}
                        value={field.value ?? ''}
                        type={showPassword ? 'text' : 'password'}
                        className={`${inputCn} pr-12`}
                      />
                      <Button
                        isIconOnly
                        variant='ghost'
                        size='sm'
                        onPress={() => setShowPassword(p => !p)}
                        className='absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400'
                      >
                        <Icon
                          icon={showPassword ? 'mdi:eye-off' : 'mdi:eye'}
                          width={18}
                        />
                      </Button>
                    </div>
                    <ErrorMessage>{fieldState.error?.message}</ErrorMessage>
                  </div>
                )}
              />
            </div>

            <div className='flex items-center justify-between w-full -mt-2'>
              <Checkbox
                isSelected={rememberMe}
                onChange={setRememberMe}
                className='gap-3'
              >
                <Checkbox.Control>
                  <Checkbox.Indicator />
                </Checkbox.Control>
                <Checkbox.Content className='text-sm font-medium text-zinc-50'>
                  {t('auth.rememberMe')}
                </Checkbox.Content>
              </Checkbox>
              <span className='text-zinc-400 text-sm p-0 h-auto min-w-0 hover:text-zinc-200 cursor-pointer'>
                {t('auth.forgotPassword')}
              </span>
            </div>

            <Button
              onPress={() => formMethod.handleSubmit(handleClick)()}
              isDisabled={isPending || !formMethod.formState.isValid}
              className='bg-white text-black w-full h-[52px] rounded-2xl text-base font-medium'
              size='lg'
            >
              {isPending ? t('auth.login.loading') : t('auth.login.submit')}
            </Button>
            {isError && (
              <ErrorMessage className='text-center'>
                {t('auth.login.error')}
              </ErrorMessage>
            )}
          </div>
        </div>
      </div>
      <div className="flex-1 mr-5 bg-[url('/auth.png')] bg-cover bg-center  border-l border-border" />
    </div>
  );
}
