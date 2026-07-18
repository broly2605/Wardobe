"use client";

import { motion } from "framer-motion";
import { humanize } from "@/lib/format";

export interface BarDatum {
  label: string;
  count: number;
  hex?: string;
}

/** Horizontal bar list — used for category/formality/color breakdowns. */
export function BarList({
  data,
  humanizeLabels = true,
}: {
  data: BarDatum[];
  humanizeLabels?: boolean;
}) {
  if (!data.length) {
    return <p className="py-6 text-center text-sm text-muted">No data yet.</p>;
  }
  const max = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="space-y-3">
      {data.map((d, i) => (
        <div key={`${d.label}-${i}`}>
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-foreground">
              {d.hex && (
                <span
                  className="h-3 w-3 rounded-full border border-border"
                  style={{ backgroundColor: d.hex }}
                />
              )}
              {humanizeLabels ? humanize(d.label) : d.label}
            </span>
            <span className="text-muted">{d.count}</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
            <motion.div
              className="h-full rounded-full"
              style={{
                background: d.hex ?? "rgb(var(--brand))",
              }}
              initial={{ width: 0 }}
              animate={{ width: `${(d.count / max) * 100}%` }}
              transition={{ duration: 0.6, ease: "easeOut", delay: i * 0.04 }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
