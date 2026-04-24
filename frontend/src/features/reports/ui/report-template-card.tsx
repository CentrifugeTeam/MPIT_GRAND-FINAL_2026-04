import { Card } from '@heroui/react';
import { Icon } from '@iconify/react';

export type ReportTemplateCardProps = {
  title: string;
  description: string;
  onPress: () => void;
  'aria-label'?: string;
};

/**
 * Карточка пресета отчёта: 261×144, rounded-3xl, бордер 1px (макет дашборда).
 */
export function ReportTemplateCard({
  title,
  description,
  onPress,
  'aria-label': ariaLabel,
}: ReportTemplateCardProps) {
  return (
    <Card
      role='button'
      tabIndex={0}
      aria-label={ariaLabel ?? title}
      onClick={onPress}
      onKeyDown={e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onPress();
        }
      }}
      className='h-[144px] w-[261px] max-w-[261px] shrink-0 cursor-pointer rounded-3xl border border-zinc-700/90 bg-[#a3a3a3] p-4 shadow-none transition-[transform,box-shadow] hover:brightness-[1.02] hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900/40 active:scale-[0.99]'
    >
      <div className='flex h-full min-h-0 flex-col items-stretch gap-1.5 overflow-hidden text-left'>
        <Icon
          icon='mdi:file-document-outline'
          width={28}
          height={28}
          className='shrink-0 text-white'
          aria-hidden
        />
        <h3 className='line-clamp-2 text-sm font-semibold leading-snug text-white'>
          {title}
        </h3>
        {description ? (
          <p className='line-clamp-2 text-xs leading-snug text-zinc-800/90'>
            {description}
          </p>
        ) : null}
      </div>
    </Card>
  );
}
