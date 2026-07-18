"use client";

import { motion } from "framer-motion";
import type { Weather, WeatherCondition } from "@/lib/types";
import { humanize } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

/** Emoji glyph per simplified condition — keeps the card lightweight. */
const CONDITION_GLYPH: Record<WeatherCondition, string> = {
  clear: "☀️",
  cloudy: "⛅",
  rain: "🌧️",
  snow: "❄️",
  storm: "⛈️",
  fog: "🌫️",
};

function fmt(value: number | null | undefined, suffix: string): string {
  if (value == null) return "—";
  return `${Math.round(value)}${suffix}`;
}

/** Qualitative UV band for a quick read. */
function uvBand(uv: number | null): string {
  if (uv == null) return "—";
  if (uv < 3) return "Low";
  if (uv < 6) return "Moderate";
  if (uv < 8) return "High";
  if (uv < 11) return "Very high";
  return "Extreme";
}

interface Metric {
  label: string;
  value: string;
  hint?: string;
}

export function WeatherCard({ weather }: { weather: Weather }) {
  const feels = weather.feels_like_c ?? weather.temp_current_c;
  const current = weather.temp_current_c ?? (weather.temp_min_c + weather.temp_max_c) / 2;

  const metrics: Metric[] = [
    { label: "Temperature", value: fmt(current, "°C") },
    { label: "Feels Like", value: fmt(feels, "°C") },
    { label: "Humidity", value: fmt(weather.humidity_pct, "%") },
    { label: "Rain Chance", value: fmt(weather.precipitation_prob, "%") },
    { label: "Wind", value: fmt(weather.wind_kph, " km/h") },
    {
      label: "UV Index",
      value: fmt(weather.uv_index, ""),
      hint: uvBand(weather.uv_index),
    },
  ];

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center gap-4 border-b border-border p-5">
        <span className="text-4xl leading-none" aria-hidden>
          {CONDITION_GLYPH[weather.condition] ?? "🌡️"}
        </span>
        <div className="min-w-0">
          <p className="text-sm text-muted">
            {weather.label ? weather.label.replace(/_/g, " ") : "Current weather"}
          </p>
          <p className="truncate text-lg font-semibold">
            {humanize(weather.condition)} · {fmt(current, "°C")}
          </p>
        </div>
        <div className="ml-auto text-right text-xs text-muted">
          <p>H {fmt(weather.temp_max_c, "°")}</p>
          <p>L {fmt(weather.temp_min_c, "°")}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-px bg-border sm:grid-cols-6">
        {metrics.map((m, i) => (
          <motion.div
            key={m.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: Math.min(i * 0.04, 0.3) }}
            className="bg-surface px-3 py-4 text-center"
          >
            <p className="text-[11px] uppercase tracking-wide text-muted">
              {m.label}
            </p>
            <p className="mt-1 text-base font-semibold tabular-nums">{m.value}</p>
            {m.hint && <p className="text-[11px] text-muted">{m.hint}</p>}
          </motion.div>
        ))}
      </div>
    </Card>
  );
}

export function WeatherCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-center gap-4 border-b border-border p-5">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-4 w-40" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-px bg-border sm:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="space-y-2 bg-surface px-3 py-4">
            <Skeleton className="mx-auto h-2.5 w-14" />
            <Skeleton className="mx-auto h-4 w-10" />
          </div>
        ))}
      </div>
    </Card>
  );
}
