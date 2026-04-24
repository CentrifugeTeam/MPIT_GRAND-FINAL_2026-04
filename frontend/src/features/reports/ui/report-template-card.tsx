import { Card } from "@heroui/react";
import { Icon } from "@iconify/react";

export type ReportTemplateCardProps = {
  title: string;
  description: string;
  onPress: () => void;
  "aria-label"?: string;
};

/**
 * Карточка пресета отчёта: 261×144, rounded-3xl, бордер 1px (макет дашборда).
 */
export function ReportTemplateCard({
  title,
  description,
  onPress,
  "aria-label": ariaLabel,
}: ReportTemplateCardProps) {
  return (
    <Card
      role="button"
      tabIndex={0}
      aria-label={ariaLabel ?? title}
      onClick={onPress}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onPress();
        }
      }}
      className="h-[144px] w-[251px] max-w-[261px] shrink-0 cursor-pointer rounded-3xl border border-[#28282C] bg-[#18181B]/40 p-4 transition-[transform,box-shadow] hover:brightness-[1.05] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-600/50 active:scale-[0.99]"
      style={{
        boxShadow:
          "0px 0px 1px 0px rgba(0,0,0,0.06), 0px 1px 2px 0px rgba(0,0,0,0.06), 0px 2px 4px 0px rgba(0,0,0,0.06), 0px 4px 8px 0px rgba(0,0,0,0.06)",
      }}
    >
      <div className="flex h-full min-h-0 flex-col items-stretch gap-1.5 overflow-hidden text-left">
        <Icon
          icon="mdi:file-document-outline"
          width={28}
          height={28}
          className="shrink-0 text-white"
          aria-hidden
        />
        <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-white">
          {title}
        </h3>
        {description ? (
          <p className="line-clamp-2 text-xs leading-snug text-zinc-400">
            {description}
          </p>
        ) : null}
      </div>
    </Card>
  );
}

