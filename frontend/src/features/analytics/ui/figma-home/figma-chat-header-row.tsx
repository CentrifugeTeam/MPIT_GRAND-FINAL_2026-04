import { Dropdown } from '@heroui/react';
import { Icon } from '@iconify/react';

import type { FigmaTranslateFn } from '../../config/figma-analytics-faq';
import {
  FIGMA_DROPDOWN_ITEM,
  FIGMA_DROPDOWN_MENU,
  FIGMA_DROPDOWN_POPOVER,
} from './figma-heroui-dropdown-classes';
import { FigmaSimpleTooltip } from './figma-simple-tooltip';
import { DotsVertical } from '@/shared/ui/assets/icons';

export type FigmaChatHeaderRowProps = {
  t: FigmaTranslateFn;
  nlConversationId: string | null;
  nlChatAccessRole?: 'owner' | 'viewer' | null;
  onShareChat: () => void;
  historyBusy: boolean;
  onRefreshHistory: () => void;
  onStartNewChat: () => void;
};

export function FigmaChatHeaderRow({
  t,
  nlConversationId,
  nlChatAccessRole = 'owner',
  onShareChat,
  historyBusy,
  onRefreshHistory,
  onStartNewChat,
}: FigmaChatHeaderRowProps) {
  const isViewer = nlChatAccessRole === 'viewer';

  return (
    <div className='absolute right-5 top-5 flex items-center gap-1.5 z-50'>
      {!isViewer ? (
        <FigmaSimpleTooltip
          label={
            nlConversationId
              ? t('home.figma.shareTooltip')
              : t('home.figma.shareDisabledTooltip')
          }
          side='bottom'
        >
          <span className='inline-flex shrink-0'>
            <button
              type='button'
              disabled={!nlConversationId}
              onClick={() => void onShareChat()}
              className='relative flex size-10 cursor-pointer items-center justify-center rounded-[24px] transition-all hover:bg-[#27272a]/40 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40'
            >
              <Icon
                icon='mdi:share-variant-outline'
                className='text-[#fcfcfc]'
                width={20}
              />
              <span
                aria-hidden='true'
                className='pointer-events-none absolute inset-0 rounded-[24px] border border-solid border-[#28282c]'
              />
            </button>
          </span>
        </FigmaSimpleTooltip>
      ) : null}
      <Dropdown.Root>
        <FigmaSimpleTooltip
          label={t('home.figma.chatMenuTooltip')}
          side='bottom'
        >
          <Dropdown.Trigger
            aria-label={t('home.figma.chatMenuAria')}
            className='relative inline-flex size-10 shrink-0 cursor-pointer items-center justify-center rounded-[24px] transition-all hover:bg-[#27272a]/40 active:scale-[0.97]'
          >
            <DotsVertical
              className='text-[#fcfcfc]'
              width={14}
              height={14}
            />
            <span
              aria-hidden='true'
              className='pointer-events-none absolute inset-0 rounded-[24px] border border-solid border-[#28282c]'
            />
          </Dropdown.Trigger>
        </FigmaSimpleTooltip>
        <Dropdown.Popover
          placement='bottom end'
          className={FIGMA_DROPDOWN_POPOVER}
        >
          <Dropdown.Menu className={FIGMA_DROPDOWN_MENU}>
            <Dropdown.Item
              className={FIGMA_DROPDOWN_ITEM}
              textValue={t('home.figma.newChat')}
              onAction={() => void onStartNewChat()}
            >
              <span className='flex items-center gap-2'>
                <Icon
                  icon='mdi:message-plus-outline'
                  width={18}
                />
                {t('home.figma.newChat')}
              </span>
            </Dropdown.Item>
            <Dropdown.Item
              className={FIGMA_DROPDOWN_ITEM}
              textValue={t('home.analytics.refreshHistory')}
              onAction={() => {
                if (!historyBusy) onRefreshHistory();
              }}
            >
              <span className='flex items-center gap-2'>
                <Icon
                  icon={historyBusy ? 'mdi:loading' : 'mdi:refresh'}
                  className={historyBusy ? 'animate-spin' : undefined}
                  width={18}
                />
                {historyBusy
                  ? t('home.analytics.historyLoading')
                  : t('home.analytics.refreshHistory')}
              </span>
            </Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown.Popover>
      </Dropdown.Root>
    </div>
  );
}
