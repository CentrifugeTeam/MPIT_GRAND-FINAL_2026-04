import { useCallback, useState } from 'react';
import { motion } from 'motion/react';

import type { AppNotification } from '@/shared/api/notifications-api';

type TFn = (key: string, opts?: Record<string, unknown>) => string;

function payloadInvite(p: Record<string, unknown> | null | undefined) {
  const o = p && typeof p === 'object' ? p : {};
  return {
    invite_id: String(o.invite_id ?? ''),
    conversation_id: String(o.conversation_id ?? ''),
    owner_email: String(o.owner_email ?? ''),
    chat_title: String(o.chat_title ?? ''),
  };
}

export type FigmaChatInviteNotificationModalProps = {
  t: TFn;
  notification: AppNotification;
  onClose: () => void;
  onAccept: (inviteId: string, notificationId: string) => Promise<void>;
  onReject: (inviteId: string, notificationId: string) => Promise<void>;
};

export function FigmaChatInviteNotificationModal({
  t,
  notification,
  onClose,
  onAccept,
  onReject,
}: FigmaChatInviteNotificationModalProps) {
  const [busy, setBusy] = useState(false);
  const pl = payloadInvite(notification.payload ?? undefined);
  const title = (notification.title || pl.chat_title || 'Chat').trim();
  const from = (pl.owner_email || '').trim() || notification.message;

  const run = useCallback(
    async (kind: 'accept' | 'reject') => {
      if (!pl.invite_id) return;
      setBusy(true);
      try {
        if (kind === 'accept') {
          await onAccept(pl.invite_id, notification.id);
        } else {
          await onReject(pl.invite_id, notification.id);
        }
        onClose();
      } finally {
        setBusy(false);
      }
    },
    [pl.invite_id, notification.id, onAccept, onReject, onClose],
  );

  return (
    <motion.div
      className='fixed inset-0 z-[120] flex items-center justify-center p-4'
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className='absolute inset-0 bg-black/60 backdrop-blur-sm'
        onClick={() => !busy && onClose()}
      />
      <motion.div
        className='relative z-10 w-full max-w-md rounded-3xl border border-[#28282c] bg-[#18181b] p-6 shadow-xl'
        initial={{ scale: 0.96, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
      >
        <h2 className='mb-1 font-sans text-lg font-semibold text-[#fafafa]'>
          {t('home.figma.chatInviteModalTitle')}
        </h2>
        <p className='mb-1 font-sans text-[15px] text-[#e4e4e7]'>{title}</p>
        <p className='mb-6 font-sans text-[13px] text-[#a1a1aa]'>
          {t('home.figma.chatInviteFrom')}: {from}
        </p>
        <div className='flex justify-end gap-2'>
          <button
            type='button'
            disabled={busy || !pl.invite_id}
            onClick={() => void run('reject')}
            className='rounded-xl border border-[#3f3f46] px-4 py-2 font-sans text-[13px] text-[#e4e4e7] hover:bg-[#27272a] disabled:opacity-50'
          >
            {t('home.figma.chatInviteReject')}
          </button>
          <button
            type='button'
            disabled={busy || !pl.invite_id}
            onClick={() => void run('accept')}
            className='rounded-xl bg-[#3b82f6] px-4 py-2 font-sans text-[13px] text-white hover:bg-[#2563eb] disabled:opacity-50'
          >
            {t('home.figma.chatInviteAccept')}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
