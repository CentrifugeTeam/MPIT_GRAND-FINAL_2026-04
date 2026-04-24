import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Button, ScrollShadow, Spinner } from '@heroui/react';
import { Icon } from '@iconify/react';

import {
  deleteReportTask,
  dispatchReportTask,
  fetchReportById,
  fetchReportTaskById,
  type ReportRun,
  type ReportTask,
} from '@/features/analytics/api/analytics-api';
import { FigmaConfirmDialog } from '@/features/analytics/ui/figma-home/figma-confirm-dialog';
import type { ChartPayloadShape } from '@/entities/analytics';
import { AnalyticsCharts } from '@/features/analytics';
import { Archive, ArrowsRotateLeft } from '@/shared/ui/assets/icons';

/* ------------------------------------------------------------------ */
/* RunItem                                                             */
/* ------------------------------------------------------------------ */

interface RunItemProps {
  run: ReportRun;
  defaultExpanded?: boolean;
}

function RunItem({ run, defaultExpanded = false }: RunItemProps) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(defaultExpanded);

  const { data: fullRun, isLoading } = useQuery({
    queryKey: ['report-run', run.id],
    queryFn: () => fetchReportById(run.id),
    enabled: expanded,
    placeholderData: run,
  });

  const date = run.started_at ?? run.created_at;
  const formattedDate = new Date(date).toLocaleDateString('ru-RU', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  const hasContent =
    run.status === 'done' ||
    run.status === 'failed' ||
    !!run.result_summary ||
    !!run.result_payload;

  const resultPayload = fullRun?.result_payload as Record<string, unknown> | null;
  const chartPayload = (resultPayload?.chart_payload ?? null) as ChartPayloadShape | null;

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
        <div className='border-t border-white/8 px-3 py-4 flex flex-col gap-4'>
          {isLoading && !fullRun && (
            <div className='flex items-center justify-center py-6'>
              <Spinner size='sm' />
            </div>
          )}

          {fullRun?.result_summary && (
            <p className='text-base leading-relaxed text-foreground'>
              {fullRun.result_summary}
            </p>
          )}

          {fullRun?.status === 'failed' && fullRun.error && (
            <p className='text-sm text-danger'>{fullRun.error}</p>
          )}

          {chartPayload && (
            <div className='rounded-2xl border border-border bg-white/3 shadow-[inset_0px_0px_22px_0px_rgba(255,255,255,0.04)] backdrop-blur-md p-5'>
              <div className='flex flex-col gap-1 mb-4'>
                <p className='text-base font-semibold text-foreground'>
                  {(fullRun ?? run).query_text.length > 60
                    ? `${(fullRun ?? run).query_text.slice(0, 60)}…`
                    : (fullRun ?? run).query_text}
                </p>
                {(fullRun ?? run).finished_at && (
                  <p className='text-sm text-muted'>
                    {new Date((fullRun ?? run).finished_at!).toLocaleDateString(
                      'ru-RU',
                      {
                        weekday: 'long',
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      },
                    )}
                  </p>
                )}
              </div>
              <AnalyticsCharts payload={chartPayload} />
            </div>
          )}

          {!isLoading && !fullRun?.result_summary && !chartPayload && fullRun?.status !== 'failed' && (
            <p className='text-sm text-muted text-center py-4'>
              {t('reports.detail.noContent')}
            </p>
          )}
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
  onDelete?: () => void;
}

export function TaskDetailPanel({
  task,
  schedule,
  onClose,
  onEdit,
  onTogglePause,
  onDelete,
}: TaskDetailPanelProps) {
  const { t } = useTranslation();
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

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

  const deleteMutation = useMutation({
    mutationFn: () => deleteReportTask(task.id),
    onSuccess: () => {
      setIsDeleteOpen(false);
      onClose();
      onDelete?.();
    },
  });

  const runs = currentTask.reports ?? [];

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
              onPress={() => setIsDeleteOpen(true)}
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

        {/* Schedule row: left = schedule + edit/pause, right = generate */}
        <div className='mt-3 flex items-center justify-between gap-2'>
          <div className='flex items-center gap-2'>
            <div className='flex items-center gap-1 text-sm text-foreground'>
              <ArrowsRotateLeft
                width={14}
                className='shrink-0'
              />
              <span>{schedule}</span>
            </div>
            <div className='flex items-center gap-0.5'>
              <Button
                isIconOnly
                variant='ghost'
                size='sm'
                aria-label={t('reports.detail.edit')}
                onPress={onEdit}
                className='h-7 w-7 min-w-7 text-muted hover:text-foreground'
              >
                <Icon
                  icon='mdi:pencil-outline'
                  width={14}
                />
              </Button>
              <Button
                isIconOnly
                variant='ghost'
                size='sm'
                aria-label={
                  currentTask.is_active
                    ? t('reports.detail.pause')
                    : t('reports.detail.resume')
                }
                onPress={onTogglePause}
                className='h-7 w-7 min-w-7 text-muted hover:text-foreground'
              >
                <Icon
                  icon={currentTask.is_active ? 'mdi:pause' : 'mdi:play'}
                  width={14}
                />
              </Button>
            </div>
          </div>

          <Button
            variant='outline'
            size='sm'
            isPending={dispatchMutation.isPending}
            onPress={() => dispatchMutation.mutate()}
            className='h-8 shrink-0 border-border px-3 text-sm font-medium'
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

        {/* Description */}
        {currentTask.instruction && (
          <p className='mt-2 text-sm leading-snug text-muted'>
            {currentTask.instruction}
          </p>
        )}
      </div>

      {/* Runs list */}
      <ScrollShadow
        className='min-h-0 flex-1'
        hideScrollBar
      >
        <div className='flex flex-col gap-3 px-5 pb-6 pt-1'>
          {runs.length > 0 ? (
            runs.map((run, index) => (
              <RunItem
                key={run.id}
                run={run}
                defaultExpanded={index === 0}
              />
            ))
          ) : (
            <p className='py-8 text-center text-sm text-muted'>
              {t('reports.detail.noRuns')}
            </p>
          )}
        </div>
      </ScrollShadow>

      <FigmaConfirmDialog
        open={isDeleteOpen}
        title={t('reports.detail.deleteConfirmTitle')}
        message={t('reports.detail.deleteConfirmBody')}
        confirmLabel={
          deleteMutation.isPending
            ? '…'
            : t('reports.detail.deleteConfirmOk')
        }
        cancelLabel={t('reports.detail.deleteConfirmCancel')}
        danger
        onConfirm={() => {
          if (!deleteMutation.isPending) deleteMutation.mutate();
        }}
        onCancel={() => {
          if (!deleteMutation.isPending) setIsDeleteOpen(false);
        }}
      />
    </div>
  );
}
