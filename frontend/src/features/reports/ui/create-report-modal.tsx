import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Button,
  DateField,
  Input,
  Label,
  Modal,
  Tabs,
  TextArea,
  TimeField,
} from '@heroui/react';
import { Icon } from '@iconify/react';

export function CreateReportModal() {
  const { t } = useTranslation();
  const [reportName, setReportName] = useState('');
  const [query, setQuery] = useState('');

  return (
    <Modal>
      <Button
        variant='outline'
        radius='full'
      >
        <Icon
          icon='mdi:plus'
          width={16}
          className='mr-1'
        />
        {t('reports.addReport')}
      </Button>
      <Modal.Backdrop>
        <Modal.Container>
          <Modal.Dialog className='w-full max-w-xl rounded-3xl border border-zinc-800 bg-zinc-950 p-0 gap-0 shadow-none'>
            <div className='flex flex-col gap-4 px-[17px] pb-[17px] pt-[9px]'>
              {/* Title row */}
              <div className='flex items-center gap-2 pl-1'>
                <Input
                  value={reportName}
                  onChange={e => setReportName(e.target.value)}
                  placeholder={t('reports.modal.titlePlaceholder')}
                  aria-label={t('reports.modal.titlePlaceholder')}
                  className='min-w-0 flex-1 border-none bg-transparent text-lg font-medium text-foreground outline-none placeholder:text-muted'
                />
                <Button
                  slot='close'
                  variant='ghost'
                  size='sm'
                  radius='lg'
                  isIconOnly
                  aria-label={t('common.close')}
                  className='shrink-0 size-10 text-muted hover:text-foreground hover:bg-zinc-800'
                >
                  <Icon
                    icon='mdi:close'
                    width={16}
                  />
                </Button>
              </div>

              {/* Schedule tabs */}
              <Tabs
                defaultSelectedKey='once'
                className='w-full'
              >
                <Tabs.ListContainer>
                  <Tabs.List
                    aria-label={t('reports.modal.tabsAriaLabel')}
                    className='rounded-[28px] bg-zinc-800 px-1 py-1 gap-0.5 w-fit'
                  >
                    <Tabs.Tab
                      id='once'
                      className='rounded-[24px] px-3 py-1.5 text-sm font-medium whitespace-nowrap text-zinc-400 data-[selected=true]:text-foreground'
                    >
                      {t('reports.modal.tabOnce')}
                      <Tabs.Indicator className='rounded-[24px] bg-zinc-700 shadow-md' />
                    </Tabs.Tab>
                    <Tabs.Tab
                      id='daily'
                      className='rounded-[24px] px-3 py-1.5 text-sm font-medium whitespace-nowrap text-zinc-400 data-[selected=true]:text-foreground'
                    >
                      {t('reports.modal.tabDaily')}
                      <Tabs.Indicator className='rounded-[24px] bg-zinc-700 shadow-md' />
                    </Tabs.Tab>
                    <Tabs.Tab
                      id='weekly'
                      className='rounded-[24px] px-3 py-1.5 text-sm font-medium whitespace-nowrap text-zinc-400 data-[selected=true]:text-foreground'
                    >
                      {t('reports.modal.tabWeekly')}
                      <Tabs.Indicator className='rounded-[24px] bg-zinc-700 shadow-md' />
                    </Tabs.Tab>
                    <Tabs.Tab
                      id='monthly'
                      className='rounded-[24px] px-3 py-1.5 text-sm font-medium whitespace-nowrap text-zinc-400 data-[selected=true]:text-foreground'
                    >
                      {t('reports.modal.tabMonthly')}
                      <Tabs.Indicator className='rounded-[24px] bg-zinc-700 shadow-md' />
                    </Tabs.Tab>
                    <Tabs.Tab
                      id='yearly'
                      className='rounded-[24px] px-3 py-1.5 text-sm font-medium whitespace-nowrap text-zinc-400 data-[selected=true]:text-foreground'
                    >
                      {t('reports.modal.tabYearly')}
                      <Tabs.Indicator className='rounded-[24px] bg-zinc-700 shadow-md' />
                    </Tabs.Tab>
                  </Tabs.List>
                </Tabs.ListContainer>

                {/* Tab 1: Once — full form */}
                <Tabs.Panel
                  id='once'
                  className='flex flex-col gap-4 pt-4'
                >
                  <div className='flex items-end gap-1'>
                    <TimeField
                      name='report-time'
                      className='flex-1'
                    >
                      <Label className='mb-1 block text-sm font-medium text-foreground'>
                        {t('reports.modal.timeLabel')}
                      </Label>
                      <TimeField.Group className='flex h-9 min-h-9 w-full items-center overflow-hidden rounded-xl bg-zinc-900'>
                        <TimeField.Input className='flex flex-1 items-center gap-px text-sm text-muted'>
                          {segment => (
                            <TimeField.Segment
                              segment={segment}
                              className='rounded px-0.5 text-sm outline-none data-[placeholder=true]:text-muted focus:bg-zinc-700 focus:text-foreground'
                            />
                          )}
                        </TimeField.Input>
                      </TimeField.Group>
                    </TimeField>

                    <DateField
                      name='report-date'
                      className='w-72'
                    >
                      <Label className='mb-1 block text-sm font-medium text-foreground'>
                        {t('reports.modal.dateLabel')}
                      </Label>
                      <DateField.Group className='flex h-9 min-h-9 w-full items-center overflow-hidden rounded-xl bg-zinc-900'>
                        <DateField.Input className='flex flex-1 items-center gap-px text-sm text-foreground'>
                          {segment => (
                            <DateField.Segment
                              segment={segment}
                              className='rounded px-0.5 text-sm outline-none data-[placeholder=true]:text-muted focus:bg-zinc-700 focus:text-foreground'
                            />
                          )}
                        </DateField.Input>
                      </DateField.Group>
                    </DateField>
                  </div>

                  <div className='flex flex-col gap-1'>
                    <Label
                      htmlFor='report-query'
                      className='text-sm font-medium text-foreground'
                    >
                      {t('reports.modal.queryLabel')}
                    </Label>
                    <TextArea
                      id='report-query'
                      className='h-40 w-full resize-none rounded-xl bg-zinc-900 px-3 py-2 text-sm text-foreground placeholder:text-muted'
                      placeholder={t('reports.modal.queryPlaceholder')}
                      value={query}
                      onChange={e => setQuery(e.target.value)}
                    />
                  </div>
                </Tabs.Panel>

                {/* Remaining tabs — intentionally empty */}
                <Tabs.Panel
                  id='daily'
                  className='pt-4'
                />
                <Tabs.Panel
                  id='weekly'
                  className='pt-4'
                />
                <Tabs.Panel
                  id='monthly'
                  className='pt-4'
                />
                <Tabs.Panel
                  id='yearly'
                  className='pt-4'
                />
              </Tabs>

              {/* Footer */}
              <div className='flex justify-end'>
                <Button
                  className='bg-foreground font-medium text-background'
                  radius='full'
                >
                  {t('reports.modal.submitButton')}
                </Button>
              </div>
            </div>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  );
}
