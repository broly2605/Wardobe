import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type Tone = "default" | "brand" | "success" | "warning" | "danger";

const tones: Record<Tone, string> = {
  default: "bg-surface-2 text-muted border-border",
  brand: "bg-brand-soft text-brand border-brand/30",
  success:
    "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
  warning:
    "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
  danger:
    "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30",
};

export function Badge({
  children,
  tone = "default",
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
