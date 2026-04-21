import { motion } from "motion/react";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type FigmaConfirmDialogProps = {
  t: TFn;
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Оверлей и карточка в стиле FigmaSearchModal. */
export function FigmaConfirmDialog({
  t,
  open,
  title,
  message,
  confirmLabel,
  cancelLabel,
  danger,
  onConfirm,
  onCancel,
}: FigmaConfirmDialogProps) {
  void t;
  if (!open) return null;

  return (
    <motion.div
      className="fixed inset-0 z-[110] flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      <motion.div
        className="absolute inset-0"
        style={{ background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)" }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        onClick={onCancel}
      />
      <motion.div
        className="relative z-10 w-full max-w-[420px] overflow-hidden rounded-[24px] border border-solid border-[#28282c] bg-[#18181b] px-6 py-5 shadow-xl"
        initial={{ opacity: 0, scale: 0.97, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="figma-confirm-title"
        aria-describedby="figma-confirm-desc"
      >
        <h2
          id="figma-confirm-title"
          className="font-sans text-[18px] font-medium leading-snug text-[#fcfcfc]"
        >
          {title}
        </h2>
        <p
          id="figma-confirm-desc"
          className="mt-2 font-sans text-[14px] leading-relaxed text-[#a1a1aa]"
        >
          {message}
        </p>
        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-[24px] bg-[#27272a] px-4 py-2 font-sans text-[14px] font-medium text-[#fcfcfc] transition-colors hover:bg-[#323236] active:scale-[0.97]"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`rounded-[24px] px-4 py-2 font-sans text-[14px] font-medium transition-colors active:scale-[0.97] ${
              danger
                ? "bg-red-600 text-white hover:bg-red-500"
                : "bg-[#fcfcfc] text-[#18181b] hover:bg-[#e4e4e7]"
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
