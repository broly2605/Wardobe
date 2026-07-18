"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { api, ApiError } from "@/lib/api";
import type { ScanStatus } from "@/lib/types";
import { useDropzone, type DropzoneResult } from "@/hooks/useDropzone";
import { useToast } from "@/providers/ToastProvider";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";
import { ScanTile, type ScanEntry } from "@/components/scan/ScanTile";
import {
  SparklesIcon,
  UploadIcon,
} from "@/components/icons";

let entryCounter = 0;

export default function ScanPage() {
  const { success, error: toastError } = useToast();
  const [entries, setEntries] = useState<ScanEntry[]>([]);
  const [scanning, setScanning] = useState(false);
  const [status, setStatus] = useState<ScanStatus | null>(null);
  const entriesRef = useRef<ScanEntry[]>([]);
  entriesRef.current = entries;

  useEffect(() => {
    api.scanStatus().then(setStatus).catch(() => setStatus(null));
  }, []);

  // Revoke object URLs on unmount to avoid leaks.
  useEffect(() => {
    return () => {
      entriesRef.current.forEach((e) => URL.revokeObjectURL(e.previewUrl));
    };
  }, []);

  const patch = useCallback((id: string, updates: Partial<ScanEntry>) => {
    setEntries((prev) =>
      prev.map((e) => (e.id === id ? { ...e, ...updates } : e)),
    );
  }, []);

  const handleFiles = useCallback(
    (result: DropzoneResult) => {
      for (const { file, reason } of result.rejected) {
        toastError(`${file.name}: ${reason}`);
      }
      if (!result.accepted.length) return;
      const newEntries: ScanEntry[] = result.accepted.map((file) => ({
        id: `e${++entryCounter}`,
        file,
        previewUrl: URL.createObjectURL(file),
        progress: 0,
        state: "queued",
        item: null,
        error: null,
      }));
      setEntries((prev) => [...newEntries, ...prev]);
    },
    [toastError],
  );

  const { isDragging, openFileDialog, dropzoneProps, inputProps } =
    useDropzone(handleFiles);

  const runScan = useCallback(async () => {
    const queued = entriesRef.current.filter((e) => e.state === "queued");
    if (!queued.length) return;
    setScanning(true);
    let created = 0;

    // Sequential upload keeps per-file progress accurate and avoids hammering
    // the CV pipeline (rembg is CPU-bound).
    for (const entry of queued) {
      patch(entry.id, { state: "uploading", progress: 0 });
      try {
        const res = await api.scanOne(entry.file, (pct) => {
          patch(entry.id, {
            progress: pct,
            state: pct >= 100 ? "processing" : "uploading",
          });
        });
        if (res.ok && res.item) {
          created += 1;
          patch(entry.id, { state: "done", item: res.item, progress: 100 });
        } else {
          patch(entry.id, {
            state: "error",
            error: res.error ?? "Scan failed",
          });
        }
      } catch (e) {
        patch(entry.id, {
          state: "error",
          error: e instanceof ApiError ? e.message : "Upload failed",
        });
      }
    }

    setScanning(false);
    if (created > 0) success(`Added ${created} item${created === 1 ? "" : "s"} to your wardrobe`);
  }, [patch, success]);

  const clearFinished = useCallback(() => {
    setEntries((prev) => {
      prev
        .filter((e) => e.state === "done" || e.state === "error")
        .forEach((e) => URL.revokeObjectURL(e.previewUrl));
      return prev.filter((e) => e.state !== "done" && e.state !== "error");
    });
  }, []);

  const queuedCount = entries.filter((e) => e.state === "queued").length;
  const doneCount = entries.filter((e) => e.state === "done").length;

  return (
    <div className="space-y-6">
      {/* Status strip */}
      {status && (
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <Badge tone={status.ai_enabled ? "success" : "default"}>
            <SparklesIcon width={12} height={12} />
            {status.ai_enabled ? "AI vision on" : "Heuristic mode"}
          </Badge>
          {status.background_removal_available && (
            <Badge tone="brand">Background removal ready</Badge>
          )}
          <span className="text-muted">
            Detects: {status.detected_attributes.slice(0, 5).map((a) => a.replace(/_/g, " ")).join(", ")}
            {status.detected_attributes.length > 5 ? "…" : ""}
          </span>
        </div>
      )}

      {/* Dropzone */}
      <div
        {...dropzoneProps}
        onClick={openFileDialog}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            openFileDialog();
          }
        }}
        className={cn(
          "group relative flex cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed px-6 py-14 text-center transition-all duration-200",
          isDragging
            ? "border-brand bg-brand-soft scale-[1.01]"
            : "border-border glass hover:border-brand/50",
        )}
      >
        <input {...inputProps} />
        <motion.div
          animate={isDragging ? { y: -6, scale: 1.08 } : { y: 0, scale: 1 }}
          className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-brand text-white shadow-glass-lg"
        >
          <UploadIcon width={30} height={30} />
        </motion.div>
        <p className="text-lg font-semibold text-foreground">
          {isDragging ? "Drop to scan" : "Drag & drop clothing photos"}
        </p>
        <p className="mt-1 text-sm text-muted">
          or <span className="font-medium text-brand">browse files</span> ·
          JPEG, PNG, WebP up to 10MB
        </p>
      </div>

      {/* Action bar */}
      <AnimatePresence>
        {entries.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <Card className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div className="text-sm text-muted">
                <span className="font-medium text-foreground">
                  {entries.length}
                </span>{" "}
                in queue · {doneCount} done
              </div>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  onClick={clearFinished}
                  disabled={scanning || doneCount === 0}
                >
                  Clear finished
                </Button>
                <Button
                  onClick={runScan}
                  loading={scanning}
                  disabled={queuedCount === 0}
                >
                  <SparklesIcon width={18} height={18} />
                  {scanning
                    ? "Scanning…"
                    : `Scan ${queuedCount || ""} ${
                        queuedCount === 1 ? "photo" : "photos"
                      }`.trim()}
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <AnimatePresence mode="popLayout">
          {entries.map((entry, i) => (
            <ScanTile key={entry.id} entry={entry} index={i} />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
