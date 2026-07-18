"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { api, ApiError } from "@/lib/api";
import type { AnalyticsOverview, ClothingItem } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatCard } from "@/components/StatCard";
import { ItemCard } from "@/components/ItemCard";
import {
  ScanIcon,
  SparklesIcon,
  WardrobeIcon,
  ShirtIcon,
} from "@/components/icons";
import { ConnectionError } from "@/components/ConnectionError";

export default function DashboardPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [recent, setRecent] = useState<ClothingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [ov, items] = await Promise.all([
          api.analyticsOverview(4),
          api.listItems({ limit: 8 }),
        ]);
        if (!alive) return;
        setOverview(ov);
        setRecent(items.items);
      } catch (e) {
        if (!alive) return;
        setError(e instanceof ApiError ? e.message : "Failed to load dashboard.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (error) return <ConnectionError message={error} />;

  const stats = overview?.stats;
  const utilization = stats ? Math.round(stats.utilization_rate * 100) : 0;

  return (
    <div className="space-y-8">
      {/* Hero / CTA */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <Card className="relative overflow-hidden p-6 sm:p-8">
          <div className="pointer-events-none absolute -right-16 -top-16 h-52 w-52 rounded-full bg-gradient-brand opacity-20 blur-3xl" />
          <div className="relative flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="max-w-lg">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-brand-soft px-3 py-1 text-xs font-medium text-brand">
                <SparklesIcon width={14} height={14} /> AI-powered
              </div>
              <h2 className="text-2xl font-semibold text-foreground sm:text-3xl">
                Digitize your closet in seconds
              </h2>
              <p className="mt-2 text-sm text-muted">
                Drop in photos and the scanner detects category, colors,
                material, and more — then files each piece into your wardrobe
                automatically.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link href="/scan">
                  <Button size="lg">
                    <ScanIcon width={18} height={18} /> Start scanning
                  </Button>
                </Link>
                <Link href="/wardrobe">
                  <Button size="lg" variant="secondary">
                    <WardrobeIcon width={18} height={18} /> View wardrobe
                  </Button>
                </Link>
              </div>
            </div>
            <div className="hidden shrink-0 sm:block">
              <div className="flex h-28 w-28 items-center justify-center rounded-3xl bg-gradient-brand text-white shadow-glass-lg">
                <ShirtIcon width={56} height={56} />
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Stats */}
      <section>
        {loading ? (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-28" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard
              index={0}
              label="Total items"
              value={stats?.total_items ?? 0}
              icon={<WardrobeIcon width={18} height={18} />}
            />
            <StatCard
              index={1}
              label="Total wears"
              value={stats?.total_wears ?? 0}
              hint="Across all items"
            />
            <StatCard
              index={2}
              label="Utilization"
              value={`${utilization}%`}
              hint={`${stats?.never_worn_count ?? 0} never worn`}
            />
            <StatCard
              index={3}
              label="Outfits"
              value={stats?.total_outfits ?? 0}
              hint="Saved combinations"
            />
          </div>
        )}
      </section>

      {/* Recent additions */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">
            Recent additions
          </h3>
          <Link
            href="/wardrobe"
            className="text-sm font-medium text-brand hover:underline"
          >
            See all
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[3/4]" />
            ))}
          </div>
        ) : recent.length === 0 ? (
          <EmptyState
            icon={<ScanIcon width={26} height={26} />}
            title="Your wardrobe is empty"
            description="Scan your first clothing photos to get started. The AI will tag everything for you."
            action={
              <Link href="/scan">
                <Button>
                  <ScanIcon width={18} height={18} /> Scan clothes
                </Button>
              </Link>
            }
          />
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {recent.map((item, i) => (
              <ItemCard key={item.id} item={item} index={i} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
