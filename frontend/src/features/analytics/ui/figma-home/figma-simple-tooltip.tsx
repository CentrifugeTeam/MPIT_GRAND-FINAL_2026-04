import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

type Props = {
  label: string;
  children: React.ReactNode;
  /** У узкой колонки (сайдбар) используйте right — подсказка уходит в область контента и не обрезается. */
  side?: "bottom" | "top" | "left" | "right";
};

const GAP = 8;
const TOOLTIP_Z = 50_000;

type Coords = { top: number; left: number; transform: string };

function computeCoords(
  rect: DOMRect,
  side: NonNullable<Props["side"]>,
): Coords {
  switch (side) {
    case "top":
      return {
        top: rect.top - GAP,
        left: rect.left + rect.width / 2,
        transform: "translate(-50%, -100%)",
      };
    case "left":
      return {
        top: rect.top + rect.height / 2,
        left: rect.left - GAP,
        transform: "translate(-100%, -50%)",
      };
    case "right":
      return {
        top: rect.top + rect.height / 2,
        left: rect.right + GAP,
        transform: "translateY(-50%)",
      };
    case "bottom":
    default:
      return {
        top: rect.bottom + GAP,
        left: rect.left + rect.width / 2,
        transform: "translateX(-50%)",
      };
  }
}

/** Тултип в портале: не режется overflow:hidden у предков, поверх оверлеев модалок. */
export function FigmaSimpleTooltip({ label, children, side = "bottom" }: Props) {
  const [open, setOpen] = useState(false);
  const [coords, setCoords] = useState<Coords | null>(null);
  const leaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const anchorRef = useRef<HTMLSpanElement>(null);
  const id = useId();

  const updatePosition = useCallback(() => {
    const el = anchorRef.current;
    if (!el || !open) return;
    const rect = el.getBoundingClientRect();
    setCoords(computeCoords(rect, side));
  }, [open, side]);

  useLayoutEffect(() => {
    if (!open) return;
    updatePosition();
  }, [open, side, label, updatePosition]);

  useEffect(() => {
    if (!open) return;
    updatePosition();
    const onScrollOrResize = () => updatePosition();
    window.addEventListener("scroll", onScrollOrResize, true);
    window.addEventListener("resize", onScrollOrResize);
    return () => {
      window.removeEventListener("scroll", onScrollOrResize, true);
      window.removeEventListener("resize", onScrollOrResize);
    };
  }, [open, updatePosition]);

  const clearLeave = useCallback(() => {
    if (leaveTimer.current) {
      clearTimeout(leaveTimer.current);
      leaveTimer.current = null;
    }
  }, []);

  const onEnter = useCallback(() => {
    clearLeave();
    setOpen(true);
  }, [clearLeave]);

  const onLeave = useCallback(() => {
    clearLeave();
    leaveTimer.current = setTimeout(() => {
      setCoords(null);
      setOpen(false);
    }, 80);
  }, [clearLeave]);

  const wrap =
    side === "left" || side === "right"
      ? "whitespace-normal text-left leading-snug"
      : "whitespace-nowrap";

  const tip =
    open &&
    coords &&
    typeof document !== "undefined" &&
    createPortal(
      <span
        id={id}
        role="tooltip"
        style={{
          position: "fixed",
          top: coords.top,
          left: coords.left,
          transform: coords.transform,
          zIndex: TOOLTIP_Z,
        }}
        className={`pointer-events-none max-w-[min(280px,calc(100vw-16px))] rounded-lg border border-solid border-[#3f3f46] bg-[#27272a] px-2.5 py-1.5 font-sans text-[11px] font-medium text-[#fcfcfc] shadow-[0_4px_24px_rgba(0,0,0,0.35)] ${wrap}`}
      >
        {label}
      </span>,
      document.body,
    );

  return (
    <span
      ref={anchorRef}
      className="relative inline-flex max-w-full"
      onPointerEnter={onEnter}
      onPointerLeave={onLeave}
    >
      <span aria-describedby={open ? id : undefined}>{children}</span>
      {tip}
    </span>
  );
}
