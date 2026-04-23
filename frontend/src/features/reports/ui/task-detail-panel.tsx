import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Button, ScrollShadow } from '@heroui/react';
import { Icon } from '@iconify/react';

import {
  dispatchReportTask,
  fetchReportTaskById,
  type ReportTask,
  type ReportRun,
} from '@/features/analytics/api/analytics-api';
import { Archive, ArrowsRotateLeft } from '@/shared/ui/assets/icons';

interface RunItemProps {
  run: ReportRun;
}

function ResultCard({ run }: { run: ReportRun }) {
  const { t } = useTranslation();
  const date = run.finished_at ?? run.started_at ?? run.created_at;
  const formattedDate = new Date(date).toLocaleDateString('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  return (
    <div className='relative overflow-hidden rounded-2xl border border-border bg-white/3 shadow-[inset_0px_0px_22px_0px_rgba(255,255,255,0.04)] backdrop-blur-md'>
      <div className='flex flex-col gap-4 p-5'>
        {/* card header */}
        <div className='flex items-start gap-2'>
          <div className='flex min-w-0 flex-1 flex-col gap-1'>
            <p className='truncate text-base font-semibold text-foreground'>
              {run.query_text.length > 60
                ? `${run.query_text.slice(0, 60)}…`
                : run.query_text}
            </p>
            <p className='truncate text-sm text-muted'>{formattedDate}</p>
          </div>
          <div className='flex shrink-0 items-center gap-1.5'>
            <Button
              variant='outline'
              size='sm'
              className='h-8 border-border px-3 text-sm font-medium'
            >
              <Icon
                icon='mdi:plus'
                width={14}
              />
              {t('reports.detail.createTask')}
            </Button>
            <Button
              isIconOnly
              variant='outline'
              size='sm'
              aria-label={t('reports.detail.moreActions')}
              className='h-8 w-8 min-w-8 border-border'
            >
              <Icon
                icon='mdi:dots-vertical'
                width={14}
              />
            </Button>
          </div>
        </div>

        {/* result content */}
        {run.result_summary && (
          <p className='text-sm leading-relaxed text-foreground/80'>
            {run.result_summary}
          </p>
        )}
        {run.status === 'failed' && run.error && (
          <p className='text-sm text-danger'>{run.error}</p>
        )}
      </div>
    </div>
  );
}

function RunItem({ run }: RunItemProps) {
  const [expanded, setExpanded] = useState(false);

  const date = run.started_at ?? run.created_at;
  const formattedDate = new Date(date).toLocaleDateString('ru-RU', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  const hasContent =
    !!run.result_summary || (run.status === 'failed' && !!run.error);

  return (
    <div
      className={`overflow-hidden border border-white/8 bg-surface transition-[border-radius] duration-200 ${
        expanded ? 'rounded-3xl' : 'rounded-2xl'
      }`}
    >
      <button
        type='button'
        className='flex w-full cursor-pointer items-center justify-between px-4 py-3 text-left transition-colors hover:bg-white/4'
        onClick={() => hasContent && setExpanded(v => !v)}
        aria-expanded={expanded}
        disabled={!hasContent}
      >
        <div className='flex flex-col gap-1 pl-2'>
          <span className='text-base font-semibold text-foreground'>
            {run.query_text.length > 55
              ? `${run.query_text.slice(0, 55)}…`
              : run.query_text}
          </span>
          <span className='text-xs tracking-tight text-muted'>
            {formattedDate}
          </span>
        </div>
        {hasContent && (
          <Icon
            icon='mdi:chevron-down'
            width={20}
            className={`shrink-0 text-muted transition-transform ${expanded ? 'rotate-180' : ''}`}
          />
        )}
      </button>

      {expanded && hasContent && (
        <div className='border-t border-white/8 px-3 py-4'>
          {run.result_summary && (
            <p className='mb-4 text-base leading-relaxed text-foreground'>
              {run.result_summary}
            </p>
          )}
          {run.status === 'failed' && run.error && (
            <p className='mb-4 text-sm text-danger'>{run.error}</p>
          )}
          <ResultCard run={run} />
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* TaskDetailPanel                                                     */
/* ------------------------------------------------------------------ */

interface TaskDetailPanelProps {
  task: ReportTask;
  schedule: string;
  onClose: () => void;
  onEdit?: () => void;
  onTogglePause?: () => void;
}

export function TaskDetailPanel({
  task,
  schedule,
  onClose,
  onEdit,
  onTogglePause,
}: TaskDetailPanelProps) {
  const { t } = useTranslation();

  const { data: freshTask, refetch } = useQuery({
    queryKey: ['report-task', task.id],
    queryFn: () => fetchReportTaskById(task.id),
    enabled: !!task.id,
    placeholderData: task,
  });

  const currentTask = freshTask ?? task;

  const dispatchMutation = useMutation({
    mutationFn: () => dispatchReportTask(task.id),
    onSuccess: () => {
      setTimeout(refetch, 10000);
    },
  });

  return (
    <div className='flex h-full w-full flex-col overflow-hidden bg-background'>
      {/* Header */}
      <div className='shrink-0 px-5 pt-5 pb-3'>
        {/* Title row */}
        <div className='flex items-center justify-between'>
          <h2 className='text-xl font-semibold tracking-tight text-foreground'>
            {currentTask.title}
          </h2>

          <div className='flex items-center'>
            <Button
              isIconOnly
              variant='ghost'
              size='sm'
              aria-label={t('reports.detail.archive')}
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

        {/* Meta row */}
        <div className='mt-3 flex flex-col gap-2'>
          <div className='flex flex-wrap items-center gap-3'>
            {/* schedule label */}
            <div className='flex items-center gap-1 text-sm text-foreground'>
              <ArrowsRotateLeft
                width={14}
                className='shrink-0'
              />
              <span>{schedule}</span>
            </div>

            {/* action buttons */}
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
                aria-label={
                  currentTask.is_active
                    ? t('reports.detail.pause')
                    : t('reports.detail.resume')
                }
                onPress={onTogglePause}
                className='h-8 w-8 min-w-8 border-border'
              >
                <Icon
                  icon={currentTask.is_active ? 'mdi:pause' : 'mdi:play'}
                  width={14}
                />
              </Button>
              <Button
                variant='outline'
                size='sm'
                isPending={dispatchMutation.isPending}
                onPress={() => dispatchMutation.mutate()}
                className='h-8 border-border px-3 text-sm font-medium'
              >
                {!dispatchMutation.isPending && (
                  <Icon
                    icon='mdi:play-circle-outline'
                    width={14}
                  />
                )}
                {t('reports.detail.generateReport')}
              </Button>
            </div>
          </div>

          {/* description */}
          {currentTask.instruction && (
            <p className='text-sm leading-snug text-muted'>
              {currentTask.instruction}
            </p>
          )}
        </div>
      </div>

      {/* Runs list */}
      <ScrollShadow
        className='min-h-0 flex-1'
        hideScrollBar
      >
        <div className='flex flex-col gap-3 px-5 pb-6 pt-1'>
          {currentTask.reports && currentTask.reports.length > 0 ? (
            currentTask.reports.map(run => (
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
