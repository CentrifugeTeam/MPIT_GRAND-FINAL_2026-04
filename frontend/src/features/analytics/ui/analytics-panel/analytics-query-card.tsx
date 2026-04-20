import { Button, Card } from "@heroui/react";
import { Icon } from "@iconify/react";

import type { AnalyticsStageKey } from "@/features/analytics/lib/stage-weights";
import type { InterpretationHint } from "@/features/analytics/ui/analytics-panel/interpretation-banner";
import { InterpretationBanner } from "@/features/analytics/ui/analytics-panel/interpretation-banner";
import { ProgressBar } from "@/shared/ui/progress-bar";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type AnalyticsQueryCardProps = {
  t: TFn;
  interpretationHint: InterpretationHint | null;
  hideInterpretationStrip: boolean;
  question: string;
  maxRowsStr: string;
  busy: boolean;
  stageKey: AnalyticsStageKey;
  stageLabel: string;
  progress: number;
  activeId: string | null;
  onQuestionChange: (v: string) => void;
  onMaxRowsChange: (v: string) => void;
  onSubmit: () => void;
  onRerun: () => void;
};

export function AnalyticsQueryCard({
  t,
  interpretationHint,
  hideInterpretationStrip,
  question,
  maxRowsStr,
  busy,
  stageKey,
  stageLabel,
  progress,
  activeId,
  onQuestionChange,
  onMaxRowsChange,
  onSubmit,
  onRerun,
}: AnalyticsQueryCardProps) {
  return (
    <Card className="border border-border bg-surface p-5 shadow-sm">
      <div className="flex flex-col gap-4">
        <label className="text-sm font-medium text-foreground">
          {t("home.analytics.questionLabel")}
        </label>
        {!hideInterpretationStrip && (
          <InterpretationBanner t={t} hint={interpretationHint} variant="compact" />
        )}
        <textarea
          value={question}
          onChange={(e) => onQuestionChange(e.target.value)}
          placeholder={t("home.analytics.placeholder")}
          rows={3}
          disabled={busy}
          className="bg-default border-border text-foreground placeholder:text-muted focus:border-accent w-full resize-y rounded-xl border px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-accent/30"
        />

        <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label className="text-muted mb-1 block text-xs">
              {t("home.analytics.maxRowsLabel")}
            </label>
            <input
              type="text"
              inputMode="numeric"
              value={maxRowsStr}
              onChange={(e) => onMaxRowsChange(e.target.value)}
              placeholder={t("home.analytics.maxRowsPlaceholder")}
              disabled={busy}
              className="bg-default border-border text-foreground placeholder:text-muted focus:border-accent w-full rounded-xl border px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-accent/30"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            className="bg-foreground text-background rounded-full px-6"
            onPress={() => void onSubmit()}
            isDisabled={busy || !question.trim()}
          >
            {busy ? (
              <span className="flex items-center gap-2">
                <Icon icon="mdi:loading" className="animate-spin" width={18} />
                {t("home.analytics.running")}
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Icon icon="mdi:chart-timeline-variant" width={18} />
                {t("home.analytics.submit")}
              </span>
            )}
          </Button>
          {activeId && (
            <Button
              variant="outline"
              className="rounded-full"
              onPress={onRerun}
              isDisabled={busy || !question.trim()}
            >
              <Icon icon="mdi:repeat" className="mr-1" width={18} />
              {t("home.analytics.rerun")}
            </Button>
          )}
          {stageLabel && (
            <span className="text-muted text-sm">{stageLabel}</span>
          )}
        </div>

        {(busy || stageKey !== "idle") && (
          <div className="space-y-1 pt-2">
            <ProgressBar value={progress} />
            <p className="text-muted text-xs">{t(`home.analytics.stage.${stageKey}`)}</p>
          </div>
        )}
      </div>
    </Card>
  );
}
