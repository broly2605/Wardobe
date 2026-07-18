// Typed client for the Wardrobe backend.
//
// Requests use relative paths ("/api/...") which Next rewrites to the backend
// (see next.config.ts), so the browser stays same-origin. Image URLs returned
// by the API ("/uploads/...") are likewise proxied.

import type {
  AnalyticsOverview,
  AppStatus,
  BatchScanResponse,
  Category,
  ClothingItem,
  Color,
  Page,
  RecommendationRequest,
  RecommendedOutfit,
  ScanStatus,
  ScannedItemResult,
  Season,
  Formality,
  Weather,
} from "./types";

const BASE = ""; // same-origin; Next proxies /api and /uploads

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Is the backend running?");
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      /* keep default */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Resolve an image path/URL from the API to something the browser can load. */
export function imageSrc(item: {
  image_url: string | null;
  image_path: string | null;
}): string | null {
  if (item.image_url) return item.image_url;
  if (item.image_path) return `/uploads/${item.image_path}`;
  return null;
}

export interface ListItemsParams {
  category_id?: number;
  season?: Season;
  formality?: Formality;
  search?: string;
  include_archived?: boolean;
  limit?: number;
  offset?: number;
}

export const api = {
  // --- Items ---
  listItems(params: ListItemsParams = {}): Promise<Page<ClothingItem>> {
    const q = new URLSearchParams();
    if (params.category_id != null) q.set("category_id", String(params.category_id));
    if (params.season) q.set("season", params.season);
    if (params.formality) q.set("formality", params.formality);
    if (params.search) q.set("search", params.search);
    if (params.include_archived) q.set("include_archived", "true");
    q.set("limit", String(params.limit ?? 60));
    q.set("offset", String(params.offset ?? 0));
    return request<Page<ClothingItem>>(`/api/items?${q.toString()}`);
  },

  getItem(id: number): Promise<ClothingItem> {
    return request<ClothingItem>(`/api/items/${id}`);
  },

  deleteItem(id: number): Promise<{ detail: string }> {
    return request<{ detail: string }>(`/api/items/${id}`, { method: "DELETE" });
  },

  // --- Reference ---
  listCategories(): Promise<Category[]> {
    return request<Category[]>(`/api/categories`);
  },
  listColors(): Promise<Color[]> {
    return request<Color[]>(`/api/colors`);
  },

  // --- Analytics ---
  analyticsOverview(topN = 5): Promise<AnalyticsOverview> {
    return request<AnalyticsOverview>(`/api/analytics/overview?top_n=${topN}`);
  },

  // --- Weather ---
  getWeather(latitude: number, longitude: number): Promise<Weather> {
    const q = new URLSearchParams({
      latitude: String(latitude),
      longitude: String(longitude),
    });
    return request<Weather>(`/api/weather?${q.toString()}`);
  },

  // --- Recommendations ---
  recommend(payload: RecommendationRequest = {}): Promise<RecommendedOutfit> {
    return request<RecommendedOutfit>(`/api/recommendations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  // --- Scanner ---
  scanStatus(): Promise<ScanStatus> {
    return request<ScanStatus>(`/api/scan/status`);
  },
  appStatus(): Promise<AppStatus> {
    return request<AppStatus>(`/api/settings/status`);
  },

  /**
   * Scan a single image with upload-progress reporting. Uses XHR because the
   * fetch API can't report upload progress in browsers yet.
   */
  scanOne(
    file: File,
    onProgress?: (pct: number) => void,
  ): Promise<ScannedItemResult> {
    return uploadWithProgress<ScannedItemResult>(
      "/api/scan",
      [["file", file]],
      onProgress,
    );
  },

  scanBatch(
    files: File[],
    onProgress?: (pct: number) => void,
  ): Promise<BatchScanResponse> {
    return uploadWithProgress<BatchScanResponse>(
      "/api/scan/batch",
      files.map((f) => ["files", f] as [string, File]),
      onProgress,
    );
  },
};

function uploadWithProgress<T>(
  path: string,
  parts: [string, File][],
  onProgress?: (pct: number) => void,
): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const form = new FormData();
    for (const [key, file] of parts) form.append(key, file, file.name);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE}${path}`);
    xhr.responseType = "json";

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress?.(100);
        resolve(xhr.response as T);
      } else {
        const detail =
          (xhr.response && (xhr.response.detail as string)) ||
          `Upload failed (${xhr.status})`;
        reject(new ApiError(xhr.status, detail));
      }
    };
    xhr.onerror = () =>
      reject(new ApiError(0, "Network error during upload."));
    xhr.send(form);
  });
}
