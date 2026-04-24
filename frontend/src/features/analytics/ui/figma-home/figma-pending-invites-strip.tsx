import type { ChatInviteItem } from '@/features/analytics/api/analytics-api';

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type FigmaPendingInvitesStripProps = {
  t: TFn;
  invites: ChatInviteItem[];
  busy: boolean;
  onAccept: (inviteId: string) => Promise<void>;
  onReject: (inviteId: string) => Promise<void>;
};

export function FigmaPendingInvitesStrip({
  t,
  invites,
  busy,
  onAccept,
  onReject,
}: FigmaPendingInvitesStripProps) {
  if (!busy && invites.length === 0) {
    return null;
  }

  return (
    <div className='mb-6 w-full rounded-[20px] border border-[#28282c] bg-[#18181b]/80 px-4 py-3'>
      <div className='mb-2 flex items-center justify-between gap-2'>
        <span className='font-sans text-[13px] font-medium text-[#e4e4e7]'>
          {t('home.figma.pendingInvitesTitle')}
        </span>
        {busy && (
          <span className='font-sans text-[11px] text-[#a1a1aa]'>
            {t('home.figma.pendingInvitesLoading')}
          </span>
        )}
      </div>
      {busy && invites.length === 0 ? (
        <p className='font-sans text-[12px] text-[#71717a]'>{t('home.figma.pendingInvitesLoading')}</p>
      ) : (
        <ul className='flex flex-col gap-2'>
          {invites.map(inv => (
            <li
              key={inv.invite_id}
              className='flex flex-wrap items-center justify-between gap-2 rounded-[14px] bg-[#27272a]/60 px-3 py-2'
            >
              <div className='min-w-0 flex-1'>
                <p className='truncate font-sans text-[12px] text-[#e4e4e7]'>
                  {(inv.chat_title && inv.chat_title.trim()) || inv.conversation_id.slice(0, 8) + '…'}
                </p>
                {inv.owner_email ? (
                  <p className='truncate font-sans text-[11px] text-[#71717a]'>
                    {t('home.figma.chatInviteFrom')}: {inv.owner_email}
                  </p>
                ) : null}
              </div>
              <div className='flex shrink-0 gap-1.5'>
                <button
                  type='button'
                  disabled={busy}
                  onClick={() => void onReject(inv.invite_id)}
                  className='rounded-[10px] border border-[#3f3f46] px-2.5 py-1 font-sans text-[11px] text-[#e4e4e7] hover:bg-[#3f3f46] disabled:opacity-50'
                >
                  {t('home.figma.chatInviteReject')}
                </button>
                <button
                  type='button'
                  disabled={busy}
                  onClick={() => void onAccept(inv.invite_id)}
                  className='rounded-[10px] bg-[#3b82f6] px-2.5 py-1 font-sans text-[11px] text-white hover:bg-[#2563eb] disabled:opacity-50'
                >
                  {t('home.figma.chatInviteAccept')}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
