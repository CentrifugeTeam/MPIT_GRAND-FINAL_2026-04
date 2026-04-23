import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Button, ScrollShadow } from '@heroui/react';
import { Icon } from '@iconify/react';
import { AreaChart, Area, XAxis, ResponsiveContainer } from 'recharts';

import {
  dispatchReportTask,
  fetchReportTaskById,
  type ReportTask,
  type ReportRun,
} from '@/features/analytics/api/analytics-api';
import { Archive, ArrowsRotateLeft } from '@/shared/ui/assets/icons';

/* ------------------------------------------------------------------ */
/* Mock data                                                           */
/* ------------------------------------------------------------------ */

type MockChartRow = { label: string; primary: number; secondary: number };
type MockMetric = { text: string; period: string };

type MockRun = ReportRun & {
  chartData?: MockChartRow[];
  chartTitle?: string;
  chartSubtitle?: string;
  metric?: MockMetric;
};

const MOCK_CHART_DATA: MockChartRow[] = [
  { label: 'Jan', primary: 4200, secondary: 2800 },
  { label: 'Feb', primary: 5100, secondary: 3400 },
  { label: 'Mar', primary: 7300, secondary: 5200 },
  { label: 'Apr', primary: 4800, secondary: 3100 },
  { label: 'May', primary: 5600, secondary: 3800 },
  { label: 'Jun', primary: 6800, secondary: 4500 },
];

const MOCK_RUNS: MockRun[] = [
  {
    id: 'm1',
    task_id: null,
    user_id: 'mock',
    status: 'done',
    query_text: 'Количество совершенных поездок',
    result_summary:
      'Вот данные по отменам поездок за февраль 2026. Наибольшее количество отмен зафиксировано в Москве (342), далее идут Санкт-Петербург (218) и Екатеринбург (156).',
    started_at: '2026-04-22T07:50:00Z',
    finished_at: '2026-04-22T07:50:00Z',
    created_at: '2026-04-22T07:50:00Z',
    updated_at: '2026-04-22T07:50:00Z',
    error: null,
    result_payload: null,
    chartData: MOCK_CHART_DATA,
    chartTitle: 'Количество совершенных поездок',
    chartSubtitle: 'За январь месяц 2026 год',
    metric: { text: 'Рост поездок на 5.6%', period: 'За январь месяц 2026 год' },
  },
  {
    id: 'm2',
    task_id: null,
    user_id: 'mock',
    status: 'done',
    query_text: 'Количество совершенных поездок',
    result_summary: null,
    started_at: '2026-04-22T07:50:00Z',
    finished_at: '2026-04-22T07:50:00Z',
    created_at: '2026-04-22T07:50:00Z',
    updated_at: '2026-04-22T07:50:00Z',
    error: null,
    result_payload: null,
  },
  {
    id: 'm3',
    task_id: null,
    user_id: 'mock',
    status: 'done',
    query_text: 'Количество совершенных поездок',
    result_summary: null,
    started_at: '2026-04-22T07:50:00Z',
    finished_at: '2026-04-22T07:50:00Z',
    created_at: '2026-04-22T07:50:00Z',
    updated_at: '2026-04-22T07:50:00Z',
    error: null,
    result_payload: null,
  },
  {
    id: 'm4',
    task_id: null,
    user_id: 'mock',
    status: 'done',
    query_text: 'Количество совершенных поездок',
    result_summary: null,
    started_at: '2026-04-22T07:50:00Z',
    finished_at: '2026-04-22T07:50:00Z',
    created_at: '2026-04-22T07:50:00Z',
    updated_at: '2026-04-22T07:50:00Z',
    error: null,
    result_payload: null,
  },
];

/* ------------------------------------------------------------------ */
/* ResultCard                                                          */
/* ------------------------------------------------------------------ */

interface ResultCardProps {
  run: MockRun;
}

