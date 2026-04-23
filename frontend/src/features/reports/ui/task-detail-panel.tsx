import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Button, ScrollShadow, Chip } from '@heroui/react';
import { Icon } from '@iconify/react';

import {
  fetchTaskReports,
  type ReportTask,
  type ReportRun,
} from '@/features/analytics/api/analytics-api';
import { Archive, ArrowsRotateLeft } from '@/shared/ui/assets/icons';

interface RunItemProps {
  run: ReportRun;
}

function RunItem({ run }: RunItemProps) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);

  const date = run.started_at ?? run.created_at;
  const formattedDate = new Date(date).toLocaleDateString('ru-RU', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  const statusLabel: Record<ReportRun['status'], string> = {
    pending: t('reports.detail.runPending'),
    running: t('reports.detail.runRunning'),
    done: t('reports.detail.runDone'),
    failed: t('reports.detail.runFailed'),
  };

  const statusColor: Record<
    ReportRun['status'],
    'default' | 'primary' | 'success' | 'danger'
  > = {
    pending: 'default',
    running: 'primary',
    done: 'success',
    failed: 'danger',
  };

  return (
    <div className='flex flex-col overflow-hidden rounded-2xl border border-white/8 bg-surface'>
      <button
        type='button'
        className='flex w-full cursor-pointer items-center justify-between px-4 py-3 text-left transition-colors hover:bg-white/4'
        onClick={() => setExpanded(v => !v)}
        aria-expanded={expanded}
      >
        <div className='flex flex-col gap-1'>
          <span className='text-sm font-semibold text-foreground'>
            {run.query_text.length > 60
              ? `${run.query_text.slice(0, 60)}…`
              : run.query_text}
          </span>
          <span className='text-xs text-muted'>{formattedDate}</span>
        </div>
        <div className='flex shrink-0 items-center gap-2'>
          <Chip
            size='sm'
            color={statusColor[run.status]}
            variant='flat'
            radius='full'
          >
            {statusLabel[run.status]}
          </Chip>
          <Icon
            icon='mdi:chevron-down'
            width={20}
            className={`shrink-0 text-muted transition-transform ${expanded ? 'rotate-180' : ''}`}
          />
        </div>
      </button>

      {expanded && (
        <div className='border-t border-white/8 px-4 py-4'>
          {run.status === 'failed' && run.error && (
            <p className='text-sm text-danger'>{run.error}</p>
          )}
          {run.result_summary && (
            <p className='text-sm leading-relaxed text-foreground'>
              {run.result_summary}
            </p>
          )}
          {!run.result_summary && run.status !== 'failed' && (
            <p className='text-sm text-muted'>—</p>
          )}
        </div>
      )}
    </div>
  );
}

interface TaskDetailPanelProps {
  task: ReportTask;
  schedule: string;
  onClose: () => void;
  onEdit?: () => void;
  onTogglePause?: () => void;
  onGenerateReport?: () => void;
}

export function TaskDetailPanel({
  task,
  schedule,
  onClose,
  onEdit,
  onTogglePause,
  onGenerateReport,
}: TaskDetailPanelProps) {
  const { t } = useTranslation();

  const { data: runsData } = useQuery({
    queryKey: ['task-runs', task.id],
    queryFn: () => fetchTaskReports(task.id),
    enabled: !!task.id,
  });

  return (
    <div className='flex h-full w-full flex-col gap-6 overflow-hidden bg-background p-5'>
      {/* Header */}
      <div className='flex flex-col gap-3 shrink-0'>
        {/* Title row */}
        <div className='flex items-center justify-between'>
          <h2 className='text-xl font-semibold tracking-tight text-foreground'>
            {task.title}
          </h2>

          <div className='flex items-center'>
            <Button
              isIconOnly
              variant='ghost'
              size='sm'
              aria-label={t('reports.detail.close')}
              className='text-foreground'
            >
              <Archive
                width={16}
                height={16}
              />
            </Button>
            <Button
              isIconOnly
              variant='ghost'
              size='sm'
              aria-label={t('reports.detail.close')}
              onPress={onClose}
              className='text-foreground'
            >
              <Icon
                icon='mdi:close'
                width={16}
              />
            </Button>
          </div>
        </div>

        {/* Meta row: schedule + action buttons */}
        <div className='flex flex-col gap-2'>
          <div className='flex flex-wrap items-center gap-3'>
            <div className='flex items-center gap-1 text-sm text-foreground'>
              <ArrowsRotateLeft
                width={14}
                className='shrink-0'
              />
              <span>{schedule}</span>
            </div>

            <div className='flex items-center gap-1.5'>
              <Button
                isIconOnly
                variant='outline'
                size='sm'
                aria-label={t('reports.detail.edit')}
                onPress={onEdit}
                className='h-8 w-8 min-w-8 border-border'
              >
                <Icon
                  icon='mdi:pencil-outline'
                  width={14}
                />
              </Button>
              <Button
                isIconOnly
                variant='outline'
                size='sm'
                aria-label={t('reports.detail.pause')}
                onPress={onTogglePause}
                className='h-8 w-8 min-w-8 border-border'
              >
                <Icon
                  icon={task.is_active ? 'mdi:pause' : 'mdi:play'}
                  width={14}
                />
              </Button>
              <Button
                variant='outline'
                size='sm'
                onPress={onGenerateReport}
                className='h-8 border-border px-3 text-sm font-medium'
              >
                <Icon
                  icon='mdi:play-circle-outline'
                  width={14}
                />
                {t('reports.detail.generateReport')}
              </Button>
            </div>
          </div>

          {/* Description */}
          {task.instruction && (
            <p className='text-sm text-muted'>{task.instruction}</p>
          )}
        </div>
      </div>

      {/* Runs list */}
      <ScrollShadow
        className='min-h-0 flex-1'
        hideScrollBar
      >
        <div className='flex flex-col gap-3 pb-4'>
          {runsData && runsData.items.length > 0 ? (
            runsData.items.map(run => (
              <RunItem
                key={run.id}
                run={run}
              />
            ))
          ) : (
            <p className='py-8 text-center text-sm text-muted'>
              {t('reports.detail.noRuns')}
            </p>
          )}
        </div>
      </ScrollShadow>
    </div>
  );
}
