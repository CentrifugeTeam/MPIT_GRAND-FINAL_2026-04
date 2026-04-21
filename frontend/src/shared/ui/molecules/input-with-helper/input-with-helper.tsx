import { Input, type InputRootProps } from "@heroui/react";

export type InputWithHelperProps = InputRootProps & {
  helperText?: string;
};

export const InputWithHelper = ({ helperText, ...rest }: InputWithHelperProps) => {
  return (
    <div className="flex flex-col gap-3">
      <Input {...rest} />
      {helperText && <span className="text-xs text-muted">{helperText}</span>}
    </div>
  );
};
