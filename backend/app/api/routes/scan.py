"""AI wardrobe scanner endpoints.

Upload one or many clothing photos; each image is analyzed by computer vision
(and the AI vision model when a key is configured), the background is removed
when needed, and a fully auto-tagged wardrobe item is created — no manual
tagging required. These endpoints never return 503: with no AI key the scanner
degrades to deterministic pixel-based detection.

Note: like the rest of this app these endpoints are unauthenticated by design
(single-user, no accounts).
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import ScanServiceDep
from app.api.serialization import serialize_item
from app.core.config import settings
from app.schemas.scan import BatchScanResponse, ScannedItemResult, ScanStatus
from app.services.ai.scanner import KNOWN_CATEGORIES  # noqa: F401 (kept for clarity)
from app.services.background import background_removal_available
from app.services.storage import ImageValidationError

router = APIRouter(prefix="/scan", tags=["scan"])

# Attributes the scanner detects, surfaced to the frontend for display.
DETECTED_ATTRIBUTES = [
    "category",
    "primary_color",
    "secondary_color",
    "pattern",
    "material",
    "texture",
    "season",
    "sleeve_length",
    "fit",
    "formality",
    "occasion",
    "brand",
]


@router.get("/status", response_model=ScanStatus)
async def scan_status() -> ScanStatus:
    """Report scanner capabilities (AI vision + background removal availability)."""
    return ScanStatus(
        ai_enabled=settings.ai_enabled,
        background_removal_available=background_removal_available(),
        detected_attributes=DETECTED_ATTRIBUTES,
    )


@router.post("", response_model=ScannedItemResult, status_code=status.HTTP_201_CREATED)
async def scan_single(
    service: ScanServiceDep,
    file: UploadFile = File(...),
) -> ScannedItemResult:
    """Scan a single image and create an auto-tagged wardrobe item."""
    try:
        item = await service.scan_one(file)
    except ImageValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return ScannedItemResult(
        filename=file.filename or "image",
        ok=True,
        item=serialize_item(item),
    )


@router.post("/batch", response_model=BatchScanResponse)
async def scan_batch(
    service: ScanServiceDep,
    files: list[UploadFile] = File(...),
) -> BatchScanResponse:
    """Scan multiple images. Per-file failures are reported without failing all."""
    if not files:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "No files were uploaded."
        )
    outcomes = await service.scan_many(files)
    results = [
        ScannedItemResult(
            filename=filename,
            ok=item is not None,
            item=serialize_item(item) if item is not None else None,
            error=error,
        )
        for filename, item, error in outcomes
    ]
    created = sum(1 for r in results if r.ok)
    return BatchScanResponse(
        scanned=len(results), created=created, results=results
    )
