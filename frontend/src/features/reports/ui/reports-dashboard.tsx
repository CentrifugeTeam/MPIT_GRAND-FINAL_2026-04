import { useCallback, useEffect, useMemo, useState } from "react";
import { Icon } from "@iconify/react";
import { useLocation, useNavigate } from "react-router";
import { ScrollShadow, Spinner } from "@heroui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";

import {
  answerChatInvite,
  CHAT_INVITES_QUERY_KEY,
  FigmaAnalyticsSidebar,
  useAnalyticsPanel,
} from "@/features/analytics";
import { deleteNotification } from "@/shared/api/notifications-api";
import { readUuidFromAccessToken, useAuthStore } from "@/shared/lib/auth-store";
import { forceReconnectNotificationSse } from "@/shared/lib/notification-sse-broadcast";
import { useNotificationsSse } from "@/shared/lib/use-notifications-sse";
import type {
  ReportTask,
  ReportTaskTemplate,
} from "@/features/analytics/api/analytics-api";
import { patchReportTask } from "@/features/analytics/api/analytics-api";
import { useReportTasks } from "../model/use-report-tasks";
import { useReportTemplates } from "../model/use-report-templates";
import { CreateReportModal } from "./create-report-modal";
import { ReportTaskItem } from "./report-task-item";
import { ReportTemplatesCarousel } from "./report-templates-carousel";
import { TaskDetailPanel } from "./task-detail-panel";
import { useDataSources } from "../model/use-data-sources";

const WEEK_DAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"];

function formatWeeklyDay(weeklyDay: number | null): string | null {
  if (weeklyDay == null) return null;
  // API stores ISO weekday numbers (1..7), while some legacy data may be 0..6.
  if (weeklyDay >= 1 && weeklyDay <= 7) return WEEK_DAYS[weeklyDay - 1] ?? null;
  if (weeklyDay >= 0 && weeklyDay <= 6) return WEEK_DAYS[weeklyDay] ?? null;
  return null;
}

type ReportsLocationState = {
  createReportFromChat?: { instruction: string };
};

function trimTime(t: string): string {
  return t.slice(0, 5);
}

function formatSchedule(task: ReportTask): string {
  switch (task.schedule_type) {
    case "once": {
      if (!task.once_at) return "Однократно";
      const d = new Date(task.once_at);
      const dd = String(d.getDate()).padStart(2, "0");
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      const yyyy = d.getFullYear();
      const hhmm = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
      return `${dd}.${mm}.${yyyy} в ${hhmm}`;
    }
    case "daily":
      return task.daily_time
        ? `Ежедневно в ${trimTime(task.daily_time)}`
        : "Ежедневно";
    case "weekly": {
      const day = formatWeeklyDay(task.weekly_day);
      const time = task.weekly_time ? trimTime(task.weekly_time) : null;
      if (day && time) return `Раз в неделю, ${day} в ${time}`;
      if (time) return `Раз в неделю в ${time}`;
      if (day) return `Раз в неделю, ${day}`;
      return "Раз в неделю";
    }
    case "monthly":
      return task.monthly_day != null
        ? `Ежемесячно ${task.monthly_day} числа`
        : "Ежемесячно";
    case "yearly":
      return task.yearly_date_ddmm
        ? `Ежегодно ${task.yearly_date_ddmm.replace(":", ".")}`
        : "Ежегодно";
    default:
      return task.schedule_type;
  }
}

