"""Lightweight color-harmony helpers for the rule-based stylist.

These functions let the offline recommender reason about color pairings without
any external service. They operate on hex strings and the coarse ``family``
label attached to :class:`~app.models.reference.Color`.
"""

from __future__ import annotations

import colorsys
import io

# Families we treat as endlessly combinable — they anchor most outfits.
NEUTRAL_FAMILIES = {"neutral", "black", "white", "grey", "gray", "beige"}


def hex_to_hsl(hex_str: str) -> tuple[float, float, float]:
    """Convert ``#rrggbb`` (or ``#rgb``) to (hue°, saturation, lightness)."""
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    # colorsys returns hue, lightness, saturation (HLS ordering).
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    return hue * 360, saturation, lightness


def is_neutral(family: str | None) -> bool:
    """True when a color family is a wardrobe neutral."""
    return (family or "").lower() in NEUTRAL_FAMILIES


def harmony_score(hex_a: str, hex_b: str) -> float:
    """Score how well two colors pair, from 0 (clash) to 1 (harmonious).

    Uses hue distance on the color wheel: near-analogous and complementary
    relationships score highest, awkward mid-distances lowest.
    """
    hue_a, _sat_a, _l_a = hex_to_hsl(hex_a)
    hue_b, _sat_b, _l_b = hex_to_hsl(hex_b)
    diff = abs(hue_a - hue_b) % 360
    diff = min(diff, 360 - diff)  # shortest arc

    if diff <= 30:  # analogous
        return 0.9
    if 150 <= diff <= 210:  # complementary
        return 0.85
    if 100 <= diff <= 140:  # triadic-ish
        return 0.7
    return 0.45


def palette_cohesion(hexes: list[str]) -> float:
    """Average pairwise harmony across a set of colors (1.0 if <2 colors)."""
    if len(hexes) < 2:
        return 1.0
    scores: list[float] = []
    for i in range(len(hexes)):
        for j in range(i + 1, len(hexes)):
            scores.append(harmony_score(hexes[i], hexes[j]))
    return sum(scores) / len(scores) if scores else 1.0


# --- Computer-vision color extraction ------------------------------------
# These power the scanner's deterministic Primary/Secondary color detection.
# They operate purely on pixels (Pillow), so color detection works with no
# AI key configured.


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an ``(r, g, b)`` tuple to a ``#rrggbb`` string."""
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, int(c))) for c in rgb))


def _is_backgroundish(rgb: tuple[int, int, int]) -> bool:
    """True for near-white/near-transparent pixels we treat as background."""
    r, g, b = rgb
    # Near-white (typical product/cutout background).
    return r > 244 and g > 244 and b > 244


def dominant_colors(
    image_bytes: bytes, k: int = 3
) -> list[tuple[tuple[int, int, int], float]]:
    """Return up to ``k`` dominant ``((r,g,b), weight)`` colors, most first.

    The image is downscaled and adaptively quantized with Pillow; near-white
    background pixels are discarded so the garment's own colors win. ``weight``
    is each color's share of the counted (non-background) pixels.
    """
    from PIL import Image

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return []
    img.thumbnail((160, 160))

    # Adaptive palette quantization groups similar pixels into clusters.
    quant = img.quantize(colors=max(k * 4, 8), method=Image.Quantize.FASTOCTREE)
    palette = quant.getpalette() or []
    counts = quant.getcolors() or []  # list of (count, palette_index)

    clusters: list[tuple[int, tuple[int, int, int]]] = []
    total = 0
    for count, idx in counts:
        rgb = (
            palette[idx * 3],
            palette[idx * 3 + 1],
            palette[idx * 3 + 2],
        )
        if _is_backgroundish(rgb):
            continue
        clusters.append((count, rgb))
        total += count

    if not clusters:
        return []

    clusters.sort(key=lambda c: c[0], reverse=True)
    return [(rgb, count / total) for count, rgb in clusters[:k]]


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """Perceptually-weighted Euclidean distance between two RGB colors."""
    # Weights approximate human sensitivity (more green, less blue).
    rmean = (a[0] + b[0]) / 2
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return (
        (2 + rmean / 256) * dr * dr
        + 4 * dg * dg
        + (2 + (255 - rmean) / 256) * db * db
    ) ** 0.5


def nearest_color_name(
    rgb: tuple[int, int, int], palette: list[tuple[str, str]]
) -> tuple[str, str] | None:
    """Return the ``(name, hex)`` from ``palette`` closest to ``rgb``.

    ``palette`` is a list of ``(name, hex)`` pairs (e.g. seeded ``Color`` rows).
    """
    best: tuple[str, str] | None = None
    best_dist = float("inf")
    for name, hex_str in palette:
        h = hex_str.lstrip("#")
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        try:
            target = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            continue
        dist = color_distance(rgb, target)
        if dist < best_dist:
            best_dist, best = dist, (name, hex_str)
    return best
