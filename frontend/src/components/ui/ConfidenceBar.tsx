"use client";

import { motion } from "framer-motion";
import { confidenceBand, confidencePct } from "@/lib/format";
import { cn } from "@/lib/cn";

const toneColor: Record<string, string> = {
  high: "bg-emerald-500",
  medium: "bg-amber-500",
  low: "bg-rose-500",
};

export function ConfidenceBar({
  value,
  showLabel = true,
  className,
}: {
  value: number | null | undefined;
  showLabel?: boolean;
  className?: string;
}) {
  const band = confidenceBand(value);
  const pct = value == null ? 0 : value <= 1 ? value * 100 : value;

  return (
    <div className={cn("w-full", className)}>
      {showLabel && (
        <div className="mb-1 flex items-center justify-between text-xs">
          <span className="text-muted">Confidence</span>
          <span className="font-medium text-foreground">
            {confidencePct(value)} · {band.label}
          </span>
        </div>
      )}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-2">
        <motion.div
          className={cn("h-full rounded-full", toneColor[band.tone])}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
