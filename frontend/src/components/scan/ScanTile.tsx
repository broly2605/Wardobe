"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { ClothingItem } from "@/lib/types";
import { imageSrc } from "@/lib/api";
import { humanize } from "@/lib/format";
import { Badge } from "@/components/ui/Badge";
import { ColorDots } from "@/components/ui/ColorDots";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { CheckIcon, CloseIcon, SparklesIcon } from "@/components/icons";

export type ScanState = "queued" | "uploading" | "processing" | "done" | "error";

export interface ScanEntry {
  id: string;
  file: File;
  previewUrl: string;
  progress: number;
  state: ScanState;
  item: ClothingItem | null;
  error: string | null;
}

export function ScanTile({ entry, index }: { entry: ScanEntry; index: number }) {
  const scan = entry.item?.ai_metadata?.scan;
  const displaySrc =
    entry.state === "done" && entry.item
      ? imageSrc(entry.item) ?? entry.previewUrl
      : entry.previewUrl;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.25, delay: Math.min(index * 0.04, 0.3) }}
      className="overflow-hidden rounded-2xl glass shadow-glass"
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-surface-2">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={displaySrc}
          alt={entry.file.name}
          className="h-full w-full object-cover"
        />

        {/* Processing overlay */}
        {(entry.state === "uploading" || entry.state === "processing") && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/45 backdrop-blur-sm">
            <span className="h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent" />
            <span className="text-xs font-medium text-white">
              {entry.state === "uploading"
                ? `Uploading ${entry.progress}%`
                : "Analyzing…"}
            </span>
          </div>
        )}

        {/* Status badge */}
        <div className="absolute right-2 top-2">
          {entry.state === "done" && (
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500 text-white shadow">
              <CheckIcon width={16} height={16} />
            </span>
          )}
          {entry.state === "error" && (
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-rose-500 text-white shadow">
              <CloseIcon width={16} height={16} />
            </span>
          )}
        </div>

        {scan?.background_removed && entry.state === "done" && (
          <div className="absolute left-2 top-2">
            <Badge tone="brand">
              <SparklesIcon width={12} height={12} /> BG removed
            </Badge>
          </div>
        )}
      </div>

      <div className="space-y-2 p-3">
        {entry.state === "error" ? (
          <>
            <p className="truncate text-sm font-medium text-foreground">
              {entry.file.name}
            </p>
            <p className="text-xs text-rose-500">{entry.error}</p>
          </>
        ) : entry.state === "done" && entry.item ? (
          <>
            <div className="flex items-center justify-between gap-2">
              <Link
                href={`/wardrobe/${entry.item.id}`}
                className="truncate text-sm font-medium text-foreground hover:text-brand"
              >
                {entry.item.name}
              </Link>
              <ColorDots colors={entry.item.colors} size={14} />
            </div>
            <div className="flex flex-wrap gap-1.5">
              <Badge>{entry.item.category.name}</Badge>
              {scan?.pattern && scan.pattern !== "solid" && (
                <Badge>{humanize(scan.pattern)}</Badge>
              )}
              {scan?.source === "cv_fallback" && (
                <Badge tone="warning">Heuristic</Badge>
              )}
            </div>
            <ConfidenceBar value={scan?.confidence} />
          </>
        ) : (
          <p className="truncate text-sm text-muted">{entry.file.name}</p>
        )}
      </div>
    </motion.div>
  );
}
