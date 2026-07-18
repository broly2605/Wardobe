// Small display-formatting helpers shared across pages.

/** Turn an enum-ish value ("smart_casual") into a label ("Smart Casual"). */
export function humanize(value: string | null | undefined): string {
  if (!value) return "—";
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Format a 0..1 confidence as a percentage string. */
export function confidencePct(value: number | null | undefined): string {
  if (value == null) return "—";
  const pct = value <= 1 ? value * 100 : value;
  return `${Math.round(pct)}%`;
}

/** A qualitative label + color band for a confidence value. */
export function confidenceBand(value: number | null | undefined): {
  label: string;
  tone: "high" | "medium" | "low";
} {
  const v = value == null ? 0 : value <= 1 ? value : value / 100;
  if (v >= 0.75) return { label: "High", tone: "high" };
  if (v >= 0.45) return { label: "Medium", tone: "medium" };
  return { label: "Low", tone: "low" };
}

/** Format an ISO date string as a short readable date. */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Relative "time ago" for recent-activity displays. */
export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const secs = Math.max(1, Math.floor((Date.now() - then) / 1000));
  const units: [number, string][] = [
    [60, "second"],
    [60, "minute"],
    [24, "hour"],
    [7, "day"],
    [4.34524, "week"],
    [12, "month"],
    [Number.POSITIVE_INFINITY, "year"],
  ];
  let value = secs;
  let unit = "second";
  for (const [size, name] of units) {
    if (value < size) {
      unit = name;
      break;
    }
    value = value / size;
    unit = name;
  }
  const rounded = Math.floor(value);
  return `${rounded} ${unit}${rounded === 1 ? "" : "s"} ago`;
}

/** Pick readable text color (black/white) for a given hex background. */
export function contrastText(hex: string): string {
  const h = hex.replace("#", "");
  const full =
    h.length === 3
      ? h
          .split("")
          .map((c) => c + c)
          .join("")
      : h;
  const r = parseInt(full.slice(0, 2), 16) || 0;
  const g = parseInt(full.slice(2, 4), 16) || 0;
  const b = parseInt(full.slice(4, 6), 16) || 0;
  // Perceived luminance.
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.6 ? "#111120" : "#ffffff";
}
