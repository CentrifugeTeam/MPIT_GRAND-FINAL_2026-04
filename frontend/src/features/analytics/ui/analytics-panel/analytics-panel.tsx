import { AnalyticsQueryCard } from "./analytics-query-card";
import { AnalyticsResults } from "./analytics-results";
import { AnalyticsSidebar } from "./analytics-sidebar";
import { useAnalyticsPanel } from "./use-analytics-panel";

export function AnalyticsPanel() {
  const p = useAnalyticsPanel();

  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
      <AnalyticsSidebar
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
        onSelectEntry={p.selectEntry}
        onStartNewChat={p.startNewChat}
        onLoadHistory={() => void p.loadHistory()}
        onConfirmDeleteAll={p.confirmDeleteAll}
        onStartEditingRow={p.startEditingRow}
        onConfirmDeleteOne={p.confirmDeleteOne}
        t={p.t}
      />

      <div className="min-w-0 flex-1 space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {p.t("home.analytics.title")}
          </h1>
          <p className="mt-1 text-sm text-muted">{p.t("home.analytics.subtitle")}</p>
        </div>

        <AnalyticsQueryCard
          t={p.t}
          interpretationHint={p.interpretationHint}
          hideInterpretationStrip={!!p.result}
          question={p.question}
          maxRowsStr={p.maxRowsStr}
          busy={p.busy}
          stageKey={p.stageKey}
          stageLabel={p.stageLabel}
          progress={p.progress}
          activeId={p.activeId}
          onQuestionChange={p.setQuestion}
          onMaxRowsChange={p.setMaxRowsStr}
          onSubmit={p.run}
          onRerun={p.rerun}
        />

        {p.result && (
          <AnalyticsResults
            t={p.t}
            result={p.result}
            showChart={p.showChart}
            chartPayload={p.chartPayload}
            interpretationFallback={p.interpretationHint}
          />
        )}
      </div>
    </div>
  );
}
