import {
  ArrowsIcon,
  CommentIcon,
  PauseIcon,
  PlayIcon,
} from '@/shared/ui/assets/icons';
import { Surface, Separator, Button } from '@heroui/react';
import { Icon } from '@iconify/react';
import { useState } from 'react';

interface ReportTaskItemProps {
  id: string;
  title: string;
  schedule: string;
  isActive?: boolean;
  description?: string;
  lastRunTime?: string;
  isSelected?: boolean;
  onClick?: (id: string) => void;
  onPause?: (id: string) => void;
  onResume?: (id: string) => void;
}

export function ReportTaskItem({
  id,
  title,
  schedule,
  isActive = true,
  description,
  lastRunTime,
  isSelected,
  onClick,
  onPause,
  onResume,
}: ReportTaskItemProps) {
  const hasSecondRow = description !== undefined || lastRunTime !== undefined;
  const [hovered, setHovered] = useState(false);

  return (
    <Surface
      variant='default'
      className={`flex w-full cursor-pointer flex-col rounded-3xl border px-5 py-4 transition-colors ${
        isSelected
          ? 'border-primary/50 bg-content1'
          : 'border-white/8 hover:border-white/16'
      }`}
      onClick={() => onClick?.(id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className='flex w-full items-center justify-between'>
        <span className='text-[14px] font-semibold text-foreground'>
          {title}
        </span>
        <div className='flex items-center gap-2'>
          {hovered ? (
            isActive ? (
              <button
                className='flex items-center justify-center rounded-full text-muted transition-colors hover:bg-white/10 hover:text-foreground cursor-pointer'
                onClick={e => {
                  e.stopPropagation();
                  onPause?.(id);
                }}
              >
                <PauseIcon
                  width={16}
                  height={16}
                  className='text-default-foreground'
                />
              </button>
            ) : (
              <button
                className='flex items-center justify-center rounded-full text-warning transition-colors hover:bg-white/10 hover:text-foreground'
                onClick={e => {
                  e.stopPropagation();
                  onResume?.(id);
                }}
              >
                <PlayIcon
                  width={16}
                  height={16}
                  className='text-muted'
                />
              </button>
            )
          ) : !isActive ? (
            <>
              <PauseIcon
                width={16}
                height={16}
                className='shrink-0 text-warning'
              />
              <span className='text-[14px] text-warning'>Приостановлено</span>
            </>
          ) : (
            <>
              <span className='text-[14px]'>{schedule}</span>
              <ArrowsIcon
                width={16}
                height={16}
                className='shrink-0 text-muted'
              />
            </>
          )}
        </div>
      </div>

      {hasSecondRow && (
        <>
          <Separator className='my-2' />
          <div className='flex w-full items-center justify-between'>
            <div className='flex items-center gap-1.5'>
              <CommentIcon
                width={14}
                height={14}
                className='shrink-0 text-muted self-start mt-1'
              />
              {description && (
                <span className='text-[14px] text-muted'>{description}</span>
              )}
            </div>
            {lastRunTime && (
              <span className='text-[14px] text-muted'>{lastRunTime}</span>
            )}
          </div>
        </>
      )}
    </Surface>
  );
}
