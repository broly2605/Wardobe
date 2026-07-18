"""Background removal for scanned clothing photos.

"Remove the background if necessary" is handled here with a two-tier strategy so
the scanner works regardless of what's installed:

* When :mod:`rembg` (ONNX U2-Net) is importable, we produce a true subject cutout
  and composite it onto a clean white canvas — ideal for busy backdrops.
* Otherwise we fall back to a lightweight Pillow heuristic that flattens a
  near-uniform background to white by sampling the image edges.

Either way the function returns ``(jpeg_bytes, removed)`` so callers can record
whether a cutout was actually applied. Removal only runs when the background
looks non-trivial, so already-clean product shots are left untouched.
"""

from __future__ import annotations

import io
from functools import lru_cache

from PIL import Image

# Largest dimension kept for the processed image (mirrors storage limits).
_MAX_DIMENSION = 1600
# Edge pixels are sampled to judge how uniform the background is.
_EDGE_SAMPLE = 24
# Std-dev threshold (0-255) below which edges count as a "clean" background.
_UNIFORM_STD_THRESHOLD = 18.0
# How close a pixel must be to the sampled background color to be flattened.
_FLATTEN_TOLERANCE = 42.0


@lru_cache(maxsize=1)
def _load_rembg():
    """Return rembg's ``remove`` callable, or ``None`` if unavailable.

    Import and model load are deferred and cached: the first cutout pays the
    model-download/initialization cost, later calls are cheap, and an
    environment without the wheel simply gets ``None``.
    """
    try:
        from rembg import remove  # type: ignore

        return remove
    except Exception:
        return None


def background_removal_available() -> bool:
    """Whether true (rembg) cutouts are available in this environment."""
    return _load_rembg() is not None


def _edge_pixels(image: Image.Image) -> list[tuple[int, int, int]]:
    """Sample RGB pixels around the four edges of the image."""
    rgb = image.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    xs = [int(i * (w - 1) / (_EDGE_SAMPLE - 1)) for i in range(_EDGE_SAMPLE)]
    ys = [int(i * (h - 1) / (_EDGE_SAMPLE - 1)) for i in range(_EDGE_SAMPLE)]
    samples: list[tuple[int, int, int]] = []
    for x in xs:
        samples.append(px[x, 0])
        samples.append(px[x, h - 1])
    for y in ys:
        samples.append(px[0, y])
        samples.append(px[w - 1, y])
    return samples


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _needs_removal(image: Image.Image) -> bool:
    """Whether the background warrants removal.

    Removal is "necessary" when the border either varies a lot (a busy/cluttered
    backdrop) or is a uniform color that isn't near-white (a colored studio
    background that would otherwise pollute color detection). An already-clean
    near-white shot needs nothing.
    """
    samples = _edge_pixels(image)
    if not samples:
        return False
    means = []
    for channel in range(3):
        vals = [float(s[channel]) for s in samples]
        mean = _mean(vals)
        std = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
        if std > _UNIFORM_STD_THRESHOLD:
            return True  # busy / varied background
        means.append(mean)
    # Uniform border: remove it unless it's already a near-white backdrop.
    return not all(m > 236 for m in means)


def _flatten_uniform_background(image: Image.Image) -> Image.Image:
    """Replace a near-uniform edge-color background with white (PIL fallback)."""
    rgb = image.convert("RGB")
    samples = _edge_pixels(rgb)
    bg = tuple(round(_mean([float(s[c]) for s in samples])) for c in range(3))

    px = rgb.load()
    w, h = rgb.size
    white = (255, 255, 255)
    tol_sq = _FLATTEN_TOLERANCE**2
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if ((r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2) <= tol_sq:
                px[x, y] = white
    return rgb


def _to_jpeg(image: Image.Image) -> bytes:
    """Encode an image to JPEG bytes on a white background."""
    if image.mode in ("RGBA", "LA", "P"):
        base = Image.new("RGB", image.size, (255, 255, 255))
        rgba = image.convert("RGBA")
        base.paste(rgba, mask=rgba.split()[-1])
        image = base
    elif image.mode != "RGB":
        image = image.convert("RGB")
    image.thumbnail((_MAX_DIMENSION, _MAX_DIMENSION))
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=90, optimize=True)
    return buf.getvalue()


def remove_background(image_bytes: bytes) -> tuple[bytes, bool]:
    """Return ``(processed_jpeg_bytes, removed)`` for an uploaded image.

    Removal only runs when the background looks non-trivial. rembg is preferred;
    a Pillow heuristic is the offline fallback. On any failure the original image
    is returned re-encoded, with ``removed=False``.
    """
    try:
        source = Image.open(io.BytesIO(image_bytes))
        source.load()
    except Exception:
        # Not a decodable image here; hand bytes back untouched.
        return image_bytes, False

    if not _needs_removal(source):
        # Already a clean shot — no removal necessary.
        return _to_jpeg(source), False

    remove = _load_rembg()
    if remove is not None:
        try:
            cut = remove(image_bytes)  # PNG bytes with alpha
            cut_img = Image.open(io.BytesIO(cut))
            return _to_jpeg(cut_img), True
        except Exception:
            pass  # fall through to the heuristic

    try:
        flattened = _flatten_uniform_background(source)
        return _to_jpeg(flattened), True
    except Exception:
        return _to_jpeg(source), False
