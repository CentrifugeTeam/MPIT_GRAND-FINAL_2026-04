import {
  memo,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import { Button, Card, Disclosure } from '@heroui/react';
import { motion } from 'motion/react';
import { Virtuoso } from 'react-virtuoso';

import { downloadQueue } from '@/shared/lib/download-queue';

import { Logo } from '@/shared/ui/atoms/logo';

import type { NlChatLine } from '../../lib/use-nl-orchestrator-chat';

import { ANALYTICS_TABLE_PREVIEW_MAX } from '../../config/constants';
import {
  nlChatHasSeriesChart,
  nlChatHasTablePreview,
} from '../../lib/nl-chat-viz';
import { AnalyticsCharts } from '../analytics-charts';
import { FigmaSimpleTooltip } from '../figma-home/figma-simple-tooltip';
import { DataTablePreview } from '@/shared/ui/organisms/data-table-preview';
import {
  ArrowDownToSquare,
  ArrowRotateRight,
  ClockArrowRotateLeftIcon,
  CopyIcon,
} from '@/shared/ui/assets/icons';

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type TranscriptVariant = 'card' | 'figma' | 'grok';

export type NlChatAssistantActionHandlers = {
  onRetry: (payload: {
    assistantLineId: string;
    userMessage: string;
    userLineId: string | null;
  }) => void | Promise<void>;
  onCreateReportTask: (userQuestion: string) => void | Promise<void>;
  onNewChat: () => void;
};

function precedingUserForRetry(
  lines: NlChatLine[],
  assistantIndex: number,
): { text: string; lineId: string } | null {
  for (let i = assistantIndex - 1; i >= 0; i--) {
    if (lines[i]!.role === 'user') {
      return { text: lines[i]!.text, lineId: lines[i]!.id };
    }
  }
  return null;
}

const bubbleCard = {
  user: 'ml-4 rounded-xl border border-border/60 bg-primary/10 px-3 py-2.5 text-sm',
  assistant: 'mr-4 border-l-2 border-border pl-3 pr-1 py-2 text-sm',
  system: 'text-muted border-l border-dashed border-border/70 pl-3 text-xs',
};

const bubbleFigma = {
  user: 'ml-2 rounded-xl border border-[#28282c] bg-[#27272a]/80 px-3 py-2.5 text-sm text-[#fcfcfc]',
  assistant:
    'mr-2 border-l-2 border-[#3f3f46] pl-3 pr-1 py-2 text-sm text-[#fcfcfc]',
  system: 'text-[#a1a1aa] border-l border-dashed border-[#28282c] pl-3 text-xs',
};

const bubbleGrok = {
  user: 'ml-auto w-fit max-w-[min(85%,520px)] min-w-0 rounded-[22px] bg-[#27272a] px-4 py-3 text-left font-sans text-[15px] font-normal leading-relaxed text-[#fafafa] break-words',
  assistant:
    'w-full max-w-[min(720px,100%)] font-sans text-[15px] font-normal leading-relaxed text-[#e4e4e7]',
  system:
    'mx-auto max-w-[min(560px,100%)] text-center font-sans text-xs leading-snug text-[#71717a]',
};

const iconMotionTransition = {
  type: 'spring' as const,
  stiffness: 420,
  damping: 28,
};

// ---------------------------------------------------------------------------
// Thinking accordion — показывается вместо reasoning-блока в grok-варианте.
//
// Состояния:
//   1. answerPending && !reasoning  → только пульсирующий орб (Logo)
//   2. reasoning существует         → орб + «Думаю...» + аккордеон (collapsed)
// ---------------------------------------------------------------------------
function GrokThinkingBlock({
  t,
  reasoning,
  answerPending,
}: {
  t: TFn;
  reasoning: string | null | undefined;
  answerPending: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasReasoning = Boolean(reasoning?.trim());

  if (!hasReasoning && answerPending) {
    return (
      <div className='mb-4'>
        <Logo
          compact
          pulsing
        />
      </div>
    );
  }

  if (!hasReasoning) return null;

  return (
    <div className='mb-4'>
      <Disclosure
        isExpanded={isExpanded}
        onExpandedChange={setIsExpanded}
      >
        <Disclosure.Heading>
          <div className='flex gap-1 items-center'>
            <Logo
              compact
              pulsing={answerPending}
            />
            <Button
              slot='trigger'
              variant='ghost'
              className='flex h-auto min-w-0 items-center gap-2 rounded-xl px-2 py-1.5 data-[hover=true]:bg-[#27272a]/60'
            >
              <span className='text-sm font-medium text-[#a1a1aa]'>
                {t('home.analytics.chatThinking')}
              </span>
              <Disclosure.Indicator className='text-[#71717a]' />
            </Button>
          </div>
        </Disclosure.Heading>
        <Disclosure.Content>
          <Disclosure.Body className='mt-2 border-l border-[#28282c] py-2.5 px-2.5'>
            <pre className='whitespace-pre-wrap font-sans text-xs leading-snug text-[#A1A1AA]'>
              {reasoning}
            </pre>
          </Disclosure.Body>
        </Disclosure.Content>
      </Disclosure>
    </div>
  );
}

function GrokAssistantToolbar({
  t,
  plain,
  userCtx,
  assistantLineId,
  handlers,
  actionsLocked,
}: {
  t: TFn;
  plain: string;
  userCtx: { text: string; lineId: string } | null;
  assistantLineId: string;
  handlers: NlChatAssistantActionHandlers;
  actionsLocked: boolean;
}) {
  const [copyFlash, setCopyFlash] = useState(false);

  useEffect(() => {
    if (!copyFlash) return;
    const id = window.setTimeout(() => setCopyFlash(false), 1800);
    return () => window.clearTimeout(id);
  }, [copyFlash]);

  const handleCopy = useCallback(async () => {
    if (actionsLocked || !plain) return;
    try {
      await navigator.clipboard.writeText(plain);
      setCopyFlash(true);
    } catch {
      /* ignore */
    }
  }, [actionsLocked, plain]);

  const lockHint = t('home.analytics.chatActionsLocked');
  const copyTooltipLabel = actionsLocked
    ? lockHint
    : copyFlash
      ? t('home.analytics.chatCopied')
      : t('home.analytics.chatActionCopy');

  const iconWrap =
    'inline-flex size-9 shrink-0 cursor-pointer items-center justify-center rounded-xl text-[#71717a] transition-colors hover:bg-[#27272a]/80 hover:text-[#e4e4e7]';
  const iconWrapDisabled = 'pointer-events-none cursor-not-allowed opacity-40';

  return (
    <div className='mt-3 flex flex-wrap items-center gap-0.5 mx-2.5'>
      {userCtx?.text?.trim() ? (
        <FigmaSimpleTooltip
          label={actionsLocked ? lockHint : t('home.analytics.chatActionRetry')}
          side='top'
        >
          <motion.span
            className='inline-flex'
            whileHover={actionsLocked ? undefined : { scale: 1.06 }}
            whileTap={actionsLocked ? undefined : { scale: 0.94 }}
            transition={iconMotionTransition}
          >
            <button
              type='button'
              className={`${iconWrap} ${actionsLocked ? iconWrapDisabled : ''}`}
              aria-label={t('home.analytics.chatActionRetry')}
              aria-disabled={actionsLocked}
              disabled={actionsLocked}
              onClick={() =>
                void handlers.onRetry({
                  assistantLineId,
                  userMessage: userCtx.text.trim(),
                  userLineId: userCtx.lineId,
                })
              }
            >
              <ArrowRotateRight
                width={18}
                height={18}
              />
            </button>
          </motion.span>
        </FigmaSimpleTooltip>
      ) : null}
      {plain ? (
        <FigmaSimpleTooltip
          label={copyTooltipLabel}
          side='top'
        >
          <motion.span
            className='inline-flex'
            whileHover={actionsLocked ? undefined : { scale: 1.06 }}
            whileTap={actionsLocked ? undefined : { scale: 0.94 }}
            transition={iconMotionTransition}
          >
            <button
              type='button'
              className={`${iconWrap} ${actionsLocked ? iconWrapDisabled : ''}`}
              aria-label={copyTooltipLabel}
              aria-disabled={actionsLocked}
              disabled={actionsLocked}
              onClick={() => void handleCopy()}
            >
              <CopyIcon
                width={18}
                height={18}
              />
            </button>
          </motion.span>
        </FigmaSimpleTooltip>
      ) : null}
      {userCtx?.text?.trim() ? (
        <FigmaSimpleTooltip
          label={actionsLocked ? lockHint : t('home.analytics.download')}
          side='top'
        >
          <motion.span
            className='inline-flex'
            whileHover={actionsLocked ? undefined : { scale: 1.06 }}
            whileTap={actionsLocked ? undefined : { scale: 0.94 }}
            transition={iconMotionTransition}
          >
            <button
              type='button'
              className={`${iconWrap} ${actionsLocked ? iconWrapDisabled : ''}`}
              aria-label={t('home.analytics.download')}
              aria-disabled={actionsLocked}
              disabled={actionsLocked}
              onClick={async () => {
                downloadQueue.add(
                  {
                    title: t('home.analytics.downloadToastLoading'),
                    indicator: (
                      <ArrowDownToSquare
                        height={16}
                        width={16}
                      />
                    ),
                  },
                  { timeout: 2000 },
                );
              }}
            >
              <ArrowDownToSquare
                width={16}
                height={16}
              />
            </button>
          </motion.span>
        </FigmaSimpleTooltip>
      ) : null}
      {userCtx?.text?.trim() ? (
        <FigmaSimpleTooltip
          label={t('home.analytics.chatActionCreateTask')}
          side='top'
        >
          <motion.span
            className='inline-flex'
            whileHover={actionsLocked ? undefined : { scale: 1.06 }}
            whileTap={actionsLocked ? undefined : { scale: 0.94 }}
            transition={iconMotionTransition}
          >
            <button
              type='button'
              className={`${iconWrap} ${actionsLocked ? iconWrapDisabled : ''}`}
              aria-label={t('home.analytics.chatActionCreateTask')}
              aria-disabled={actionsLocked}
              disabled={actionsLocked}
              onClick={() =>
                void handlers.onCreateReportTask(userCtx.text.trim())
              }
            >
              <ClockArrowRotateLeftIcon
                width={16}
                height={16}
              />
            </button>
          </motion.span>
        </FigmaSimpleTooltip>
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Мемоизированный компонент одного сообщения.
//
// React.memo гарантирует, что при стриминге перерисовывается ТОЛЬКО последний
// элемент (у него изменился объект `line`), а не все видимые сообщения.
//
// userCtxText / userCtxLineId передаются как примитивы (строки), чтобы
// React.memo мог корректно сравнить их (объект { text, lineId } был бы новым
// при каждом вызове itemContent, ломая мемоизацию).
// ---------------------------------------------------------------------------
type BubbleStyles = typeof bubbleCard;

type ChatMessageBubbleProps = {
  line: NlChatLine;
  variant: TranscriptVariant;
  b: BubbleStyles;
  labelMuted: string;
  preClass: string;
  sqlBox: string;
  innerCard: string;
  itemGap: string;
  reasoningBox: string;
  reasoningPre: string;
  reasoningLabel: string;
  showRoleLabels: boolean;
  showAssistantToolbar: boolean;
  assistantActionHandlers: NlChatAssistantActionHandlers | null | undefined;
  assistantActionsLocked: boolean;
  t: TFn;
  /** Примитивы для toolbar: стабильны для завершённых сообщений → memo работает */
  userCtxText: string | null;
  userCtxLineId: string | null;
};

const ChatMessageBubble = memo(function ChatMessageBubble({
  line: l,
  variant,
  b,
  labelMuted,
  preClass,
  sqlBox,
  innerCard,
  itemGap,
  reasoningBox,
  reasoningPre,
  reasoningLabel,
  showRoleLabels,
  showAssistantToolbar,
  assistantActionHandlers,
  assistantActionsLocked,
  t,
  userCtxText,
  userCtxLineId,
}: ChatMessageBubbleProps) {
  const userCtx =
    userCtxText && userCtxLineId
      ? { text: userCtxText, lineId: userCtxLineId }
      : null;

  return (
    <div className={itemGap}>
      <div
        className={
          l.role === 'user'
            ? b.user
            : l.role === 'assistant'
              ? b.assistant
              : b.system
        }
      >
        {showRoleLabels && l.role !== 'system' && (
          <span className={`mb-1 block ${labelMuted}`}>
            {l.role === 'user'
              ? t('home.analytics.chatRoleUser')
              : t('home.analytics.chatRoleAssistant')}
          </span>
        )}
        {(l.role === 'assistant' || l.role === 'system') &&
          (l.reasoning || l.answerPending) &&
          (variant === 'grok' ? (
            <GrokThinkingBlock
              t={t}
              reasoning={l.reasoning}
              answerPending={l.answerPending ?? false}
            />
          ) : (
            <div className={reasoningBox}>
              <span className={reasoningLabel}>
                {t('home.analytics.chatReasoningLabel')}
              </span>
              <pre className={reasoningPre}>
                {l.reasoning ||
                  (l.answerPending
                    ? t('home.analytics.chatReasoningLoading')
                    : '')}
              </pre>
            </div>
          ))}
        <pre className={preClass}>
          {l.answerPending && !l.text.trim()
            ? t('home.analytics.chatAnswerComposing')
            : l.text}
        </pre>
        {l.sql && <pre className={sqlBox}>{l.sql}</pre>}
        {l.role === 'assistant' &&
          l.chartPayload &&
          nlChatHasSeriesChart(l.chartPayload) && (
            <Card className={innerCard}>
              <h4 className={labelMuted + ' mb-3'}>
                {t('home.analytics.chartTitle')}
              </h4>
              <AnalyticsCharts payload={l.chartPayload} />
            </Card>
          )}
        {l.role === 'assistant' && nlChatHasTablePreview(l.columns, l.rows) && (
          <Card className={innerCard}>
            <h4 className={labelMuted + ' mb-3'}>
              {t('home.analytics.tableTitle')}
            </h4>
            <DataTablePreview
              columns={l.columns ?? []}
              rows={l.rows ?? []}
              emptyLabel={t('home.analytics.tableEmpty')}
              truncatedHint={t('home.analytics.tableTruncated', {
                max: ANALYTICS_TABLE_PREVIEW_MAX,
                total: l.rows?.length ?? 0,
              })}
              maxPreviewRows={ANALYTICS_TABLE_PREVIEW_MAX}
            />
            <p
              className={
                variant === 'figma' || variant === 'grok'
                  ? 'mt-2 text-xs text-[#a1a1aa]'
                  : 'text-muted mt-2 text-xs'
              }
            >
              {t('home.analytics.rowCount', {
                count: l.rowCount ?? l.rows?.length ?? 0,
              })}
            </p>
          </Card>
        )}
        {showAssistantToolbar &&
          l.role === 'assistant' &&
          !l.answerPending &&
          assistantActionHandlers && (
            <GrokAssistantToolbar
              t={t}
              plain={l.text.trim()}
              userCtx={userCtx}
              assistantLineId={l.id}
              handlers={assistantActionHandlers}
              actionsLocked={assistantActionsLocked}
            />
          )}
      </div>
    </div>
  );
});

// ---------------------------------------------------------------------------

export function NlChatTranscriptBlock({
  t,
  nlChatLines,
  variant,
  emptyLabel,
  assistantActionHandlers,
  assistantActionsLocked = false,
  scrollerEl,
}: {
  t: TFn;
  nlChatLines: NlChatLine[];
  variant: TranscriptVariant;
  emptyLabel: string;
  assistantActionHandlers?: NlChatAssistantActionHandlers | null;
  assistantActionsLocked?: boolean;
  /** Внешний scroll-контейнер — передаётся для варианта grok из родителя. */
  scrollerEl?: HTMLElement | null;
}) {
  const b =
    variant === 'grok'
      ? bubbleGrok
      : variant === 'figma'
        ? bubbleFigma
        : bubbleCard;
  const labelMuted =
    variant === 'figma' || variant === 'grok'
      ? 'text-[#71717a] text-xs font-medium uppercase tracking-wide'
      : 'text-muted text-xs font-medium uppercase tracking-wide';
  const preClass =
    variant === 'figma' || variant === 'grok'
      ? 'whitespace-pre-wrap font-sans text-[inherit] px-2.5'
      : 'whitespace-pre-wrap font-sans text-foreground px-2.5';
  const sqlBox =
    variant === 'figma' || variant === 'grok'
      ? 'mt-3 overflow-x-auto rounded-xl border border-[#28282c] bg-[#0c0c0e] p-3 font-mono text-[12px] leading-snug text-[#d4d4d8] mx-2.5'
      : 'mt-2 overflow-x-auto rounded-lg bg-black/5 p-2 text-xs text-foreground mx-2.5';
  const innerCard =
    variant === 'figma' || variant === 'grok'
      ? 'mt-4 rounded-2xl border border-[#28282c] bg-[#09090b] p-4 shadow-none mx-2.5'
      : 'border-border mt-3 border border-border/80 bg-surface/80 p-4 shadow-none mx-2.5';

  const wrapClass =
    variant === 'grok'
      ? 'w-full px-1 py-1'
      : variant === 'figma'
        ? 'max-h-[min(420px,45vh)] overflow-y-auto rounded-xl border border-[#28282c] bg-[#060607]/40 p-3'
        : 'max-h-72 overflow-y-auto rounded-xl border border-border bg-default/25 p-3';

  const reasoningBox =
    variant === 'grok' || variant === 'figma'
      ? 'mb-2 rounded-lg border border-[#3f3f46]/60 bg-[#18181b]/80 px-2.5 py-2'
      : 'bg-muted/30 border-border/60 mb-2 rounded-lg border px-2.5 py-2';
  const reasoningPre =
    variant === 'grok' || variant === 'figma'
      ? 'whitespace-pre-wrap font-sans text-[12px] leading-snug text-[#a1a1aa]'
      : 'text-muted whitespace-pre-wrap font-sans text-xs leading-snug';
  const reasoningLabel =
    variant === 'grok' || variant === 'figma'
      ? 'mb-1 block text-[10px] font-medium uppercase tracking-wide text-[#71717a]'
      : 'text-muted mb-1 block text-[10px] font-medium uppercase tracking-wide';

  const showRoleLabels = variant !== 'grok';
  const showAssistantToolbar =
    variant === 'grok' && assistantActionHandlers != null;

  const itemGap = variant === 'grok' ? 'pb-8' : 'pb-3';

  /** В grok-чате системные строки (очередь SQL, ошибки транспорта) не показываем. */
  const virtuosoLines = useMemo(
    () =>
      variant === 'grok'
        ? nlChatLines.filter((l) => l.role !== 'system')
        : nlChatLines,
    [variant, nlChatLines],
  );

  // Ref для ленты Virtuoso — itemContent читает его вместо захвата через closure.
  // Обновляется синхронно ПОСЛЕ рендера (useLayoutEffect), до того, как Virtuoso
  // вызовет itemContent. Это позволяет убрать nlChatLines из dep-массива
  // useCallback и сохранить стабильную ссылку на функцию между стриминг-чанками.
  const nlChatLinesRef = useRef<NlChatLine[]>(virtuosoLines);
  useLayoutEffect(() => {
    nlChatLinesRef.current = virtuosoLines;
  });

  // Для card/figma: захватываем обёртку div как scroll-контейнер
  const [containerEl, setContainerEl] = useState<HTMLElement | null>(null);
  const captureRef = useCallback((el: HTMLElement | null) => {
    setContainerEl(el);
  }, []);

  const customScrollParent =
    variant === 'grok' ? (scrollerEl ?? undefined) : (containerEl ?? undefined);

  // itemContent стабилен между стриминг-обновлениями: nlChatLines читается
  // через ref, а не через closure. Virtuoso вызывает itemContent вне
  // render-фазы — к этому моменту useLayoutEffect уже обновил ref.
  const itemContent = useCallback(
    (index: number) => {
      const lines = nlChatLinesRef.current;
      const l = lines[index]!;
      // Вычисляем userCtx здесь (не в render ChatMessageBubble), передаём
      // как примитивы, чтобы React.memo корректно сравнивал пропсы.
      const rawUserCtx =
        showAssistantToolbar && l.role === 'assistant' && !l.answerPending
          ? precedingUserForRetry(lines, index)
          : null;
      return (
        <ChatMessageBubble
          key={l.id}
          line={l}
          variant={variant}
          b={b}
          labelMuted={labelMuted}
          preClass={preClass}
          sqlBox={sqlBox}
          innerCard={innerCard}
          itemGap={itemGap}
          reasoningBox={reasoningBox}
          reasoningPre={reasoningPre}
          reasoningLabel={reasoningLabel}
          showRoleLabels={showRoleLabels}
          showAssistantToolbar={showAssistantToolbar}
          assistantActionHandlers={assistantActionHandlers}
          assistantActionsLocked={assistantActionsLocked}
          t={t}
          userCtxText={rawUserCtx?.text ?? null}
          userCtxLineId={rawUserCtx?.lineId ?? null}
        />
      );
    },
    [
      variant,
      b,
      labelMuted,
      preClass,
      sqlBox,
      innerCard,
      itemGap,
      showRoleLabels,
      showAssistantToolbar,
      reasoningBox,
      reasoningPre,
      reasoningLabel,
      assistantActionHandlers,
      assistantActionsLocked,
      t,
    ],
  );

  const initialIndex =
    virtuosoLines.length > 0 ? virtuosoLines.length - 1 : 0;

  if (variant === 'grok') {
    return (
      <div className={wrapClass}>
        {virtuosoLines.length === 0 && (
          <p className='text-sm text-[#a1a1aa]'>{emptyLabel}</p>
        )}
        {virtuosoLines.length > 0 && (
          <Virtuoso
            customScrollParent={customScrollParent}
            data={virtuosoLines}
            followOutput='auto'
            initialTopMostItemIndex={initialIndex}
            itemContent={itemContent}
            overscan={200}
          />
        )}
      </div>
    );
  }

  return (
    <div
      ref={captureRef}
      className={wrapClass}
    >
      {nlChatLines.length === 0 && (
        <p
          className={
            variant === 'figma'
              ? 'text-sm text-[#a1a1aa]'
              : 'text-muted text-sm'
          }
        >
          {emptyLabel}
        </p>
      )}
      {nlChatLines.length > 0 && containerEl && (
        <Virtuoso
          customScrollParent={containerEl}
          data={nlChatLines}
          followOutput='auto'
          initialTopMostItemIndex={initialIndex}
          itemContent={itemContent}
          overscan={200}
        />
      )}
    </div>
  );
}
