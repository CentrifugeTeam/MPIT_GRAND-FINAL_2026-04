import { Dropdown } from '@heroui/react';
import { Icon } from '@iconify/react';
import { useNavigate } from 'react-router';

import { useAuthStore } from '@/shared/lib/auth-store';
import {
  FIGMA_DROPDOWN_ITEM,
  FIGMA_DROPDOWN_ITEM_DANGER,
  FIGMA_DROPDOWN_MENU,
  FIGMA_DROPDOWN_POPOVER,
} from './figma-heroui-dropdown-classes';
import { FigmaSimpleTooltip } from './figma-simple-tooltip';

type FigmaSidebarProfileButtonProps = {
  isOpen: boolean;
  t: (key: string) => string;
};

export function FigmaSidebarProfileButton({
  isOpen,
  t,
}: FigmaSidebarProfileButtonProps) {
  const clearSession = useAuthStore(s => s.clearSession);
  const navigate = useNavigate();

  const trigger = (
    <Dropdown.Trigger
      aria-label={t('home.figma.profileAria')}
      className='flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-full bg-[#27272a] transition-all duration-200 hover:bg-[#3f3f46] active:scale-[0.97]'
    >
      <Icon icon='mdi:account' className='text-[#a1a1aa]' width={16} />
    </Dropdown.Trigger>
  );

  return (
    <Dropdown.Root placement='top start'>
      {isOpen ? (
        trigger
      ) : (
        <FigmaSimpleTooltip label={t('home.figma.profileAria')} side='right'>
          {trigger}
        </FigmaSimpleTooltip>
      )}

      <Dropdown.Popover
        className={`${FIGMA_DROPDOWN_POPOVER} !min-w-[232px] !rounded-[20px] !shadow-[0px_2px_8px_0px_rgba(0,0,0,0.06),0px_-6px_12px_0px_rgba(0,0,0,0.03),0px_14px_28px_0px_rgba(0,0,0,0.08)]`}
      >
        <Dropdown.Menu className={`${FIGMA_DROPDOWN_MENU} min-w-[216px]`}>
          <Dropdown.Item
            className={FIGMA_DROPDOWN_ITEM}
            textValue={t('home.figma.profileSettings')}
            onAction={() => void navigate('/settings')}
          >
            <span className='flex items-center gap-3'>
              <Icon icon='mdi:cog-outline' width={16} className='shrink-0 text-[#a1a1aa]' />
              {t('home.figma.profileSettings')}
            </span>
          </Dropdown.Item>
          <Dropdown.Item
            className={FIGMA_DROPDOWN_ITEM_DANGER}
            textValue={t('home.figma.profileLogout')}
            onAction={() => {
              clearSession();
              void navigate('/auth/login');
            }}
          >
            <span className='flex items-center gap-3'>
              <Icon
                icon='mdi:logout'
                width={16}
                className='shrink-0'
              />
              {t('home.figma.profileLogout')}
            </span>
          </Dropdown.Item>
        </Dropdown.Menu>
      </Dropdown.Popover>
    </Dropdown.Root>
  );
}
