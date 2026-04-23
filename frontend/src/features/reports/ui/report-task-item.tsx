import { Surface, Separator } from '@heroui/react';
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
                className='flex items-center justify-center rounded-full text-muted transition-colors hover:bg-white/10 hover:text-foreground'
                onClick={e => {
                  e.stopPropagation();
                  onPause?.(id);
                }}
              >
                <Icon
                  icon='mdi:pause-circle-outline'
                  width={16}
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
                <Icon
                  icon='mdi:play-circle-outline'
                  width={16}
                  className='text-muted'
                />
              </button>
            )
          ) : !isActive ? (
            <>
              <Icon
                icon='mdi:pause-circle-outline'
                width={16}
                className='shrink-0 text-warning'
              />
              <span className='text-[14px] text-warning'>Приостановлено</span>
            </>
          ) : (
            <>
              <span className='text-[14px] text-muted'>{schedule}</span>
              <Icon
                icon='mdi:repeat'
                width={16}
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
              <Icon
                icon='mdi:comment-outline'
                width={14}
                className='shrink-0 text-muted'
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
