import { useCallback, useState } from 'react';
import { motion } from 'motion/react';

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type FigmaShareChatEmailsModalProps = {
  t: TFn;
  onClose: () => void;
  onSubmit: (emails: string[]) => Promise<void>;
};

function parseEmails(raw: string): string[] {
  const parts = raw.split(/[\s,;]+/).map(s => s.trim().toLowerCase());
  const seen = new Set<string>();
  const out: string[] = [];
  for (const p of parts) {
    if (p.length < 3 || !p.includes('@') || seen.has(p)) continue;
    seen.add(p);
    out.push(p);
  }
  return out;
}

export function FigmaShareChatEmailsModal({ t, onClose, onSubmit }: FigmaShareChatEmailsModalProps) {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const handleSubmit = useCallback(async () => {
    const emails = parseEmails(text);
    if (emails.length === 0) {
      setErr(t('home.figma.shareModalErrorEmpty'));
      return;
    }
    setErr(null);
    setBusy(true);
    try {
      await onSubmit(emails);
      onClose();
    } catch {
      setErr(t('home.figma.shareModalErrorSend'));
    } finally {
      setBusy(false);
    }
  }, [onSubmit, onClose, text, t]);

  return (
    <motion.div
      className='fixed inset-0 z-[110] flex items-start justify-center pt-[14vh]'
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className='absolute inset-0 bg-black/50 backdrop-blur-sm'
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        onClick={() => !busy && onClose()}
      />
      <motion.div
        className='relative z-10 w-full max-w-md rounded-3xl border border-[#28282c] bg-[#18181b] p-5 shadow-xl'
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2 className='mb-2 font-sans text-base font-semibold text-[#fafafa]'>
          {t('home.figma.shareModalTitle')}
        </h2>
        <p className='mb-3 font-sans text-[12px] leading-relaxed text-[#a1a1aa]'>
          {t('home.figma.shareModalHint')}
        </p>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder={t('home.figma.shareModalPlaceholder')}
          disabled={busy}
          rows={4}
          className='mb-2 w-full resize-y rounded-xl border border-[#3f3f46] bg-[#09090b] px-3 py-2 font-sans text-[13px] text-[#e4e4e7] outline-none ring-0 placeholder:text-[#71717a] focus:border-[#52525b]'
        />
        {err ? <p className='mb-2 font-sans text-[12px] text-danger'>{err}</p> : null}
        <div className='mt-3 flex justify-end gap-2'>
          <button
            type='button'
            disabled={busy}
            onClick={onClose}
            className='rounded-xl border border-[#3f3f46] px-4 py-2 font-sans text-[13px] text-[#e4e4e7] hover:bg-[#27272a] disabled:opacity-50'
          >
            {t('home.figma.shareModalCancel')}
          </button>
          <button
            type='button'
            disabled={busy}
            onClick={() => void handleSubmit()}
            className='rounded-xl bg-[#3b82f6] px-4 py-2 font-sans text-[13px] text-white hover:bg-[#2563eb] disabled:opacity-50'
          >
            {busy ? '…' : t('home.figma.shareModalSend')}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
