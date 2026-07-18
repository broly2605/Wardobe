"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { api, ApiError } from "@/lib/api";
import type { Occasion, RecommendedOutfit, Weather } from "@/lib/types";
import { useGeolocation } from "@/hooks/useGeolocation";
import { useToast } from "@/providers/ToastProvider";
import { humanize } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import { EmptyState } from "@/components/ui/EmptyState";
import { ItemCard } from "@/components/ItemCard";
import { WeatherCard, WeatherCardSkeleton } from "@/components/WeatherCard";
import { SparklesIcon } from "@/components/icons";

const OCCASIONS: Occasion[] = [
  "everyday",
  "work",
  "workout",
  "date",
  "party",
  "formal_event",
  "travel",
  "outdoor",
];

export default function StylePage() {
  const { success, error: toastError } = useToast();
  const { status: geoStatus, coords, error: geoError, request } = useGeolocation();

  const [occasion, setOccasion] = useState<Occasion>("everyday");
  const [prompt, setPrompt] = useState("");
  const [weather, setWeather] = useState<Weather | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [outfit, setOutfit] = useState<RecommendedOutfit | null>(null);
  const [generating, setGenerating] = useState(false);

  // Fetch weather as soon as we have a location fix. This gives the user an
  // immediate read on conditions even before they generate an outfit.
  useEffect(() => {
    if (!coords) return;
    let alive = true;
    setWeatherLoading(true);
    api
      .getWeather(coords.latitude, coords.longitude)
      .then((w) => alive && setWeather(w))
      .catch(() => alive && setWeather(null))
      .finally(() => alive && setWeatherLoading(false));
    return () => {
      alive = false;
    };
  }, [coords]);

  const generate = useCallback(async () => {
    setGenerating(true);
    try {
      const result = await api.recommend({
        occasion,
        latitude: coords?.latitude ?? null,
        longitude: coords?.longitude ?? null,
        prompt: prompt.trim() || null,
      });
      setOutfit(result);
      // The recommendation echoes back the weather it used — keep the card in
      // sync so what's shown always matches what shaped the suggestion.
      if (result.weather) setWeather(result.weather);
      if (!result.items.length) {
        toastError("Not enough items to build an outfit yet.");
      } else {
        success(result.used_ai ? "Styled with AI" : "Styled for you");
      }
    } catch (e) {
      toastError(e instanceof ApiError ? e.message : "Couldn't generate an outfit.");
    } finally {
      setGenerating(false);
    }
  }, [occasion, coords, prompt, success, toastError]);

  return (
    <div className="space-y-6">
      {/* Location status */}
      <LocationBanner
        status={geoStatus}
        error={geoError}
        onRetry={request}
      />

      {/* Weather intelligence */}
      {weatherLoading && !weather ? (
        <WeatherCardSkeleton />
      ) : weather ? (
        <WeatherCard weather={weather} />
      ) : null}

      {/* Controls */}
      <Card className="flex flex-col gap-4 p-5 sm:flex-row sm:items-end">
        <label className="flex flex-1 flex-col gap-1.5">
          <span className="text-xs font-medium uppercase tracking-wide text-muted">
            Occasion
          </span>
          <Select
            value={occasion}
            onChange={(e) => setOccasion(e.target.value as Occasion)}
          >
            {OCCASIONS.map((o) => (
              <option key={o} value={o}>
                {humanize(o)}
              </option>
            ))}
          </Select>
        </label>

        <label className="flex flex-[2] flex-col gap-1.5">
          <span className="text-xs font-medium uppercase tracking-wide text-muted">
            Any preferences? (optional)
          </span>
          <input
            type="text"
            value={prompt}
            maxLength={500}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. something bold, keep it minimal"
            className="h-10 rounded-xl border border-border bg-surface px-3 text-sm text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
          />
        </label>

        <Button onClick={generate} loading={generating} size="lg">
          <SparklesIcon width={18} height={18} />
          {generating ? "Styling…" : "Style me"}
        </Button>
      </Card>

      {/* Result */}
      {outfit && outfit.items.length > 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="brand">
              <SparklesIcon width={12} height={12} />
              {outfit.used_ai ? "AI stylist" : "Rule-based"}
            </Badge>
            <Badge>{humanize(outfit.occasion)}</Badge>
            {weather && (
              <Badge tone="default">
                Weather-aware · {humanize(weather.condition)}
              </Badge>
            )}
          </div>

          <Card className="p-5">
            <p className="text-sm leading-relaxed text-foreground">
              {outfit.rationale}
            </p>
          </Card>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {outfit.items.map((item, i) => (
              <ItemCard key={item.id} item={item} index={i} />
            ))}
          </div>
        </motion.div>
      ) : (
        !generating && (
          <EmptyState
            icon={<SparklesIcon width={24} height={24} />}
            title="Ready when you are"
            description="Pick an occasion and I'll build a weather-appropriate outfit from your wardrobe."
          />
        )
      )}
    </div>
  );
}

function LocationBanner({
  status,
  error,
  onRetry,
}: {
  status: ReturnType<typeof useGeolocation>["status"];
  error: string | null;
  onRetry: () => void;
}) {
  if (status === "granted" || status === "idle") return null;

  const prompting = status === "prompting";
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-border glass px-4 py-3 text-sm">
      <span className="text-muted">
        {prompting
          ? "Requesting your location for weather-aware styling…"
          : error ??
            "Location is off. Outfits will still work, but without weather."}
      </span>
      {!prompting && (
        <Button variant="secondary" size="sm" className="ml-auto" onClick={onRetry}>
          Enable location
        </Button>
      )}
    </div>
  );
}