function ResultCard({ run }: ResultCardProps) {
  const date = run.finished_at ?? run.started_at ?? run.created_at;
  const formattedDate = new Date(date).toLocaleDateString('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  const title = run.chartTitle ?? (run.query_text.length > 60
    ? `${run.query_text.slice(0, 60)}…`
    : run.query_text);

  return (
    <div className='relative overflow-hidden rounded-2xl border border-border bg-white/3 shadow-[inset_0px_0px_22px_0px_rgba(255,255,255,0.04)] backdrop-blur-md'>
      <div className='flex flex-col gap-3 p-5 pb-4'>
        {/* card header */}
        <div className='flex items-start justify-between gap-2'>
          <div className='flex min-w-0 flex-1 flex-col gap-0.5'>
            <p className='truncate text-base font-semibold text-foreground'>
              {title}
            </p>
            <p className='text-sm text-muted'>
              {run.chartSubtitle ?? formattedDate}
            </p>
          </div>
          <Button
            isIconOnly
            variant='ghost'
            size='sm'
            aria-label='Дополнительно'
            className='h-8 w-8 min-w-8 shrink-0 text-muted'
          >
            <Icon
              icon='mdi:dots-vertical'
              width={16}
            />
          </Button>
        </div>

        {/* area chart */}
        {run.chartData && run.chartData.length > 0 && (
          <div className='h-[140px] w-full'>
            <ResponsiveContainer
              width='100%'
              height='100%'
            >
              <AreaChart
                data={run.chartData}
                margin={{ top: 4, right: 0, bottom: 0, left: 0 }}
              >
                <defs>
                  <linearGradient
                    id='gradPrimary'
                    x1='0'
                    y1='0'
                    x2='0'
                    y2='1'
                  >
                    <stop
                      offset='0%'
                      stopColor='#4ade80'
                      stopOpacity={0.35}
                    />
                    <stop
                      offset='100%'
                      stopColor='#4ade80'
                      stopOpacity={0}
                    />
                  </linearGradient>
                  <linearGradient
                    id='gradSecondary'
                    x1='0'
                    y1='0'
                    x2='0'
                    y2='1'
                  >
                    <stop
                      offset='0%'
                      stopColor='#22c55e'
                      stopOpacity={0.2}
                    />
                    <stop
                      offset='100%'
                      stopColor='#22c55e'
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey='label'
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: 'var(--color-muted, #888)' }}
                  interval='preserveStartEnd'
                />
                <Area
                  type='monotone'
                  dataKey='primary'
                  stroke='#4ade80'
                  strokeWidth={2}
                  fill='url(#gradPrimary)'
                  dot={false}
                  activeDot={false}
                />
                <Area
                  type='monotone'
                  dataKey='secondary'
                  stroke='#22c55e'
                  strokeWidth={1.5}
                  fill='url(#gradSecondary)'
                  dot={false}
                  activeDot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* metric footer */}
        {run.metric && (
          <div className='flex flex-col gap-0.5 pt-1'>
            <p className='text-sm font-semibold text-foreground'>
              {run.metric.text}
            </p>
            <p className='text-xs text-muted'>{run.metric.period}</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* RunItem                                                             */
/* ------------------------------------------------------------------ */

interface RunItemProps {
  run: MockRun;
  defaultExpanded?: boolean;
}

function RunItem({ run, defaultExpanded = false }: RunItemProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const date = run.started_at ?? run.created_at;
  const formattedDate = new Date(date).toLocaleDateString('ru-RU', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  const hasContent =
    !!run.result_summary || (run.status === 'failed' && !!run.error) || !!run.chartData;

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
          {run.result_summary && (
            <p className='text-base leading-relaxed text-foreground'>
              {run.result_summary}
            </p>
          )}
          {run.status === 'failed' && run.error && (
            <p className='text-sm text-danger'>{run.error}</p>
          )}
          {(run.chartData || run.result_summary) && (
            <ResultCard run={run} />
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

  // TODO: replace with currentTask.reports when API is ready
  const runs = MOCK_RUNS;

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
    </div>
  );
}
