import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Button,
  Calendar,
  DateField,
  DatePicker,
  Input,
  Label,
  ListBox,
  Modal,
  Select,
  Tabs,
  TextArea,
  TimeField,
} from '@heroui/react';
import { Icon } from '@iconify/react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { DateValue, Time } from '@internationalized/date';

import type { AnalyticsDataSourceItem } from '@/features/analytics/api/analytics-api';
import {
  createReportTask,
  type CreateReportTaskBody,
  type ReportTaskScheduleType,
} from '@/features/analytics/api/analytics-api';

type Props = {
  dataSources?: AnalyticsDataSourceItem[];
};

const fieldGroupCls =
  'flex h-9 min-h-9 w-full items-center overflow-hidden rounded-xl bg-zinc-900 border-0 ring-0 outline-none focus-within:ring-0 focus-within:outline-none';

const WEEKDAY_ISO: Record<string, number> = {
  monday: 1,
  tuesday: 2,
  wednesday: 3,
  thursday: 4,
  friday: 5,
  saturday: 6,
  sunday: 7,
};

function fmtTime(t: Time): string {
  return `${String(t.hour).padStart(2, '0')}:${String(t.minute).padStart(2, '0')}`;
}

export function CreateReportModal({ dataSources = [] }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const [isOpen, setIsOpen] = useState(false);
  const [reportName, setReportName] = useState('');
  const [query, setQuery] = useState('');
  const [monthDay, setMonthDay] = useState(1);
  const [scheduleTab, setScheduleTab] =
    useState<ReportTaskScheduleType>('once');
  const [sourceKey, setSourceKey] = useState<string>(dataSources[0]?.key ?? '');
  const [time, setTime] = useState<Time | null>(null);
  const [dateOnce, setDateOnce] = useState<DateValue | null>(null);
  const [dateYearly, setDateYearly] = useState<DateValue | null>(null);
  const [weekday, setWeekday] = useState('monday');

  const { mutate, isPending } = useMutation({
    mutationFn: createReportTask,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['reportTasks'] });
      resetAndClose();
    },
  });

  function resetAndClose() {
    setIsOpen(false);
    setReportName('');
    setQuery('');
    setTime(null);
    setDateOnce(null);
    setDateYearly(null);
    setWeekday('monday');
    setMonthDay(1);
    setScheduleTab('once');
  }

  function handleSubmit() {
    if (!reportName.trim() || !query.trim() || !sourceKey) return;

    const timeStr = time ? fmtTime(time) : '09:00';
    let schedule: CreateReportTaskBody['schedule'];

    switch (scheduleTab) {
      case 'once': {
        if (!dateOnce) return;
        const once_at = `${dateOnce.year}-${String(dateOnce.month).padStart(2, '0')}-${String(dateOnce.day).padStart(2, '0')}T${timeStr}:00`;
        schedule = { schedule_type: 'once', timezone: 'UTC', once_at };
        break;
      }
      case 'daily':
        schedule = {
          schedule_type: 'daily',
          timezone: 'UTC',
          daily_time: timeStr,
        };
        break;
      case 'weekly':
        schedule = {
          schedule_type: 'weekly',
          timezone: 'UTC',
          weekly_day: WEEKDAY_ISO[weekday],
          weekly_time: timeStr,
        };
        break;
      case 'monthly':
        schedule = {
          schedule_type: 'monthly',
          timezone: 'UTC',
          monthly_day: monthDay,
          monthly_time: timeStr,
        };
        break;
      case 'yearly': {
        if (!dateYearly) return;
        const yearly_date_ddmm = `${String(dateYearly.day).padStart(2, '0')}:${String(dateYearly.month).padStart(2, '0')}`;
        schedule = {
          schedule_type: 'yearly',
          timezone: 'UTC',
          yearly_date_ddmm,
          yearly_time: timeStr,
        };
        break;
      }
    }

    mutate({
      title: reportName.trim(),
      instruction: query.trim(),
      analytics_source_key: sourceKey,
      is_active: true,
      schedule,
    });
  }

  const dbSelect = (
    <Select
      className='w-full'
      placeholder={t('reports.modal.dbPlaceholder')}
      selectedKey={sourceKey}
      onSelectionChange={k => setSourceKey(String(k))}
    >
      <Label className='mb-1 block text-sm font-medium text-foreground'>
        {t('reports.modal.dbLabel')}
      </Label>
      <Select.Trigger className='h-9 w-full rounded-xl border-0 bg-zinc-900 px-3 ring-0 outline-none focus:ring-0 focus:outline-none'>
        <Select.Value className='text-sm text-muted' />
        <Select.Indicator />
      </Select.Trigger>
      <Select.Popover>
        <ListBox>
          {dataSources.length === 0 ? (
            <ListBox.Item
              id='__empty'
              isDisabled
              textValue='—'
            >
              —
            </ListBox.Item>
          ) : (
            dataSources.map(s => (
              <ListBox.Item
                key={s.key}
                id={s.key}
                textValue={s.display_name}
              >
                {s.display_name}
                <ListBox.ItemIndicator />
              </ListBox.Item>
            ))
          )}
        </ListBox>
      </Select.Popover>
    </Select>
  );

  const timeField = (
    <TimeField
      name='report-time'
      className='flex-1'
      value={time ?? undefined}
      onChange={setTime}
    >
      <Label className='mb-1 block text-sm font-medium text-foreground'>
        {t('reports.modal.timeLabel')}
      </Label>
      <TimeField.Group className={fieldGroupCls}>
        <TimeField.Input className='flex flex-1 items-center gap-px px-3 text-sm text-foreground'>
          {segment => (
            <TimeField.Segment
              segment={segment}
              className='rounded px-0.5 text-sm outline-none data-[placeholder=true]:text-muted focus:bg-zinc-700 focus:text-foreground'
            />
          )}
        </TimeField.Input>
        <div className='flex h-9 w-10 shrink-0 items-center justify-center text-zinc-400'>
          <Icon
            icon='mdi:clock-outline'
            width={16}
          />
        </div>
      </TimeField.Group>
    </TimeField>
  );

  function datePicker(
    value: DateValue | null,
    onChange: (v: DateValue | null) => void,
    ariaKey: string,
  ) {
    return (
      <DatePicker
        className='flex-1'
        name={ariaKey}
        value={value ?? undefined}
        onChange={onChange}
      >
        <Label className='mb-1 block text-sm font-medium text-foreground'>
          {t('reports.modal.dateLabel')}
        </Label>
        <DateField.Group
          fullWidth
          className={fieldGroupCls}
        >
          <DateField.Input className='flex flex-1 items-center gap-px px-3 text-sm text-foreground'>
            {segment => (
              <DateField.Segment
                segment={segment}
                className='rounded px-0.5 text-sm outline-none data-[placeholder=true]:text-muted focus:bg-zinc-700 focus:text-foreground'
              />
            )}
          </DateField.Input>
          <DateField.Suffix className='flex h-9 w-10 shrink-0 items-center justify-center'>
            <DatePicker.Trigger className='flex size-full items-center justify-center text-zinc-400 hover:text-foreground'>
              <DatePicker.TriggerIndicator className='size-4' />
            </DatePicker.Trigger>
          </DateField.Suffix>
        </DateField.Group>
        <DatePicker.Popover>
          <Calendar aria-label={t('reports.modal.calendarAriaLabel')}>
            <Calendar.Header>
              <Calendar.YearPickerTrigger>
                <Calendar.YearPickerTriggerHeading />
                <Calendar.YearPickerTriggerIndicator />
              </Calendar.YearPickerTrigger>
              <Calendar.NavButton slot='previous' />
              <Calendar.NavButton slot='next' />
            </Calendar.Header>
            <Calendar.Grid>
              <Calendar.GridHeader>
                {day => <Calendar.HeaderCell>{day}</Calendar.HeaderCell>}
              </Calendar.GridHeader>
              <Calendar.GridBody>
                {date => <Calendar.Cell date={date} />}
              </Calendar.GridBody>
            </Calendar.Grid>
            <Calendar.YearPickerGrid>
              <Calendar.YearPickerGridBody>
                {({ year }) => <Calendar.YearPickerCell year={year} />}
              </Calendar.YearPickerGridBody>
            </Calendar.YearPickerGrid>
          </Calendar>
        </DatePicker.Popover>
      </DatePicker>
    );
  }

  function queryArea(id: string) {
    return (
      <div className='flex flex-col gap-1'>
        <Label
          htmlFor={id}
          className='text-sm font-medium text-foreground'
        >
          {t('reports.modal.queryLabel')}
        </Label>
        <TextArea
          id={id}
          className='h-40 w-full resize-none rounded-xl border-0 bg-zinc-900 px-3 py-2 text-sm text-foreground ring-0 outline-none placeholder:text-muted focus:ring-0 focus:outline-none'
          placeholder={t('reports.modal.queryPlaceholder')}
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
      </div>
    );
  }

  return (
    <>
      <Button
        variant='outline'
        radius='full'
        onPress={() => setIsOpen(true)}
      >
        <Icon
          icon='mdi:plus'
          width={16}
          className='mr-1'
        />
        {t('reports.addReport')}
      </Button>

      <Modal
        isOpen={isOpen}
        onOpenChange={setIsOpen}
      >
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
                    className='min-w-0 flex-1 border-none bg-transparent text-lg font-medium text-foreground outline-none ring-0 placeholder:text-muted focus:outline-none focus:ring-0'
                  />
                  <Button
                    slot='close'
                    variant='ghost'
                    size='sm'
                    radius='lg'
                    isIconOnly
                    aria-label={t('common.close')}
                    className='size-10 shrink-0 text-zinc-400 hover:bg-zinc-800 hover:text-foreground'
                  >
                    <Icon
                      icon='mdi:close'
                      width={16}
                    />
                  </Button>
                </div>

                {/* Schedule tabs */}
                <Tabs
                  selectedKey={scheduleTab}
                  onSelectionChange={k =>
                    setScheduleTab(k as ReportTaskScheduleType)
                  }
                  className='w-full'
                >
                  <Tabs.ListContainer>
                    <Tabs.List
                      aria-label={t('reports.modal.tabsAriaLabel')}
                      className='w-full rounded-[28px] bg-zinc-800 px-2 py-1 gap-0.5'
                    >
                      {(
                        [
                          'once',
                          'daily',
                          'weekly',
                          'monthly',
                          'yearly',
                        ] as const
                      ).map(key => (
                        <Tabs.Tab
                          key={key}
                          id={key}
                          className='rounded-[20px] px-3 py-1.5 text-sm font-medium whitespace-nowrap text-zinc-400 data-[selected=true]:text-foreground'
                        >
                          {t(
                            `reports.modal.tab${key.charAt(0).toUpperCase()}${key.slice(1)}`,
                          )}
                          <Tabs.Indicator className='rounded-[20px] bg-zinc-700 shadow-md' />
                        </Tabs.Tab>
                      ))}
                    </Tabs.List>
                  </Tabs.ListContainer>

                  {/* Once */}
                  <Tabs.Panel
                    id='once'
                    className='flex flex-col gap-4 pt-4'
                  >
                    {dbSelect}
                    <div className='flex items-end gap-2'>
                      {timeField}
                      {datePicker(dateOnce, setDateOnce, 'report-date-once')}
                    </div>
                    {queryArea('report-query-once')}
                  </Tabs.Panel>

                  {/* Daily */}
                  <Tabs.Panel
                    id='daily'
                    className='flex flex-col gap-4 pt-4'
                  >
                    {dbSelect}
                    <div className='flex items-end gap-2'>{timeField}</div>
                    {queryArea('report-query-daily')}
                  </Tabs.Panel>

                  {/* Weekly */}
                  <Tabs.Panel
                    id='weekly'
                    className='flex flex-col gap-4 pt-4'
                  >
                    {dbSelect}
                    <div className='flex items-end gap-2'>
                      {timeField}
                      <Select
                        className='w-44 shrink-0'
                        selectedKey={weekday}
                        onSelectionChange={k => setWeekday(String(k))}
                      >
                        <Label className='mb-1 block text-sm font-medium text-foreground'>
                          {t('reports.modal.weekdayLabel')}
                        </Label>
                        <Select.Trigger className='h-9 w-full rounded-xl border-0 bg-zinc-900 px-3 ring-0 outline-none focus:ring-0 focus:outline-none'>
                          <Select.Value className='text-sm text-foreground' />
                          <Select.Indicator />
                        </Select.Trigger>
                        <Select.Popover>
                          <ListBox>
                            {(
                              [
                                'monday',
                                'tuesday',
                                'wednesday',
                                'thursday',
                                'friday',
                                'saturday',
                                'sunday',
                              ] as const
                            ).map(day => (
                              <ListBox.Item
                                key={day}
                                id={day}
                                textValue={t(`reports.modal.weekdays.${day}`)}
                              >
                                {t(`reports.modal.weekdays.${day}`)}
                                <ListBox.ItemIndicator />
                              </ListBox.Item>
                            ))}
                          </ListBox>
                        </Select.Popover>
                      </Select>
                    </div>
                    {queryArea('report-query-weekly')}
                  </Tabs.Panel>

                  {/* Monthly */}
                  <Tabs.Panel
                    id='monthly'
                    className='flex flex-col gap-4 pt-4'
                  >
                    {dbSelect}
                    <div className='flex items-end gap-2'>
                      {timeField}
                      <div className='flex w-44 shrink-0 flex-col gap-1'>
                        <div className='mb-1 flex items-center gap-1'>
                          <Label className='text-sm font-medium text-foreground'>
                            {t('reports.modal.dayOfMonthLabel')}
                          </Label>
                          <span title={t('reports.modal.dayOfMonthTooltip')}>
                            <Icon
                              icon='mdi:information-outline'
                              width={12}
                              className='text-zinc-400'
                            />
                          </span>
                        </div>
                        <div className={fieldGroupCls}>
                          <input
                            type='number'
                            min={1}
                            max={31}
                            value={monthDay}
                            onChange={e =>
                              setMonthDay(
                                Math.max(
                                  1,
                                  Math.min(31, Number(e.target.value)),
                                ),
                              )
                            }
                            className='flex-1 bg-transparent px-3 text-sm text-foreground outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
                          />
                          <div className='flex h-9 w-8 shrink-0 flex-col items-center justify-center text-zinc-400'>
                            <button
                              type='button'
                              tabIndex={-1}
                              onClick={() =>
                                setMonthDay(d => Math.min(31, d + 1))
                              }
                              className='flex flex-1 w-full items-center justify-center hover:text-foreground'
                            >
                              <Icon
                                icon='mdi:chevron-up'
                                width={12}
                              />
                            </button>
                            <button
                              type='button'
                              tabIndex={-1}
                              onClick={() =>
                                setMonthDay(d => Math.max(1, d - 1))
                              }
                              className='flex flex-1 w-full items-center justify-center hover:text-foreground'
                            >
                              <Icon
                                icon='mdi:chevron-down'
                                width={12}
                              />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                    {queryArea('report-query-monthly')}
                  </Tabs.Panel>

                  {/* Yearly */}
                  <Tabs.Panel
                    id='yearly'
                    className='flex flex-col gap-4 pt-4'
                  >
                    {dbSelect}
                    <div className='flex items-end gap-2'>
                      {timeField}
                      {datePicker(
                        dateYearly,
                        setDateYearly,
                        'report-date-yearly',
                      )}
                    </div>
                    {queryArea('report-query-yearly')}
                  </Tabs.Panel>
                </Tabs>

                {/* Footer */}
                <div className='flex justify-end'>
                  <Button
                    className='bg-foreground font-medium text-background'
                    radius='full'
                    isLoading={isPending}
                    isDisabled={isPending}
                    onPress={handleSubmit}
                  >
                    {t('reports.modal.submitButton')}
                  </Button>
                </div>
              </div>
            </Modal.Dialog>
          </Modal.Container>
        </Modal.Backdrop>
      </Modal>
    </>
  );
}
