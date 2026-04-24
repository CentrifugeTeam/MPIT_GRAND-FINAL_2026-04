import { zodResolver } from '@hookform/resolvers/zod';
import { Button, Checkbox, ErrorMessage, Input, Tabs } from '@heroui/react';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import z from 'zod';

import { useRegister } from '@/entities/auth';
import i18n from '@/shared/lib/i18n';
import {
  ArrowRightToSquareIcon,
  EyeCloseIcon,
  EyeIcon,
  PersonPlusIcon,
} from '@/shared/ui/assets/icons';

const registerSchema = z
  .object({
    email: z
      .string()
      .min(1, i18n.t('validation.required'))
      .refine(val => z.email().safeParse(val).success, {
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
  'bg-zinc-900 border-transparent rounded-xl h-11 px-3 text-zinc-50 placeholder:text-zinc-400 text-sm w-full focus-visible:ring-1 focus-visible:ring-zinc-600 outline-none';

export function AuthRegisterForm() {
  const { t } = useTranslation();
  const { mutateAsync, isPending, isError } = useRegister();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [confTerms, setConfirmTerms] = useState(false);

  const formMethod = useForm<RegisterSchemaData>({
    resolver: zodResolver(registerSchema),
    mode: 'all',
    defaultValues: { email: '', password: '', confirmPassword: '' },
  });

  const handleClick = async (data: RegisterSchemaData) => {
    try {
      await mutateAsync({
        email: data.email,
        password: data.password,
        confirm_password: data.confirmPassword,
      });
      navigate('/auth/login', {
        replace: true,
        state: { registeredEmail: data.email.trim() },
      });
    } catch {
      /* registration failed — isError handles UI */
    }
  };

  return (
    <div className='dark min-h-screen flex bg-background'>
      <div className='w-1/2 shrink-0 flex items-center justify-center'>
        <div className='w-96 flex flex-col gap-8'>
          <div className='flex flex-col gap-3'>
            <h1 className='text-foreground text-3xl font-medium leading-9'>
              {t('auth.register.title')}
            </h1>
            <p className='text-foreground/80 text-base leading-relaxed'>
              {t('auth.register.subtitle')}
            </p>
          </div>

          <Tabs
            selectedKey='signup'
            onSelectionChange={key => {
              if (key === 'signin') navigate('/auth/login');
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
                    <ArrowRightToSquareIcon
                      width={16}
                      height={16}
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
                    <PersonPlusIcon
                      width={16}
                      height={16}
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
                        {showPassword ? (
                          <EyeCloseIcon
                            width={16}
                            height={16}
                          />
                        ) : (
                          <EyeIcon
                            height={16}
                            width={16}
                          />
                        )}
                      </Button>
                    </div>
                    <ErrorMessage>{fieldState.error?.message}</ErrorMessage>
                  </div>
                )}
              />

              <Controller
                name='confirmPassword'
                control={formMethod.control}
                render={({ field, fieldState }) => (
                  <div className='flex flex-col gap-1'>
                    <label className='text-zinc-50 text-sm font-medium'>
                      {t('auth.confirmPassword')}
                    </label>
                    <div className='relative'>
                      <Input
                        {...field}
                        value={field.value ?? ''}
                        type={showConfirm ? 'text' : 'password'}
                        className={`${inputCn} pr-12`}
                      />
                      <Button
                        isIconOnly
                        variant='ghost'
                        size='sm'
                        onPress={() => setShowConfirm(p => !p)}
                        className='absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400'
                      >
                        {showConfirm ? (
                          <EyeCloseIcon
                            width={16}
                            height={16}
                          />
                        ) : (
                          <EyeIcon
                            height={16}
                            width={16}
                          />
                        )}
                      </Button>
                    </div>
                    <ErrorMessage>{fieldState.error?.message}</ErrorMessage>
                  </div>
                )}
              />
            </div>

            <div className='flex items-center justify-between w-full -mt-2'>
              <Checkbox
                isSelected={confTerms}
                onChange={setConfirmTerms}
                className='gap-3'
              >
                <Checkbox.Control>
                  <Checkbox.Indicator />
                </Checkbox.Control>
                <Checkbox.Content className='text-sm font-medium text-zinc-50'>
                  {t('auth.terms')}
                </Checkbox.Content>
              </Checkbox>
            </div>

            <Button
              onPress={() => void formMethod.handleSubmit(handleClick)()}
              isDisabled={
                isPending || !confTerms || !formMethod.formState.isValid
              }
              className='bg-white text-black w-full h-[52px] rounded-2xl text-base font-medium'
              size='lg'
            >
              {isPending
                ? t('auth.register.loading')
                : t('auth.register.submit')}
            </Button>
            {isError && (
              <ErrorMessage className='text-center'>
                {t('auth.register.error')}
              </ErrorMessage>
            )}
          </div>
        </div>
      </div>
      <div className="flex-1 mr-5 bg-[url('/auth.png')] bg-cover bg-center  border-l border-border" />
    </div>
  );
}
