"use client";

import { useCallback, useEffect, useState } from "react";

export interface Coords {
  latitude: number;
  longitude: number;
}

export type GeoStatus =
  | "idle" // haven't asked yet
  | "prompting" // waiting on the browser permission dialog / fix
  | "granted" // we have coordinates
  | "denied" // user blocked location
  | "unavailable" // no geolocation API or hardware error
  | "error"; // transient failure (timeout, etc.)

export interface GeolocationState {
  status: GeoStatus;
  coords: Coords | null;
  error: string | null;
  /** Trigger a (re)request for the current position. */
  request: () => void;
}

const STORAGE_KEY = "wardrobe:last-coords";

/** Read the last known coordinates so weather can render before a fresh fix. */
function readCached(): Coords | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Coords;
    if (typeof parsed.latitude === "number" && typeof parsed.longitude === "number") {
      return parsed;
    }
  } catch {
    /* ignore malformed cache */
  }
  return null;
}

/**
 * Request the user's location and expose it reactively.
 *
 * Automatically requests a fix on mount so weather intelligence kicks in
 * without a manual step; `request()` lets the UI retry after a denial. The
 * last successful fix is cached in localStorage to avoid a blank state on
 * subsequent visits.
 */
export function useGeolocation(autoRequest = true): GeolocationState {
  const [coords, setCoords] = useState<Coords | null>(null);
  const [status, setStatus] = useState<GeoStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(() => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setStatus("unavailable");
      setError("Location isn't supported on this device.");
      return;
    }
    setStatus("prompting");
    setError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const next: Coords = {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        };
        setCoords(next);
        setStatus("granted");
        try {
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch {
          /* storage may be unavailable (private mode) — non-fatal */
        }
      },
      (err) => {
        if (err.code === err.PERMISSION_DENIED) {
          setStatus("denied");
          setError("Location permission was denied.");
        } else if (err.code === err.POSITION_UNAVAILABLE) {
          setStatus("unavailable");
          setError("Your location is currently unavailable.");
        } else {
          setStatus("error");
          setError("Couldn't get your location. Try again.");
        }
      },
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 10 * 60_000 },
    );
  }, []);

  useEffect(() => {
    // Seed from cache so the UI isn't empty while we get a fresh fix.
    const cached = readCached();
    if (cached) setCoords(cached);
    if (autoRequest) request();
  }, [autoRequest, request]);

  return { status, coords, error, request };
}
