import { useEffect } from 'react';
import { motion } from 'motion/react';
import { Card, ListBox, Select } from '@heroui/react';
import { useTranslation } from 'react-i18next';

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type FigmaSettingsModalProps = {
  t: TFn;
  onClose: () => void;
};

export function FigmaSettingsModal({ t, onClose }: FigmaSettingsModalProps) {
  const { i18n } = useTranslation();

  const langKey = i18n.language?.toLowerCase().startsWith('ru') ? 'ru' : 'en';

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <motion.div
      className='fixed inset-0 z-[100] flex items-start justify-center pt-[12vh]'
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      <motion.div
        className='absolute inset-0'
        style={{
          background: 'rgba(0,0,0,0.5)',
          backdropFilter: 'blur(4px)',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.25 }}
        onClick={onClose}
      />

      <motion.div
        className='relative z-10 w-full max-w-lg overflow-hidden rounded-3xl border border-border bg-background'
        initial={{ opacity: 0, scale: 1.05, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
      >
        <button
          type='button'
          onClick={onClose}
          className='absolute right-4 top-4 z-10 flex size-8 cursor-pointer items-center justify-center rounded-3xl bg-surface transition-colors hover:bg-surface-secondary active:scale-[0.97]'
          aria-label={t('common.close')}
        >
          <svg
            width='10'
            height='10'
            viewBox='0 0 10 10'
            fill='none'
          >
            <path
              d='M1 1l8 8M9 1L1 9'
              stroke='currentColor'
              strokeWidth='1.5'
              strokeLinecap='round'
              className='text-muted'
            />
          </svg>
        </button>

        <div className='border-b border-border px-5 pb-4 pr-14 pt-5'>
          <h2 className='text-lg font-semibold text-foreground'>
            {t('settings.title')}
          </h2>
        </div>

        <div className='max-h-[min(60vh,480px)] space-y-4 overflow-y-auto px-5 py-4'>
          <Card className='p-4'>
            <div className='flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'>
              <div className='flex min-w-0 items-center gap-3'>
                <span className='text-xl'>🌐</span>
                <div className='min-w-0'>
                  <Card.Title>{t('settings.language')}</Card.Title>
                  <Card.Description>
                    {langKey === 'ru'
                      ? t('settings.languageRu')
                      : t('settings.languageEn')}
                  </Card.Description>
                </div>
              </div>
              <Select
                aria-label={t('settings.language')}
                className='w-full sm:w-40'
                selectedKey={langKey}
                onSelectionChange={k => void i18n.changeLanguage(String(k))}
              >
                <Select.Trigger className='h-9 w-full rounded-xl border-0 bg-zinc-900 px-3 ring-0 outline-none focus:ring-0 focus:outline-none sm:w-40'>
                  <Select.Value className='text-sm text-foreground' />
                  <Select.Indicator />
                </Select.Trigger>
                <Select.Popover>
                  <ListBox>
                    <ListBox.Item
                      id='ru'
                      textValue={t('settings.languageRu')}
                    >
                      {t('settings.languageRu')}
                      <ListBox.ItemIndicator />
                    </ListBox.Item>
                    <ListBox.Item
                      id='en'
                      textValue={t('settings.languageEn')}
                    >
                      {t('settings.languageEn')}
                      <ListBox.ItemIndicator />
                    </ListBox.Item>
                  </ListBox>
                </Select.Popover>
              </Select>
            </div>
          </Card>
        </div>
      </motion.div>
    </motion.div>
  );
}
