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

import type { AnalyticsDataSourceItem } from '@/features/analytics/api/analytics-api';

type Props = {
  dataSources?: AnalyticsDataSourceItem[];
};

const fieldGroupCls =
  'flex h-9 min-h-9 w-full items-center overflow-hidden rounded-xl bg-zinc-900 border-0 ring-0 outline-none focus-within:ring-0 focus-within:outline-none';

export function CreateReportModal({ dataSources = [] }: Props) {
  const { t } = useTranslation();
  const [reportName, setReportName] = useState('');
  const [query, setQuery] = useState('');
  const [monthDay, setMonthDay] = useState(1);

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
                defaultSelectedKey='once'
                className='w-full'
              >
                <Tabs.ListContainer>
                  <Tabs.List
                    aria-label={t('reports.modal.tabsAriaLabel')}
                    className='w-full rounded-[28px] bg-zinc-800 px-2 py-1 gap-0.5'
                  >
                    {(
                      ['once', 'daily', 'weekly', 'monthly', 'yearly'] as const
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

                {/* Tab 1: Once — full form */}
                <Tabs.Panel
                  id='once'
                  className='flex flex-col gap-4 pt-4'
                >
                  {/* Database Select */}
                  <Select
                    className='w-full'
                    placeholder={t('reports.modal.dbPlaceholder')}
                    defaultSelectedKey={dataSources[0]?.key}
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

                  {/* Time + Date row */}
                  <div className='flex items-end gap-2'>
                    {/* TimeField */}
                    <TimeField
                      name='report-time'
                      className='flex-1'
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

                    {/* DatePicker with calendar popup */}
                    <DatePicker
                      className='flex-1'
                      name='report-date'
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
                        <Calendar
                          aria-label={t('reports.modal.calendarAriaLabel')}
                        >
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
                              {day => (
                                <Calendar.HeaderCell>{day}</Calendar.HeaderCell>
                              )}
                            </Calendar.GridHeader>
                            <Calendar.GridBody>
                              {date => <Calendar.Cell date={date} />}
                            </Calendar.GridBody>
                          </Calendar.Grid>
                          <Calendar.YearPickerGrid>
                            <Calendar.YearPickerGridBody>
                              {({ year }) => (
                                <Calendar.YearPickerCell year={year} />
                              )}
                            </Calendar.YearPickerGridBody>
                          </Calendar.YearPickerGrid>
                        </Calendar>
                      </DatePicker.Popover>
                    </DatePicker>
                  </div>

                  {/* Query textarea */}
                  <div className='flex flex-col gap-1'>
                    <Label
                      htmlFor='report-query'
                      className='text-sm font-medium text-foreground'
                    >
                      {t('reports.modal.queryLabel')}
                    </Label>
                    <TextArea
                      id='report-query'
                      className='h-40 w-full resize-none rounded-xl border-0 bg-zinc-900 px-3 py-2 text-sm text-foreground ring-0 outline-none placeholder:text-muted focus:ring-0 focus:outline-none'
                      placeholder={t('reports.modal.queryPlaceholder')}
                      value={query}
                      onChange={e => setQuery(e.target.value)}
                    />
                  </div>
                </Tabs.Panel>

                <Tabs.Panel
                  id='daily'
                  className='flex flex-col gap-4 pt-4'
                >
                  {/* Database Select */}
                  <Select
                    className='w-full'
                    placeholder={t('reports.modal.dbPlaceholder')}
                    defaultSelectedKey={dataSources[0]?.key}
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

                  {/* Time + Date row */}
                  <div className='flex items-end gap-2'>
                    {/* TimeField */}
                    <TimeField
                      name='report-time'
                      className='flex-1'
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
                  </div>

                  {/* Query textarea */}
                  <div className='flex flex-col gap-1'>
                    <Label
                      htmlFor='report-query'
                      className='text-sm font-medium text-foreground'
                    >
                      {t('reports.modal.queryLabel')}
                    </Label>
                    <TextArea
                      id='report-query'
                      className='h-40 w-full resize-none rounded-xl border-0 bg-zinc-900 px-3 py-2 text-sm text-foreground ring-0 outline-none placeholder:text-muted focus:ring-0 focus:outline-none'
                      placeholder={t('reports.modal.queryPlaceholder')}
                      value={query}
                      onChange={e => setQuery(e.target.value)}
                    />
                  </div>
                </Tabs.Panel>

                <Tabs.Panel
                  id='weekly'
                  className='flex flex-col gap-4 pt-4'
                >
                  {/* Database Select */}
                  <Select
                    className='w-full'
                    placeholder={t('reports.modal.dbPlaceholder')}
                    defaultSelectedKey={dataSources[0]?.key}
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

                  {/* Time + Weekday row */}
                  <div className='flex items-end gap-2'>
                    {/* TimeField */}
                    <TimeField
                      name='report-time'
                      className='flex-1'
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

                    {/* Day of week Select */}
                    <Select
                      className='w-44 shrink-0'
                      defaultSelectedKey='monday'
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

                  {/* Query textarea */}
                  <div className='flex flex-col gap-1'>
                    <Label
                      htmlFor='report-query-weekly'
                      className='text-sm font-medium text-foreground'
                    >
                      {t('reports.modal.queryLabel')}
                    </Label>
                    <TextArea
                      id='report-query-weekly'
                      className='h-40 w-full resize-none rounded-xl border-0 bg-zinc-900 px-3 py-2 text-sm text-foreground ring-0 outline-none placeholder:text-muted focus:ring-0 focus:outline-none'
                      placeholder={t('reports.modal.queryPlaceholder')}
                      value={query}
                      onChange={e => setQuery(e.target.value)}
                    />
                  </div>
                </Tabs.Panel>

                <Tabs.Panel
                  id='monthly'
                  className='flex flex-col gap-4 pt-4'
                >
                  {/* Database Select */}
                  <Select
                    className='w-full'
                    placeholder={t('reports.modal.dbPlaceholder')}
                    defaultSelectedKey={dataSources[0]?.key}
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

                  {/* Time + Day of month row */}
                  <div className='flex items-end gap-2'>
                    {/* TimeField */}
                    <TimeField
                      name='report-time'
                      className='flex-1'
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

                    {/* Day of month input */}
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
                              Math.max(1, Math.min(31, Number(e.target.value))),
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
                            onClick={() => setMonthDay(d => Math.max(1, d - 1))}
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

                  {/* Query textarea */}
                  <div className='flex flex-col gap-1'>
                    <Label
                      htmlFor='report-query-monthly'
                      className='text-sm font-medium text-foreground'
                    >
                      {t('reports.modal.queryLabel')}
                    </Label>
                    <TextArea
                      id='report-query-monthly'
                      className='h-40 w-full resize-none rounded-xl border-0 bg-zinc-900 px-3 py-2 text-sm text-foreground ring-0 outline-none placeholder:text-muted focus:ring-0 focus:outline-none'
                      placeholder={t('reports.modal.queryPlaceholder')}
                      value={query}
                      onChange={e => setQuery(e.target.value)}
                    />
                  </div>
                </Tabs.Panel>

                <Tabs.Panel
                  id='yearly'
                  className='flex flex-col gap-4 pt-4'
                >
                  {/* Database Select */}
                  <Select
                    className='w-full'
                    placeholder={t('reports.modal.dbPlaceholder')}
                    defaultSelectedKey={dataSources[0]?.key}
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

                  {/* Time + Date row */}
                  <div className='flex items-end gap-2'>
                    {/* TimeField */}
                    <TimeField
                      name='report-time'
                      className='flex-1'
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

                    {/* DatePicker with calendar popup */}
                    <DatePicker
                      className='flex-1'
                      name='report-date'
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
                        <Calendar
                          aria-label={t('reports.modal.calendarAriaLabel')}
                        >
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
                              {day => (
                                <Calendar.HeaderCell>{day}</Calendar.HeaderCell>
                              )}
                            </Calendar.GridHeader>
                            <Calendar.GridBody>
                              {date => <Calendar.Cell date={date} />}
                            </Calendar.GridBody>
                          </Calendar.Grid>
                          <Calendar.YearPickerGrid>
                            <Calendar.YearPickerGridBody>
                              {({ year }) => (
                                <Calendar.YearPickerCell year={year} />
                              )}
                            </Calendar.YearPickerGridBody>
                          </Calendar.YearPickerGrid>
                        </Calendar>
                      </DatePicker.Popover>
                    </DatePicker>
                  </div>

                  {/* Query textarea */}
                  <div className='flex flex-col gap-1'>
                    <Label
                      htmlFor='report-query'
                      className='text-sm font-medium text-foreground'
                    >
                      {t('reports.modal.queryLabel')}
                    </Label>
                    <TextArea
                      id='report-query'
                      className='h-40 w-full resize-none rounded-xl border-0 bg-zinc-900 px-3 py-2 text-sm text-foreground ring-0 outline-none placeholder:text-muted focus:ring-0 focus:outline-none'
                      placeholder={t('reports.modal.queryPlaceholder')}
                      value={query}
                      onChange={e => setQuery(e.target.value)}
                    />
                  </div>
                </Tabs.Panel>
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
