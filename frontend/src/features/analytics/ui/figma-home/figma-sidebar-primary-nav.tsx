import { Icon } from '@iconify/react';
import { useNavigate } from 'react-router';

import { useAnalyticsChatStore } from '../../model/analytics-chat-store';
import { FIGMA_SIDEBAR_NAV_BUTTON_CLASS } from '../../config/figma-sidebar-styles';
import { FigmaSimpleTooltip } from './figma-simple-tooltip';
import {
  GearIcon,
  NewChatIcon,
  ReportsIcon,
  SearchIcon,
} from '@/shared/ui/assets/icons';

export type FigmaSidebarPrimaryNavProps = {
  isOpen: boolean;
  onOpenSearch: () => void;
  onStartNewChat: () => void;
  t: (key: string) => string;
};

export function FigmaSidebarPrimaryNav({
  isOpen,
  onOpenSearch,
  onStartNewChat,
  t,
}: FigmaSidebarPrimaryNavProps) {
  const navigate = useNavigate();
  const setActive = useAnalyticsChatStore(s => s.setActive);

  const handleNavigateToReports = () => {
    setActive(null);
    void navigate('/reports');
  };

  return (
    <div className='flex w-full flex-col gap-[4px] items-center'>
      {isOpen ? (
        <button
          type='button'
          onClick={onOpenSearch}
          className={`${FIGMA_SIDEBAR_NAV_BUTTON_CLASS} text-left`}
        >
          <div className='flex min-h-[inherit] w-full items-center gap-[12px] px-[12px] py-[6px]'>
            <SearchIcon
              className='shrink-0 text-[#a1a1aa]'
              width={16}
            />
            <span className='min-w-0 flex-1 truncate font-sans text-[14px] font-medium text-[#fcfcfc]'>
              {t('home.figma.search')}
            </span>
            <span className='rounded-lg bg-[#27272a] px-1.5 py-0.5 font-medium text-[12px] text-[#a1a1aa]'>
              {t('home.figma.searchShortcut')}
            </span>
          </div>
        </button>
      ) : (
        <FigmaSimpleTooltip
          label={t('home.figma.search')}
          side='right'
        >
          <button
            type='button'
            onClick={onOpenSearch}
            className={`${FIGMA_SIDEBAR_NAV_BUTTON_CLASS} justify-center p-2`}
          >
            <Icon
              icon='mdi:magnify'
              className='text-[#a1a1aa]'
              width={18}
            />
          </button>
        </FigmaSimpleTooltip>
      )}

      {isOpen ? (
        <button
          type='button'
          onClick={() => {
            navigate('/home');
            void onStartNewChat();
          }}
          className={`${FIGMA_SIDEBAR_NAV_BUTTON_CLASS} text-left`}
        >
          <div className='flex min-h-[inherit] w-full items-center gap-[12px] px-[12px] py-[6px]'>
            <NewChatIcon
              className='shrink-0 text-[#a1a1aa]'
              width={16}
            />
            <span className='min-w-0 flex-1 truncate font-sans text-[14px] font-medium text-[#fcfcfc]'>
              {t('home.figma.newChat')}
            </span>
          </div>
        </button>
      ) : (
        <FigmaSimpleTooltip
          label={t('home.figma.newChatTooltip')}
          side='right'
        >
          <button
            type='button'
            onClick={() => void onStartNewChat()}
            className={`${FIGMA_SIDEBAR_NAV_BUTTON_CLASS} justify-center p-2`}
          >
            <Icon
              icon='mdi:message-plus-outline'
              className='text-[#a1a1aa]'
              width={18}
            />
          </button>
        </FigmaSimpleTooltip>
      )}

      {isOpen ? (
        <button
          type='button'
          onClick={handleNavigateToReports}
          className={`${FIGMA_SIDEBAR_NAV_BUTTON_CLASS} text-left`}
        >
          <div className='flex min-h-[inherit] w-full items-center gap-[12px] px-[12px] py-[6px]'>
            <GearIcon
              className='shrink-0 text-[#a1a1aa]'
              width={16}
              height={16}
            />
            <span className='min-w-0 flex-1 truncate font-sans text-[14px] font-medium text-[#fcfcfc]'>
              {t('home.figma.reports')}
            </span>
          </div>
        </button>
      ) : (
        <FigmaSimpleTooltip
          label={t('home.figma.reports')}
          side='right'
        >
          <span className='inline-flex w-full justify-center'>
            <button
              type='button'
              onClick={handleNavigateToReports}
              className={`${FIGMA_SIDEBAR_NAV_BUTTON_CLASS} justify-center p-2`}
            >
              <Icon
                icon='mdi:file-chart-outline'
                className='text-[#a1a1aa]'
                width={18}
              />
            </button>
          </span>
        </FigmaSimpleTooltip>
      )}
    </div>
  );
}
