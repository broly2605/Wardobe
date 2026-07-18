"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { api, ApiError, imageSrc } from "@/lib/api";
import type { ClothingItem } from "@/lib/types";
import { humanize, formatDate, confidencePct } from "@/lib/format";
import { useToast } from "@/providers/ToastProvider";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { ConnectionError } from "@/components/ConnectionError";
import {
  ArrowLeftIcon,
  ImageIcon,
  SparklesIcon,
  TrashIcon,
} from "@/components/icons";
import { contrastText } from "@/lib/format";

export default function ItemDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const itemId = Number(id);
  const router = useRouter();
  const { success, error: toastError } = useToast();

  const [item, setItem] = useState<ClothingItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api
      .getItem(itemId)
      .then((it) => alive && setItem(it))
      .catch((e) => {
        if (!alive) return;
        setError(
          e instanceof ApiError ? e.message : "Failed to load this item.",
        );
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [itemId]);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.deleteItem(itemId);
      success("Item deleted");
      router.push("/wardrobe");
    } catch (e) {
      toastError(e instanceof ApiError ? e.message : "Failed to delete item.");
      setDeleting(false);
      setConfirmOpen(false);
    }
  };

  if (error) return <ConnectionError message={error} />;

  const scan = item?.ai_metadata?.scan;
  const src = item ? imageSrc(item) : null;

  return (
    <div className="space-y-6">
      <Link
        href="/wardrobe"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-muted transition-colors hover:text-foreground"
      >
        <ArrowLeftIcon width={16} height={16} /> Back to wardrobe
      </Link>

      {loading ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="aspect-square w-full" />
          <div className="space-y-4">
            <Skeleton className="h-8 w-2/3" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      ) : item ? (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Image */}
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <Card className="overflow-hidden">
              <div className="relative aspect-square bg-surface-2">
                {src ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={src}
                    alt={item.name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center text-muted">
                    <ImageIcon width={48} height={48} />
                  </div>
                )}
                {scan?.background_removed && (
                  <div className="absolute left-3 top-3">
                    <Badge tone="brand">
                      <SparklesIcon width={12} height={12} /> Background removed
                    </Badge>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Details */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.05 }}
            className="space-y-5"
          >
            <div>
              <div className="flex items-start justify-between gap-3">
                <h1 className="text-2xl font-semibold text-foreground">
                  {item.name}
                </h1>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => setConfirmOpen(true)}
                >
                  <TrashIcon width={16} height={16} /> Delete
                </Button>
              </div>
              <p className="mt-1 text-sm text-muted">
                {item.category.name}
                {item.brand ? ` · ${item.brand}` : ""}
              </p>
            </div>

            {/* Colors */}
            {item.colors.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
                  Colors
                </p>
                <div className="flex flex-wrap gap-2">
                  {item.colors.map((c) => (
                    <span
                      key={c.id}
                      className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium"
                      style={{
                        backgroundColor: c.hex,
                        color: contrastText(c.hex),
                      }}
                    >
                      {c.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Attribute grid */}
            <Card className="p-4">
              <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                <Attr label="Season" value={humanize(item.season)} />
                <Attr label="Formality" value={humanize(item.formality)} />
                <Attr label="Warmth" value={`${item.warmth}/10`} />
                <Attr label="Material" value={humanize(item.material)} />
                {scan?.pattern && (
                  <Attr label="Pattern" value={humanize(scan.pattern)} />
                )}
                {scan?.texture && (
                  <Attr label="Texture" value={humanize(scan.texture)} />
                )}
                {scan?.fit && <Attr label="Fit" value={humanize(scan.fit)} />}
                {scan?.sleeve_length && (
                  <Attr
                    label="Sleeves"
                    value={humanize(scan.sleeve_length)}
                  />
                )}
                {scan?.occasion && (
                  <Attr label="Occasion" value={humanize(scan.occasion)} />
                )}
                <Attr label="Times worn" value={String(item.wear_count)} />
              </dl>
            </Card>

            {/* Scan provenance */}
            {scan && (
              <Card className="p-4">
                <div className="mb-3 flex items-center justify-between">
                  <p className="flex items-center gap-1.5 text-sm font-medium text-foreground">
                    <SparklesIcon width={16} height={16} /> AI scan
                  </p>
                  <Badge tone={scan.source === "ai_vision" ? "success" : "warning"}>
                    {scan.source === "ai_vision"
                      ? "Vision model"
                      : "Heuristic"}
                  </Badge>
                </div>
                <ConfidenceBar value={scan.confidence} />
                {scan.detected_colors && scan.detected_colors.length > 0 && (
                  <div className="mt-3">
                    <p className="mb-1.5 text-xs text-muted">
                      Detected palette
                    </p>
                    <div className="flex gap-1.5">
                      {scan.detected_colors.map((dc, i) => (
                        <div
                          key={i}
                          title={`${dc.hex} · ${confidencePct(dc.weight)}`}
                          className="h-8 flex-1 rounded-lg border border-border"
                          style={{ backgroundColor: dc.hex }}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            )}

            {item.notes && (
              <Card className="p-4">
                <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted">
                  Notes
                </p>
                <p className="text-sm text-foreground">{item.notes}</p>
              </Card>
            )}

            <p className="text-xs text-muted">
              Added {formatDate(item.created_at)}
            </p>
          </motion.div>
        </div>
      ) : null}

      <ConfirmDialog
        open={confirmOpen}
        title="Delete this item?"
        description="This permanently removes the item and its image from your wardrobe. This can't be undone."
        confirmLabel="Delete"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  );
}

function Attr({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-0.5 font-medium text-foreground">{value}</dd>
    </div>
  );
}
