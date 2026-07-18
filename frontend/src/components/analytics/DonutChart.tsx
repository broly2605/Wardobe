"use client";

import { motion } from "framer-motion";
import type { ColorSlice } from "@/lib/types";

/** SVG donut for the color distribution. Falls back gracefully when empty. */
export function DonutChart({ data }: { data: ColorSlice[] }) {
  const total = data.reduce((sum, d) => sum + d.count, 0);
  if (total === 0) {
    return <p className="py-6 text-center text-sm text-muted">No colors yet.</p>;
  }

  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  const segments = data.map((d) => {
    const fraction = d.count / total;
    const seg = {
      hex: d.hex,
      label: d.label,
      count: d.count,
      dash: fraction * circumference,
      offset,
    };
    offset += fraction * circumference;
    return seg;
  });

  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row sm:justify-center">
      <svg width={160} height={160} viewBox="0 0 160 160" className="shrink-0">
        <g transform="rotate(-90 80 80)">
          {segments.map((s, i) => (
            <motion.circle
              key={i}
              cx={80}
              cy={80}
              r={radius}
              fill="none"
              stroke={s.hex}
              strokeWidth={20}
              strokeDasharray={`${s.dash} ${circumference - s.dash}`}
              strokeDashoffset={-s.offset}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.06 }}
            />
          ))}
        </g>
        <text
          x="80"
          y="76"
          textAnchor="middle"
          className="fill-foreground text-2xl font-semibold"
        >
          {total}
        </text>
        <text
          x="80"
          y="94"
          textAnchor="middle"
          className="fill-muted text-[10px] uppercase tracking-wide"
        >
          items
        </text>
      </svg>

      <ul className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm sm:grid-cols-1">
        {data.map((d) => (
          <li key={d.label} className="flex items-center gap-2">
            <span
              className="h-3 w-3 rounded-full border border-border"
              style={{ backgroundColor: d.hex }}
            />
            <span className="text-foreground">{d.label}</span>
            <span className="text-muted">{d.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
