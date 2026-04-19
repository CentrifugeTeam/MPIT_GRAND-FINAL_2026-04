import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import z from 'zod';

const mandatoryField = 'Поле обязательно';

const loginSchema = z.object({
  email: z
    .string(mandatoryField)
    .min(1)
    .refine(val => {
      if (!val) {
        return true;
      }
    }),
  password: z
    .string(mandatoryField)
    .min(1)
    .refine(val => {
      if (!val) {
        return true;
      }
    }),
});

type LoginSchemaData = z.infer<typeof loginSchema>;

export type Props = {};

export const LoginPage = ({}: Props) => {
  const formMethod = useForm<LoginSchemaData>({
    resolver: zodResolver(loginSchema),
    mode: 'all',
  });

  return <div></div>;
};
