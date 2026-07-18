"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError, imageSrc } from "@/lib/api";
import type { AnalyticsOverview, ClothingItem } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatCard } from "@/components/StatCard";
import { BarList } from "@/components/analytics/BarList";
import { DonutChart } from "@/components/analytics/DonutChart";
import { ConnectionError } from "@/components/ConnectionError";
import { AnalyticsIcon, ImageIcon, ScanIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .analyticsOverview(5)
      .then((d) => alive && setData(d))
      .catch((e) => {
        if (!alive) return;
        setError(
          e instanceof ApiError ? e.message : "Failed to load analytics.",
        );
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  if (error) return <ConnectionError message={error} />;

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (!data || data.stats.total_items === 0) {
    return (
      <EmptyState
        icon={<AnalyticsIcon width={26} height={26} />}
        title="No analytics yet"
        description="Once you've scanned some clothes, you'll see usage insights and breakdowns here."
        action={
          <Link href="/scan">
            <Button>
              <ScanIcon width={18} height={18} /> Scan clothes
            </Button>
          </Link>
        }
      />
    );
  }

  const { stats } = data;

  return (
    <div className="space-y-8">
      {/* Headline stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard index={0} label="Total items" value={stats.total_items} />
        <StatCard
          index={1}
          label="Utilization"
          value={`${Math.round(stats.utilization_rate * 100)}%`}
          hint="Worn at least once"
        />
        <StatCard index={2} label="Total wears" value={stats.total_wears} />
        <StatCard
          index={3}
          label="Never worn"
          value={stats.never_worn_count}
          hint={`${stats.archived_items} archived`}
        />
      </div>

      {/* Breakdowns */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="mb-4 text-base font-semibold text-foreground">
            Color distribution
          </h3>
          <DonutChart data={data.color_breakdown} />
        </Card>

        <Card className="p-5">
          <h3 className="mb-4 text-base font-semibold text-foreground">
            By category
          </h3>
          <BarList
            data={data.category_breakdown.map((c) => ({
              label: c.label,
              count: c.count,
            }))}
          />
        </Card>

        <Card className="p-5">
          <h3 className="mb-4 text-base font-semibold text-foreground">
            By formality
          </h3>
          <BarList
            data={data.formality_breakdown.map((f) => ({
              label: f.label,
              count: f.count,
            }))}
          />
        </Card>

        <Card className="p-5">
          <h3 className="mb-4 text-base font-semibold text-foreground">
            Most worn
          </h3>
          <WornList items={data.most_worn} emptyLabel="Nothing worn yet." />
        </Card>
      </div>
    </div>
  );
}

function WornList({
  items,
  emptyLabel,
}: {
  items: ClothingItem[];
  emptyLabel: string;
}) {
  if (!items.length) {
    return <p className="py-6 text-center text-sm text-muted">{emptyLabel}</p>;
  }
  return (
    <ul className="space-y-2">
      {items.map((item) => {
        const src = imageSrc(item);
        return (
          <li key={item.id}>
            <Link
              href={`/wardrobe/${item.id}`}
              className="flex items-center gap-3 rounded-xl p-2 transition-colors hover:bg-surface-2"
            >
              <span className="h-11 w-11 shrink-0 overflow-hidden rounded-lg bg-surface-2">
                {src ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={src}
                    alt={item.name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="flex h-full w-full items-center justify-center text-muted">
                    <ImageIcon width={18} height={18} />
                  </span>
                )}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-foreground">
                  {item.name}
                </span>
                <span className="block text-xs text-muted">
                  {item.category.name}
                </span>
              </span>
              <span className="shrink-0 text-sm font-semibold text-brand">
                {item.wear_count}×
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
