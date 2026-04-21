import { motion } from "motion/react";
import { Icon } from "@iconify/react";

import type { FigmaTranslateFn } from "@/features/analytics/config/figma-analytics-faq";

export function FigmaVoiceStubPanel({
  t,
  onClose,
}: {
  t: FigmaTranslateFn;
  onClose: () => void;
}) {
  return (
    <motion.div
      className="fixed bottom-8 left-1/2 z-50 w-[min(488px,calc(100vw-32px))] -translate-x-1/2"
      initial={{ opacity: 0, y: 16, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.97 }}
      transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
    >
      <div className="relative flex items-start gap-2 rounded-[24px] border border-solid border-[#28282c] bg-[#18181b] px-3 py-3 backdrop-blur-[20px]">
        <Icon icon="mdi:microphone" className="relative mt-1 shrink-0 text-[#fcfcfc]" width={20} />
        <div className="relative min-w-0 flex-1">
          <p className="font-sans text-[14px] font-medium leading-snug text-[#fcfcfc]">
            {t("home.figma.voiceTitle")}
          </p>
          <p className="mt-0.5 font-sans text-[14px] leading-snug text-[#a1a1aa]">
            {t("home.figma.voiceSubtitle")}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="relative shrink-0 rounded-[24px] bg-[#27272a] px-4 py-2 font-sans text-[14px] font-medium text-[#fcfcfc] transition-colors hover:bg-[#323236] active:scale-[0.97]"
        >
          {t("home.figma.voiceClose")}
        </button>
      </div>
    </motion.div>
  );
}
