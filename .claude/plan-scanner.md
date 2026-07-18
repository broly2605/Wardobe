# AI Wardrobe Scanner + Complete Frontend — Implementation Plan

## Goal
1. Backend: an AI Wardrobe Scanner that takes uploaded clothing images (single / multiple /
   drag-drop), auto-detects every requested attribute with computer vision, removes the
   background when needed, and auto-creates fully-tagged wardrobe items (zero manual tagging).
2. Frontend: a complete, production-ready Next.js 15 app (not a scaffold) — full layout,
   all pages, components, hooks, animations, loading/error/empty states, toasts, dark/light,
   glassmorphism, responsive — that feels like a finished premium product.

## Constraints honored
- Build on existing backend; do NOT rewrite working code or change existing API routes/schema
  unless required. Reuse repo→service→route pattern, `serialize_item`, `ai_metadata` JSONB.
- Offline-first: works with NO OpenAI key (deterministic CV color extraction + heuristics).
- rembg for accurate background removal, with graceful fallback if the wheel won't install.

---

## PART A — BACKEND

### A1. Enums (additive) — `app/models/enums.py`
Add string enums `Pattern`, `Texture`, `SleeveLength`, `Fit` for validating scan output.
No DB columns → no migration.

### A2. Attribute → storage mapping (NO migration)
- Category → `category_id` (resolve detected slug → Category; default fallback).
- Primary/Secondary Color → `colors` M2M (RGB-nearest to seed palette, ordered primary-first).
- Material → `material`; Season → `season`; Formality → `formality`; Brand → `brand`.
- Pattern, Texture, Sleeve Length, Fit, Occasion, confidence, source, bg-removed flag,
  raw detected color names/hexes → `ai_metadata.scan.*` (JSONB, already exists).

### A3. Background removal — `app/services/background.py` (new)
`remove_background(image_bytes) -> (bytes, removed: bool)`. Lazy-import `rembg`; true cutout
composited on white when available; else PIL near-uniform-edge heuristic; else original
(`removed=False`). Only runs when background looks non-trivial ("remove if necessary").
Module-level `background_removal_available()` capability probe.

### A4. Color CV — extend `app/services/ai/color_theory.py`
- `dominant_colors(image_bytes, k=3)` — PIL downscale+quantize, ignore near-white/transparent.
- `nearest_color_name(rgb, palette)` — Euclidean RGB distance to seed `Color` rows.
Deterministic Primary/Secondary color from pixels — real CV, always offline-capable.

### A5. Scanner engine — `app/services/ai/scanner.py` (new)
`WardrobeScanner(provider)`, `async detect(image_bytes) -> ScanDetection`:
1. CV dominant colors (always).
2. If `provider.enabled`: vision prompt requesting all attributes as JSON (category, colors,
   pattern, material, texture, season, sleeve_length, fit, formality, occasion, brand,
   suggested_name, confidence) via existing `provider.describe_image`.
3. Merge: vision fills semantic fields; CV mapping authoritative for primary/secondary color;
   missing → heuristic defaults + `source="cv_fallback"`. Validate enum-like fields.

### A6. Storage — `app/services/storage.py`
Add `save_processed_image(image_bytes) -> relative_path` (write processed JPEG). Existing
`save_image` untouched.

### A7. Scan orchestration — `app/services/scan_service.py` (new)
`ScanService(items, colors, categories, scanner)`:
- `scan_one(file) -> ClothingItem`: validate → optional bg removal → detect → resolve
  category/colors → build item with detected columns + `ai_metadata={"scan":{...}}` → add →
  persist processed image → re-fetch (existing `get`) for serialization.
- `scan_many(files) -> list[result]`: per-file isolation so one bad image can't fail a batch.

### A8. Schemas — `app/schemas/scan.py` (new)
`ScanDetection`, `ScannedItemResult {filename, ok, item: ClothingItemRead|None, error}`,
`BatchScanResponse {scanned, created, results[]}`, `ScanStatus`.

### A9. Route — `app/api/routes/scan.py` (new) + register in `app/api/router.py`
- `POST /api/scan` — single → `ScannedItemResult`.
- `POST /api/scan/batch` — multiple → `BatchScanResponse`.
- `GET /api/scan/status` — ai_enabled, background_removal_available, detected attribute list.
- `ImageValidationError` → 400; never 503 (always degrades to CV). Flag: no auth (matches
  app's no-auth constraint).

### A10. deps.py — `get_scan_service` + `ScanServiceDep`.
### A11. requirements.txt — add `rembg`, `onnxruntime` (defensive; fallback if no wheel).

---

## PART B — FRONTEND (complete, production-ready)

Stack: Next.js 15 App Router, React, TypeScript, TailwindCSS, Framer Motion. Talks to backend
via `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`).