export function ReportsDashboard() {
  const p = useAnalyticsPanel();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const userUuid = useAuthStore((s) => s.userUuid);
  const accessToken = useAuthStore((s) => s.accessToken);
  const { notifications } = useNotificationsSse(accessToken);
  const inviteNotifications = useMemo(
    () => notifications.filter((n) => n.type === "chat_invite"),
    [notifications],
  );
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [editingTask, setEditingTask] = useState<ReportTask | null>(null);
  const [templatePrefill, setTemplatePrefill] =
    useState<ReportTaskTemplate | null>(null);
  const [chatInstructionPrefill, setChatInstructionPrefill] = useState<
    string | null
  >(null);
  const handleInviteModalAccept = useCallback(
    async (inviteId: string, notificationId: string) => {
      const res = await answerChatInvite(inviteId, "accept");
      const uid = userUuid ?? readUuidFromAccessToken(accessToken);
      if (uid) {
        try {
          await deleteNotification(uid, notificationId);
        } catch (e) {
          if (isAxiosError(e) && e.response?.status === 404) {
            /* same as analytics workspace */
          } else {
            console.warn("deleteNotification failed after chat invite accept", e);
          }
        }
      } else {
        console.warn("deleteNotification skipped: no user id for notification path");
      }
      forceReconnectNotificationSse();
      await queryClient.invalidateQueries({ queryKey: CHAT_INVITES_QUERY_KEY });
      await p.loadHistory();
      if (res.conversation_id) {
        void navigate(`/home/${res.conversation_id}`);
      }
    },
    [navigate, p.loadHistory, queryClient, userUuid, accessToken],
  );

  const handleInviteModalReject = useCallback(
    async (inviteId: string, notificationId: string) => {
      await answerChatInvite(inviteId, "reject");
      const uid = userUuid ?? readUuidFromAccessToken(accessToken);
      if (uid) {
        try {
          await deleteNotification(uid, notificationId);
        } catch (e) {
          if (isAxiosError(e) && e.response?.status === 404) {
            /* */
          } else {
            console.warn("deleteNotification failed after chat invite reject", e);
          }
        }
      } else {
        console.warn("deleteNotification skipped: no user id for notification path");
      }
      forceReconnectNotificationSse();
      await queryClient.invalidateQueries({ queryKey: CHAT_INVITES_QUERY_KEY });
    },
    [queryClient, userUuid, accessToken],
  );

  const { data, isLoading, isError, refetch } = useReportTasks();
  const {
    data: templatesData,
    isLoading: isLoadingTemplates,
    isError: isTemplatesError,
  } = useReportTemplates();

  const selectedTask = data?.items.find((t) => t.id === selectedTaskId) ?? null;

  const pauseMutation = useMutation({
    mutationFn: (taskId: string) =>
      patchReportTask(taskId, { is_active: false }),
    onSuccess: (_data, taskId) => {
      void queryClient.invalidateQueries({ queryKey: ["report-tasks"] });
      void queryClient.invalidateQueries({ queryKey: ["report-task", taskId] });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: (taskId: string) =>
      patchReportTask(taskId, { is_active: true }),
    onSuccess: (_data, taskId) => {
      void queryClient.invalidateQueries({ queryKey: ["report-tasks"] });
      void queryClient.invalidateQueries({ queryKey: ["report-task", taskId] });
    },
  });

  const handleTaskClick = (id: string) => {
    setSelectedTaskId((prev) => (prev === id ? null : id));
  };
  const { data: dataSources, isLoading: isLoadingDataSources } =
    useDataSources();

  useEffect(() => {
    const st = location.state as ReportsLocationState | undefined;
    const ins = st?.createReportFromChat?.instruction?.trim();
    if (!ins) return;
    setChatInstructionPrefill(ins);
    navigate(`${location.pathname}${location.search}`, {
      replace: true,
      state: {},
    });
  }, [location.state, location.pathname, location.search, navigate]);

  return (
    <div className="flex min-h-0 w-full flex-1 items-stretch gap-4 overflow-hidden bg-background pl-0">
      <div className="flex min-h-0 shrink-0 self-stretch">
        <FigmaAnalyticsSidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen((v) => !v)}
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
          onSelectEntry={(entryId) => {
            const entry = p.entries.find((e) => e.id === entryId);
            const chatId = entry?.conversationId;
            if (!chatId) return;
            void navigate(`/home/${chatId}`);
          }}
          onStartNewChat={() => void navigate("/home")}
          onLoadHistory={() => void p.loadHistory()}
          onClearAllHistory={() => void p.clearAllHistoryEntries()}
          onStartEditingRow={p.startEditingRow}
          onDeleteHistoryEntry={(id) => void p.deleteHistoryEntry(id)}
          t={p.t}
          notifications={inviteNotifications}
          onNotificationAccept={handleInviteModalAccept}
          onNotificationReject={handleInviteModalReject}
        />
      </div>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <section className="relative flex min-h-0 flex-1 flex-col rounded-2xl bg-background overflow-hidden py-4">
          <div className="shrink-0 w-full max-w-[900px] mx-auto px-10 pt-10 pb-4">
            <div className="flex items-center justify-between gap-4">
              {!sidebarOpen && (
                <button
                  type="button"
                  onClick={() => setSidebarOpen(true)}
                  className="absolute top-5 left-5 flex size-10 shrink-0 cursor-pointer items-center justify-center rounded-[24px] transition-all hover:bg-[#27272a]/60 active:scale-[0.97]"
                  aria-label={p.t("home.figma.openSidebar")}
                >
                  <Icon
                    icon="mdi:menu"
                    width={22}
                    className="text-foreground"
                  />
                </button>
              )}
              <h1 className="text-2xl font-semibold text-foreground">
                {p.t("reports.title")}
              </h1>
              <CreateReportModal
                dataSources={dataSources?.items}
                refetch={refetch}
                templatePrefill={templatePrefill}
                onTemplatePrefillConsumed={() => setTemplatePrefill(null)}
                chatInstructionPrefill={chatInstructionPrefill}
                onChatInstructionPrefillConsumed={() =>
                  setChatInstructionPrefill(null)
                }
              />
              {editingTask && (
                <CreateReportModal
                  dataSources={dataSources?.items}
                  refetch={refetch}
                  taskToEdit={editingTask}
                  externalOpen={true}
                  onExternalClose={() => setEditingTask(null)}
                />
              )}
            </div>
          </div>
          <div className="shrink-0 w-full max-w-[900px] mx-auto px-10 pb-6">
            <ReportTemplatesCarousel
              items={templatesData?.items ?? []}
              isLoading={isLoadingTemplates}
              isError={isTemplatesError}
              onSelectTemplate={(tpl) => {
                setChatInstructionPrefill(null);
                setTemplatePrefill(tpl);
              }}
            />
          </div>
          <ScrollShadow className="min-h-0 flex-1" hideScrollBar>
            <div className="w-full max-w-[900px] mx-auto px-10 pb-10">
              {(isLoading || isLoadingDataSources) && (
                <div className="flex items-center justify-center py-16">
                  <Spinner size="lg" />
                </div>
              )}
              {isError && (
                <div className="flex items-center justify-center py-16">
                  <span className="text-sm text-danger">
                    {p.t("reports.loadError")}
                  </span>
                </div>
              )}
              {data && (
                <div className="flex flex-col gap-4">
                  {data.items.map((task) => (
                    <ReportTaskItem
                      key={task.id}
                      id={task.id}
                      title={task.title}
                      schedule={formatSchedule(task)}
                      isActive={task.is_active}
                      description={
                        task.last_report_sentence?.trim() || undefined
                      }
                      lastRunTime={
                        task.last_run_at
                          ? new Date(task.last_run_at).toLocaleString()
                          : undefined
                      }
                      isSelected={selectedTaskId === task.id}
                      onClick={handleTaskClick}
                      onPause={(id) => pauseMutation.mutate(id)}
                      onResume={(id) => resumeMutation.mutate(id)}
                    />
                  ))}
                  {data.items.length === 0 && (
                    <p className="py-16 text-center text-sm text-muted">
                      {p.t("reports.empty")}
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
          selectedTaskId ? "w-[512px]" : "w-0"
        }`}
      >
        <div className="flex h-full w-[512px] flex-col border-l border-border bg-background">
          {selectedTask && (
            <TaskDetailPanel
              task={selectedTask}
              schedule={formatSchedule(selectedTask)}
              onClose={() => setSelectedTaskId(null)}
              onEdit={() => setEditingTask(selectedTask)}
              onTogglePause={() => {
                if (selectedTask.is_active) {
                  pauseMutation.mutate(selectedTask.id);
                } else {
                  resumeMutation.mutate(selectedTask.id);
                }
              }}
              onDelete={() => {
                setSelectedTaskId(null);
                void queryClient.invalidateQueries({
                  queryKey: ["report-tasks"],
                });
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

