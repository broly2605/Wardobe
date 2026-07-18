"""Local filesystem image storage.

Uploaded images are written under ``settings.upload_dir`` and served statically
by FastAPI. The database only stores the relative path, so switching to object
storage (S3, GCS) later means swapping this module without touching the schema.
"""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

# Accepted image content types and a sane maximum size (8 MB).
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 8 * 1024 * 1024
# Largest dimension we keep; larger uploads are downscaled to save disk/bandwidth.
MAX_DIMENSION = 1600


class ImageValidationError(ValueError):
    """Raised when an uploaded file is not an acceptable image."""


class StorageService:
    """Persists and removes wardrobe item images on the local filesystem."""

    def __init__(self) -> None:
        self.root: Path = settings.upload_path
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_image(self, file: UploadFile) -> str:
        """Validate, normalize, and store an uploaded image.

        Returns the DB-relative path (e.g. ``items/ab12cd.jpg``). The image is
        re-encoded via Pillow, which both strips unexpected payloads and lets us
        downscale oversized photos.
        """
        raw = await self.read_valid_image(file)

        import io

        image = Image.open(io.BytesIO(raw))
        # Normalize to RGB and downscale if needed.
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

        subdir = self.root / "items"
        subdir.mkdir(parents=True, exist_ok=True)
        filename = f"{secrets.token_hex(12)}.jpg"
        dest = subdir / filename
        image.convert("RGB").save(dest, format="JPEG", quality=88, optimize=True)

        # Return a POSIX-style relative path for stable URLs across OSes.
        return f"items/{filename}"

    async def read_valid_image(self, file: UploadFile) -> bytes:
        """Return the raw bytes of an uploaded file after validating it.

        Shared by the item image upload and the scanner: it enforces the content
        type, size limit, and Pillow-decodability, raising
        :class:`ImageValidationError` on any problem.
        """
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise ImageValidationError(
                f"Unsupported image type: {file.content_type!r}. "
                "Allowed: JPEG, PNG, WebP."
            )

        raw = await file.read()
        if len(raw) > MAX_BYTES:
            raise ImageValidationError("Image exceeds the 8 MB size limit.")

        import io

        try:
            image = Image.open(io.BytesIO(raw))
            image.verify()  # integrity check
        except (UnidentifiedImageError, OSError, SyntaxError) as exc:
            # Pillow raises SyntaxError for a recognized-but-corrupt image
            # (e.g. a PNG with a bad chunk checksum), so treat it as invalid.
            raise ImageValidationError("File is not a valid image.") from exc
        return raw

    def save_processed_image(self, image_bytes: bytes) -> str:
        """Persist already-processed JPEG bytes (e.g. a background-removed image).

        Unlike :meth:`save_image` this does not re-validate or re-encode beyond a
        safety pass, since the scanner has already normalized the bytes.
        """
        import io

        image = Image.open(io.BytesIO(image_bytes))
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

        subdir = self.root / "items"
        subdir.mkdir(parents=True, exist_ok=True)
        filename = f"{secrets.token_hex(12)}.jpg"
        dest = subdir / filename
        image.convert("RGB").save(dest, format="JPEG", quality=90, optimize=True)
        return f"items/{filename}"

    def delete_image(self, relative_path: str | None) -> None:
        """Delete a stored image if it exists; silently ignore missing files."""
        if not relative_path:
            return
        target = (self.root / relative_path).resolve()
        # Guard against path traversal: must stay within the uploads root.
        if self.root.resolve() not in target.parents:
            return
        target.unlink(missing_ok=True)

    @staticmethod
    def public_url(relative_path: str | None) -> str | None:
        """Map a stored relative path to its public static URL."""
        if not relative_path:
            return None
        return f"/uploads/{relative_path}"


storage_service = StorageService()