### B1. Project config
`frontend/`: package.json, tsconfig.json, next.config.ts, tailwind.config.ts,
postcss.config.mjs, .env.local.example, .gitignore, src/app/globals.css (design tokens,
glass utilities, light/dark CSS vars).

### B2. Core lib / infrastructure
- `src/lib/types.ts` — TS types mirroring backend schemas (ClothingItem, Category, Color,
  ScanResult, Page<T>, analytics, etc.).
- `src/lib/api.ts` — typed fetch client (items list/get, scan single+batch with upload
  progress via XHR, reference data, analytics, scan status, delete). Absolute image URLs.
- `src/lib/format.ts` — label/formatting helpers (enum → Title Case, confidence %).
- `src/hooks/useTheme.ts` — dark/light with localStorage + system preference, no-flash script.
- `src/hooks/useToast.ts` + `src/providers/ToastProvider.tsx` — toast queue.
- `src/hooks/useMediaQuery.ts` — responsive helpers.

### B3. Layout & shell
- `src/app/layout.tsx` — html/body, ThemeProvider, ToastProvider, AppShell, no-flash theme script.
- `components/layout/AppShell.tsx` — grid: Sidebar + TopBar + main; mobile drawer.
- `components/layout/Sidebar.tsx` — nav (Dashboard, Scanner, Wardrobe, Analytics, Settings),
  active state, collapsible, glass.
- `components/layout/TopBar.tsx` — page title, theme toggle, Quick Scan button, AI status pill.
- `components/layout/MobileNav.tsx` — animated drawer + bottom bar for small screens.
- `components/layout/PageTransition.tsx` — Framer Motion route transitions.

### B4. Reusable UI (`components/ui/`)
Button, GlassCard/Card, Badge, Chip, Skeleton (+ card/grid variants), EmptyState, ErrorState,
Spinner, ProgressBar (animated), Modal/Sheet, Select/Dropdown, SearchInput, SegmentedControl
(grid/list & view toggles), Toast, ConfidenceMeter, ColorSwatch, AttributeItem.

### B5. Pages
- `app/page.tsx` — **Dashboard**: total items, recent scans count, Quick Scan CTA, recently
  added grid, scanner/AI status card. Skeletons + empty state.
- `app/scanner/page.tsx` — **Scanner**: Dropzone (drag&drop + click, single+multiple), preview
  thumbnails with remove, per-file animated progress, scan status indicator, retry failed,
  results list with detected attributes; posts to `/api/scan/batch` with progress.
  - `components/scanner/Dropzone.tsx`, `UploadPreviewCard.tsx`, `ScanResultCard.tsx`,
    `useScanUpload.ts` hook (queue, progress, retry).
- `app/wardrobe/page.tsx` — **Gallery**: grid/list toggle, search, filters (category, color,
  season, material), sort, pagination/infinite scroll. Card shows image, name, category,
  primary color, material, season, brand, confidence.
  - `components/wardrobe/ItemCard.tsx`, `ItemListRow.tsx`, `WardrobeFilters.tsx`,
    `useWardrobe.ts` hook.
- `app/wardrobe/[id]/page.tsx` — **Detail**: large image, all detected attributes, AI
  confidence, background-removal status, delete action, edit-free (auto-tagged) view.
- `app/analytics/page.tsx` — **Analytics**: category/color/season breakdowns from existing
  `/api/analytics` (charts via lightweight CSS/SVG bars, no heavy dep). Empty/skeleton states.
- `app/settings/page.tsx` — **Settings**: AI status, background-removal availability, detected
  attributes list, API URL info (from `/api/scan/status` + `/api/settings/status`).

### B6. States & polish
Loading skeletons per page, beautiful empty states (no items / no results), error states with
retry, toasts on scan success/failure/delete, smooth page + element transitions, full
responsive (mobile drawer + bottom nav), dark/light, glassmorphism throughout.

---

## Verification
- Backend: start uvicorn; `GET /api/scan/status`; scan a real photo single + batch, with and
  without OpenAI key; confirm items created with category/colors/material/season/formality set
  and `ai_metadata.scan` holding pattern/texture/fit/sleeve/occasion; confirm processed image
  served at `/uploads/...`; corrupt image → 400; one bad file doesn't fail the batch.
- Frontend: `npm install`; `npm run build` (typecheck + compile) must pass. Spot-run `npm run dev`.
- Clean up temp test images. Report rembg install result honestly.

## Risks
- `rembg`/`onnxruntime` may lack a Python 3.13 wheel → graceful PIL fallback keeps app working;
  I'll report actual result.
- New endpoints are unauthenticated, consistent with the app's explicit no-auth constraint (flagged).
- If some requirement pages beyond the six above were intended (e.g. Outfits), they can be added;
  this plan covers the explicitly-named pages plus Analytics/Settings for a finished feel.
