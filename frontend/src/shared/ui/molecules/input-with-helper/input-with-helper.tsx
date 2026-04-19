import { Input, type InputRootProps } from '@heroui/react';

export type Props = InputRootProps & {
  helperText?: string;
};

export const InputWithHelper = ({ helperText, ...rest }: Props) => {
  return (
    <div className='flex flex-col gap-3'>
      <Input {...rest} />
      <span className='text-black'>{helperText}</span>
    </div>
  );
};
