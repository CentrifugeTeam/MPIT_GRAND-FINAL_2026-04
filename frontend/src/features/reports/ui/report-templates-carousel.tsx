import { useTranslation } from 'react-i18next';
import { ScrollShadow, Spinner } from '@heroui/react';

import type { ReportTaskTemplate } from '@/features/analytics/api/analytics-api';
import { ReportTemplateCard } from './report-template-card';

function trimInstruction(text: string, maxLen = 120): string {
  const t = text.trim().replace(/\s+/g, ' ');
  if (t.length <= maxLen) return t;
  return `${t.slice(0, maxLen - 1)}…`;
}

export type ReportTemplatesCarouselProps = {
  items: ReportTaskTemplate[];
  isLoading: boolean;
  isError: boolean;
  onSelectTemplate: (template: ReportTaskTemplate) => void;
};

export function ReportTemplatesCarousel({
  items,
  isLoading,
  isError,
  onSelectTemplate,
}: ReportTemplatesCarouselProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div
        className='flex min-h-[144px] items-center justify-start py-2'
        aria-busy
        aria-label={t('reports.templatesLoading')}
      >
        <Spinner size='sm' />
      </div>
    );
  }

  if (isError || items.length === 0) {
    return null;
  }

  return (
    <ScrollShadow
      orientation='horizontal'
      hideScrollBar
      className='w-full min-w-0 pb-1'
      role='list'
      aria-label={t('reports.templatesCarouselAria')}
    >
      <div
        className='flex gap-3'
        style={{ scrollSnapType: 'x mandatory' }}
      >
        {items.map(template => (
          <div
            key={template.id}
            className='shrink-0'
            style={{ scrollSnapAlign: 'start' }}
            role='listitem'
          >
            <ReportTemplateCard
              title={template.title}
              description={trimInstruction(template.instruction)}
              onPress={() => onSelectTemplate(template)}
              aria-label={t('reports.templateUsePreset', {
                title: template.title,
              })}
            />
          </div>
        ))}
      </div>
    </ScrollShadow>
  );
}
