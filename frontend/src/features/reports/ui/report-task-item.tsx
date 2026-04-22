import { Surface } from "@heroui/react";
import { Icon } from "@iconify/react";

interface ReportTaskItemProps {
  title: string;
  schedule: string;
}

export function ReportTaskItem({ title, schedule }: ReportTaskItemProps) {
  return (
    <Surface
      variant="default"
      className="flex w-full items-center justify-between rounded-3xl border border-white/8 px-5 py-4"
    >
      <span className="text-sm font-semibold text-foreground">{title}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted">{schedule}</span>
        <Icon icon="mdi:repeat" width={16} className="shrink-0 text-muted" />
      </div>
    </Surface>
  );
}
