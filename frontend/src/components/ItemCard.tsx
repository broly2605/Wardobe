"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { ClothingItem } from "@/lib/types";
import { imageSrc } from "@/lib/api";
import { humanize } from "@/lib/format";
import { Badge } from "@/components/ui/Badge";
import { ColorDots } from "@/components/ui/ColorDots";
import { ImageIcon, SparklesIcon } from "@/components/icons";

export function ItemCard({
  item,
  index = 0,
}: {
  item: ClothingItem;
  index?: number;
}) {
  const src = imageSrc(item);
  const scanned = Boolean(item.ai_metadata?.scan);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: Math.min(index * 0.03, 0.3) }}
    >
      <Link
        href={`/wardrobe/${item.id}`}
        className="card-hover group block overflow-hidden rounded-2xl glass shadow-glass"
      >
        <div className="relative aspect-[3/4] overflow-hidden bg-surface-2">
          {src ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={src}
              alt={item.name}
              loading="lazy"
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-muted">
              <ImageIcon width={40} height={40} />
            </div>
          )}
          {scanned && (
            <div className="absolute left-2 top-2">
              <Badge tone="brand">
                <SparklesIcon width={12} height={12} /> AI
              </Badge>
            </div>
          )}
          {item.colors.length > 0 && (
            <div className="absolute bottom-2 right-2">
              <ColorDots colors={item.colors} size={16} />
            </div>
          )}
        </div>
        <div className="space-y-1 p-3">
          <p className="truncate font-medium text-foreground">{item.name}</p>
          <div className="flex items-center justify-between text-xs text-muted">
            <span className="truncate">{item.category.name}</span>
            <span className="shrink-0">{humanize(item.formality)}</span>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
