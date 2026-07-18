"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api, ApiError, type ListItemsParams } from "@/lib/api";
import type {
  Category,
  ClothingItem,
  Formality,
  Season,
} from "@/lib/types";
import { ItemCard } from "@/components/ItemCard";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { SearchInput } from "@/components/ui/SearchInput";
import { CardGridSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ConnectionError } from "@/components/ConnectionError";
import { ScanIcon, WardrobeIcon } from "@/components/icons";

const SEASONS: Season[] = ["spring", "summer", "autumn", "winter", "all_season"];
const FORMALITIES: Formality[] = [
  "lounge",
  "casual",
  "smart_casual",
  "business",
  "formal",
];

const PAGE_SIZE = 24;

export default function WardrobePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [items, setItems] = useState<ClothingItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [season, setSeason] = useState<Season | "">("");
  const [formality, setFormality] = useState<Formality | "">("");

  useEffect(() => {
    api.listCategories().then(setCategories).catch(() => {});
  }, []);

  // Debounce the search box.
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  const params = useMemo<ListItemsParams>(
    () => ({
      category_id: categoryId === "" ? undefined : categoryId,
      season: season === "" ? undefined : season,
      formality: formality === "" ? undefined : formality,
      search: debouncedSearch || undefined,
      limit: PAGE_SIZE,
    }),
    [categoryId, season, formality, debouncedSearch],
  );

  // Reload from the top whenever filters change.
  useEffect(() => {
    let alive = true;
    setLoading(true);
    setOffset(0);
    api
      .listItems({ ...params, offset: 0 })
      .then((page) => {
        if (!alive) return;
        setItems(page.items);
        setTotal(page.total);
        setError(null);
      })
      .catch((e) => {
        if (!alive) return;
        setError(e instanceof ApiError ? e.message : "Failed to load items.");
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [params]);

  const loadMore = useCallback(async () => {
    const nextOffset = offset + PAGE_SIZE;
    setLoadingMore(true);
    try {
      const page = await api.listItems({ ...params, offset: nextOffset });
      setItems((prev) => [...prev, ...page.items]);
      setOffset(nextOffset);
      setTotal(page.total);
    } catch {
      /* surfaced elsewhere */
    } finally {
      setLoadingMore(false);
    }
  }, [offset, params]);

  const hasFilters =
    categoryId !== "" || season !== "" || formality !== "" || debouncedSearch !== "";

  const resetFilters = () => {
    setSearch("");
    setCategoryId("");
    setSeason("");
    setFormality("");
  };

  if (error) return <ConnectionError message={error} />;

  const canLoadMore = items.length < total;

  return (
    <div className="space-y-6">
      {/* Filter bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search by name…"
        />
        <div className="flex flex-wrap gap-2">
          <Select
            value={categoryId}
            onChange={(e) =>
              setCategoryId(e.target.value ? Number(e.target.value) : "")
            }
            aria-label="Filter by category"
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
          <Select
            value={season}
            onChange={(e) => setSeason(e.target.value as Season | "")}
            aria-label="Filter by season"
          >
            <option value="">Any season</option>
            {SEASONS.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </Select>
          <Select
            value={formality}
            onChange={(e) => setFormality(e.target.value as Formality | "")}
            aria-label="Filter by formality"
          >
            <option value="">Any formality</option>
            {FORMALITIES.map((f) => (
              <option key={f} value={f}>
                {f.replace(/_/g, " ")}
              </option>
            ))}
          </Select>
          {hasFilters && (
            <Button variant="ghost" onClick={resetFilters}>
              Reset
            </Button>
          )}
        </div>
      </div>

      {/* Count */}
      {!loading && (
        <p className="text-sm text-muted">
          {total} item{total === 1 ? "" : "s"}
          {hasFilters ? " match your filters" : " in your wardrobe"}
        </p>
      )}

      {/* Grid */}
      {loading ? (
        <CardGridSkeleton count={8} />
      ) : items.length === 0 ? (
        hasFilters ? (
          <EmptyState
            icon={<WardrobeIcon width={26} height={26} />}
            title="No matches"
            description="Try loosening or resetting your filters."
            action={<Button onClick={resetFilters}>Reset filters</Button>}
          />
        ) : (
          <EmptyState
            icon={<ScanIcon width={26} height={26} />}
            title="No items yet"
            description="Scan some clothing photos to fill up your wardrobe."
            action={
              <Link href="/scan">
                <Button>
                  <ScanIcon width={18} height={18} /> Scan clothes
                </Button>
              </Link>
            }
          />
        )
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {items.map((item, i) => (
              <ItemCard key={item.id} item={item} index={i} />
            ))}
          </div>
          {canLoadMore && (
            <div className="flex justify-center pt-2">
              <Button
                variant="secondary"
                onClick={loadMore}
                loading={loadingMore}
              >
                Load more
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
