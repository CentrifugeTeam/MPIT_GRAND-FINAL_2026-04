import { useState } from 'react';
import { Icon } from '@iconify/react';
import { useNavigate } from 'react-router';
import { ScrollShadow, Spinner } from '@heroui/react';

import { FigmaAnalyticsSidebar, useAnalyticsPanel } from '@/features/analytics';
import type { ReportTask } from '@/features/analytics/api/analytics-api';
import { useReportTasks } from '../model/use-report-tasks';
import { CreateReportModal } from './create-report-modal';
import { ReportTaskItem } from './report-task-item';
import { useDataSources } from '../model/use-data-sources';

const WEEK_DAYS = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];

function trimTime(t: string): string {
  return t.slice(0, 5);
}

function formatSchedule(task: ReportTask): string {
  switch (task.schedule_type) {
    case 'once': {
      if (!task.once_at) return 'Однократно';
      const d = new Date(task.once_at);
      const dd = String(d.getDate()).padStart(2, '0');
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const yyyy = d.getFullYear();
      const hhmm = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
      return `${dd}.${mm}.${yyyy} в ${hhmm}`;
    }
    case 'daily':
      return task.daily_time
        ? `Ежедневно в ${trimTime(task.daily_time)}`
        : 'Ежедневно';
    case 'weekly': {
      const day = task.weekly_day != null ? WEEK_DAYS[task.weekly_day] : null;
      const time = task.weekly_time ? trimTime(task.weekly_time) : null;
      if (day && time) return `Раз в неделю, ${day} в ${time}`;
      if (time) return `Раз в неделю в ${time}`;
      if (day) return `Раз в неделю, ${day}`;
      return 'Раз в неделю';
    }
    case 'monthly':
      return task.monthly_time
        ? `Ежемесячно в ${trimTime(task.monthly_time)}`
        : 'Ежемесячно';
    case 'yearly':
      return task.yearly_time
        ? `Ежегодно в ${trimTime(task.yearly_time)}`
        : 'Ежегодно';
    default:
      return task.schedule_type;
  }
}

export function ReportsDashboard() {
  const p = useAnalyticsPanel();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const { data, isLoading, isError, refetch } = useReportTasks();

  const handleTaskClick = (id: string) => {
    setSelectedTaskId(prev => (prev === id ? null : id));
  };
  const { data: dataSources, isLoading: isLoadingDataSources } =
    useDataSources();

  return (
    <div className='flex min-h-0 w-full flex-1 items-stretch gap-4 overflow-hidden bg-background pl-0'>
      <div className='flex min-h-0 shrink-0 self-stretch'>
        <FigmaAnalyticsSidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(v => !v)}
          entries={p.entries}
          titles={p.titles}
          activeId={p.activeId}
          editingRowId={p.editingRowId}
          renameDraft={p.renameDraft}
          renameFieldFocused={p.renameFieldFocused}
          renameInputRef={p.renameInputRef}
          historyBusy={p.historyBusy}
          onRenameDraft={p.setRenameDraft}
          onRenameFocus={p.setRenameFieldFocused}
          onCommitRename={p.commitRename}
          onCancelRename={p.cancelRename}
          onSelectEntry={entryId => {
            const entry = p.entries.find(e => e.id === entryId);
            const chatId = entry?.conversationId;
            if (!chatId) return;
            void navigate(`/home/${chatId}`);
          }}
          onStartNewChat={() => void navigate('/home')}
          onLoadHistory={() => void p.loadHistory()}
          onClearAllHistory={() => void p.clearAllHistoryEntries()}
          onStartEditingRow={p.startEditingRow}
          onDeleteHistoryEntry={id => void p.deleteHistoryEntry(id)}
          t={p.t}
        />
      </div>

      <div className='flex min-h-0 min-w-0 flex-1 flex-col'>
        <section className='relative flex min-h-0 flex-1 flex-col rounded-2xl bg-background overflow-hidden py-4'>
          <div className='shrink-0 w-full max-w-[900px] mx-auto px-10 pt-10 pb-4'>
            <div className='flex items-center justify-between gap-4'>
              {!sidebarOpen && (
                <button
                  type='button'
                  onClick={() => setSidebarOpen(true)}
                  className='absolute top-5 left-5 flex size-10 shrink-0 cursor-pointer items-center justify-center rounded-[24px] transition-all hover:bg-[#27272a]/60 active:scale-[0.97]'
                  aria-label={p.t('home.figma.openSidebar')}
                >
                  <Icon
                    icon='mdi:menu'
                    width={22}
                    className='text-foreground'
                  />
                </button>
              )}
              <h1 className='text-2xl font-semibold text-foreground'>
                {p.t('reports.title')}
              </h1>
              <CreateReportModal
                dataSources={dataSources?.items}
                refetch={refetch}
              />
            </div>
          </div>
          <ScrollShadow
            className='min-h-0 flex-1'
            hideScrollBar
          >
            <div className='w-full max-w-[900px] mx-auto px-10 pb-10'>
              {isLoading ||
                (isLoadingDataSources && (
                  <div className='flex items-center justify-center py-16'>
                    <Spinner size='lg' />
                  </div>
                ))}
              {isError && (
                <div className='flex items-center justify-center py-16'>
                  <span className='text-sm text-danger'>
                    {p.t('reports.loadError')}
                  </span>
                </div>
              )}
              {data && (
                <div className='flex flex-col gap-4'>
                  {data.items.map(task => (
                    <ReportTaskItem
                      key={task.id}
                      id={task.id}
                      title={task.title}
                      schedule={formatSchedule(task)}
                      description={task.last_report_sentence?.trim() || undefined}
                      lastRunTime={
                        task.last_run_at
                          ? new Date(task.last_run_at).toLocaleString()
                          : undefined
                      }
                      isSelected={selectedTaskId === task.id}
                      onClick={handleTaskClick}
                    />
                  ))}
                  {data.items.length === 0 && (
                    <p className='py-16 text-center text-sm text-muted'>
                      {p.t('reports.empty')}
                    </p>
                  )}
                </div>
              )}
            </div>
          </ScrollShadow>
        </section>
      </div>

      <div
        className={`shrink-0 overflow-hidden transition-all duration-300 ease-in-out ${
          selectedTaskId ? 'w-[512px]' : 'w-0'
        }`}
      >
        <div className='flex h-full w-[512px] flex-col border-l border-border bg-background'>
          <div className='flex shrink-0 items-center justify-end p-4'>
            <button
              type='button'
              onClick={() => setSelectedTaskId(null)}
              className='flex size-8 items-center justify-center rounded-xl transition-all hover:bg-content2 active:scale-[0.97]'
              aria-label='Закрыть'
            >
              <Icon
                icon='mdi:close'
                width={18}
                className='text-foreground'
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
