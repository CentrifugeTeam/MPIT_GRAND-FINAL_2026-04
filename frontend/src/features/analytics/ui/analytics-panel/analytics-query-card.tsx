import { Button, Card } from "@heroui/react";
import { Icon } from "@iconify/react";

import type { InterpretationHint } from "../../lib/interpretation-hint";
import type { NlChatLine } from "../../lib/use-nl-orchestrator-chat";
import { NlChatTranscriptBlock } from "./nl-chat-transcript-block";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type AnalyticsQueryCardProps = {
  t: TFn;
  interpretationHint: InterpretationHint | null;
  hideInterpretationStrip: boolean;
  question: string;
  maxRowsStr: string;
  composerBusy: boolean;
  nlChatLines: NlChatLine[];
  nlChatReady: boolean;
  onQuestionChange: (v: string) => void;
  onMaxRowsChange: (v: string) => void;
  onSend: () => void;
};

export function AnalyticsQueryCard({
  t,
  interpretationHint: _interpretationHint,
  hideInterpretationStrip: _hideInterpretationStrip,
  question,
  maxRowsStr,
  composerBusy,
  nlChatLines,
  nlChatReady,
  onQuestionChange,
  onMaxRowsChange,
  onSend,
}: AnalyticsQueryCardProps) {
  return (
    <Card className="border border-border bg-surface p-5 shadow-sm">
      <div className="flex flex-col gap-4">
        <div>
          <label className="text-sm font-medium text-foreground">
            {t("home.analytics.questionLabel")}
          </label>
          <p className="text-muted mt-1 text-xs leading-relaxed">
            {t("home.analytics.chatIntegratedHint")}
          </p>
        </div>
        {/* Плашка «ясность формулировки» — временно скрыта
        {!hideInterpretationStrip && (
          <InterpretationBanner t={t} hint={interpretationHint} variant="compact" />
        )}
        */}

        <NlChatTranscriptBlock
          t={t}
          nlChatLines={nlChatLines}
          variant="card"
          emptyLabel={t("home.analytics.chatEmpty")}
        />

        <textarea
          value={question}
          onChange={(e) => onQuestionChange(e.target.value)}
          placeholder={t("home.analytics.placeholder")}
          rows={3}
          disabled={composerBusy}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void onSend();
            }
          }}
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
              disabled={composerBusy}
              className="bg-default border-border text-foreground placeholder:text-muted focus:border-accent w-full rounded-xl border px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-accent/30"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            className="bg-foreground text-background rounded-full px-6"
            onPress={() => void onSend()}
            isDisabled={composerBusy || !question.trim() || !nlChatReady}
          >
            {composerBusy ? (
              <span className="flex items-center gap-2">
                <Icon icon="mdi:loading" className="animate-spin" width={18} />
                {t("home.analytics.running")}
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Icon icon="mdi:message-text-outline" width={18} />
                {t("home.analytics.submit")}
              </span>
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
}
