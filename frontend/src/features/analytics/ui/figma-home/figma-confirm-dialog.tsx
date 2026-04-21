import { motion } from "motion/react";

export type FigmaConfirmDialogProps = {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function FigmaConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  cancelLabel,
  danger,
  onConfirm,
  onCancel,
}: FigmaConfirmDialogProps) {
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
        className="relative z-10 w-full max-w-sm overflow-hidden rounded-3xl border border-border bg-background px-6 py-5 shadow-xl"
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
          className="text-lg font-medium leading-snug text-foreground"
        >
          {title}
        </h2>
        <p
          id="figma-confirm-desc"
          className="mt-2 text-sm leading-relaxed text-muted"
        >
          {message}
        </p>
        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-3xl bg-surface px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface-secondary active:scale-[0.97]"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`rounded-3xl px-4 py-2 text-sm font-medium transition-colors active:scale-[0.97] ${
              danger
                ? "bg-danger text-danger-foreground hover:bg-danger/90"
                : "bg-foreground text-background hover:bg-foreground/90"
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
