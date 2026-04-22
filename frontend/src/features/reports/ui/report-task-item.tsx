import { Surface, Separator } from "@heroui/react";
import { Icon } from "@iconify/react";

interface ReportTaskItemProps {
  title: string;
  schedule: string;
  description?: string;
  lastRunTime?: string;
}

export function ReportTaskItem({
  title,
  schedule,
  description,
  lastRunTime,
}: ReportTaskItemProps) {
  const hasSecondRow = description !== undefined || lastRunTime !== undefined;

  return (
    <Surface
      variant="default"
      className="flex w-full flex-col rounded-3xl border border-white/8 px-5 py-4"
    >
      <div className="flex w-full items-center justify-between">
        <span className="text-[14px] font-semibold text-foreground">
          {title}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[14px] text-muted">{schedule}</span>
          <Icon icon="mdi:repeat" width={16} className="shrink-0 text-muted" />
        </div>
      </div>

      {hasSecondRow && (
        <>
          <Separator className="my-2" />
          <div className="flex w-full items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Icon
                icon="mdi:comment-outline"
                width={14}
                className="shrink-0 text-muted"
              />
              {description && (
                <span className="text-[14px] text-muted">{description}</span>
              )}
            </div>
            {lastRunTime && (
              <span className="text-[14px] text-muted">{lastRunTime}</span>
            )}
          </div>
        </>
      )}
    </Surface>
  );
}

