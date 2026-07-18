// TypeScript mirrors of the backend Pydantic schemas. Keep in sync with
// backend/app/schemas.

export type Season =
  | "spring"
  | "summer"
  | "autumn"
  | "winter"
  | "all_season";

export type Formality =
  | "lounge"
  | "casual"
  | "smart_casual"
  | "business"
  | "formal";

export interface Category {
  id: number;
  slug: string;
  name: string;
  description: string | null;
  default_warmth: number;
  sort_order: number;
}

export interface Color {
  id: number;
  name: string;
  hex: string;
  family: string | null;
}

export interface Tag {
  id: number;
  name: string;
}

/** Attributes the scanner writes into `ai_metadata.scan`. */
export interface ScanMetadata {
  pattern?: string;
  texture?: string;
  sleeve_length?: string;
  fit?: string;
  occasion?: string;
  material?: string | null;
  season?: string;
  formality?: string;
  brand?: string | null;
  confidence?: number;
  source?: "ai_vision" | "cv_fallback";
  background_removed?: boolean;
  detected_colors?: { hex: string; weight: number }[];
}

export interface ClothingItem {
  id: number;
  name: string;
  category: Category;
  brand: string | null;
  size: string | null;
  material: string | null;
  notes: string | null;
  image_path: string | null;
  image_url: string | null;
  season: Season;
  formality: Formality;
  warmth: number;
  is_archived: boolean;
  wear_count: number;
  last_worn_at: string | null;
  purchase_date: string | null;
  ai_metadata: { scan?: ScanMetadata } | null;
  colors: Color[];
  tags: Tag[];
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// --- Weather & recommendations ---
export type WeatherCondition =
  | "clear"
  | "cloudy"
  | "rain"
  | "snow"
  | "storm"
  | "fog";

export interface Weather {
  id: number;
  latitude: number;
  longitude: number;
  for_date: string;
  label: string | null;
  condition: WeatherCondition;
  temp_min_c: number;
  temp_max_c: number;
  temp_current_c: number | null;
  feels_like_c: number | null;
  humidity_pct: number | null;
  precipitation_prob: number | null;
  wind_kph: number | null;
  uv_index: number | null;
}

export type Occasion =
  | "everyday"
  | "work"
  | "workout"
  | "date"
  | "party"
  | "formal_event"
  | "travel"
  | "outdoor";

export interface RecommendationRequest {
  occasion?: Occasion;
  latitude?: number | null;
  longitude?: number | null;
  prompt?: string | null;
}

export interface RecommendedOutfit {
  items: ClothingItem[];
  rationale: string;
  used_ai: boolean;
  occasion: Occasion;
  weather: Weather | null;
}

// --- Scanner ---
export interface ScannedItemResult {
  filename: string;
  ok: boolean;
  item: ClothingItem | null;
  error: string | null;
}

export interface BatchScanResponse {
  scanned: number;
  created: number;
  results: ScannedItemResult[];
}

export interface ScanStatus {
  ai_enabled: boolean;
  background_removal_available: boolean;
  detected_attributes: string[];
}

// --- Analytics ---
export interface CountByLabel {
  label: string;
  count: number;
}

export interface ColorSlice {
  label: string;
  hex: string;
  count: number;
}

export interface WardrobeStats {
  total_items: number;
  total_outfits: number;
  total_wears: number;
  archived_items: number;
  utilization_rate: number;
  never_worn_count: number;
}

export interface AnalyticsOverview {
  stats: WardrobeStats;
  category_breakdown: CountByLabel[];
  color_breakdown: ColorSlice[];
  formality_breakdown: CountByLabel[];
  most_worn: ClothingItem[];
  least_worn: ClothingItem[];
}

// --- App status (settings) ---
export interface AppStatus {
  ai_enabled: boolean;
  ai_model: string | null;
  weather_provider: string;
  app_env: string;
}
