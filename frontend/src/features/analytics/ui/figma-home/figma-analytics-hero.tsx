import type { FigmaTranslateFn } from '../../config/figma-analytics-faq';
import { FIGMA_HERO_COPY_MAX_PX } from './figma-tokens';
import { Logo } from '@/shared/ui/assets/icons';

export function FigmaAnalyticsHero({ t }: { t: FigmaTranslateFn }) {
  return (
    <div className='flex w-full flex-col items-center gap-10'>
      <div className='flex flex-col items-center gap-6 text-center'>
        <Logo
          width={64}
          height={64}
        />
        <div
          className='flex flex-col gap-2'
          style={{ maxWidth: FIGMA_HERO_COPY_MAX_PX }}
        >
          <h1 className='font-sans text-[30px] font-medium leading-9 text-[#fcfcfc]'>
            {t('home.figma.heroTitle')}
          </h1>
          <p className='font-sans text-[18px] leading-7 text-[#a1a1aa]'>
            {t('home.figma.heroSubtitle')}
          </p>
        </div>
      </div>
    </div>
  );
}
