"""HSV-based bottle cap color classifier restricted to a circular ROI.

Categories (per spec):
  A -> Blue / Navy / Purple
  B -> Red / Orange / Yellow
  C -> Black
  D -> White
  E -> Green

Approach:
  1. Crop to circular ROI (center of frame, radius = fraction of frame height).
  2. Convert to HSV. Drop pixels outside ROI.
  3. Separate achromatic (low saturation) pixels into black (low V) / white (high V).
  4. For chromatic pixels, build a hue histogram and pick the dominant band.
  5. Map the dominant band -> category.

Tunable via ROI_RADIUS_FRACTION env var.
"""

from __future__ import annotations

import cv2
import numpy as np
from dataclasses import dataclass

from .config import ROI_RADIUS_FRACTION as _INITIAL_ROI


_roi_fraction: float = float(_INITIAL_ROI)


def get_roi_fraction() -> float:
    return _roi_fraction


def set_roi_fraction(value: float) -> float:
    global _roi_fraction
    _roi_fraction = max(0.05, min(0.45, float(value)))
    return _roi_fraction


CATEGORY_OF = {
    "red":    "B",
    "orange": "B",
    "yellow": "B",
    "green":  "E",
    "blue":   "A",
    "navy":   "A",
    "purple": "A",
    "black":  "C",
    "white":  "D",
}

# OpenCV hue: 0..179. Bands are (lo, hi) inclusive. Red wraps.
HUE_BANDS: list[tuple[str, int, int]] = [
    ("red",    0,   9),
    ("orange", 10,  22),
    ("yellow", 23,  34),
    ("green",  35,  85),
    ("blue",   86, 125),
    ("purple", 126, 160),
    ("red",    161, 179),
]


def _hue_to_name(hue: int) -> str | None:
    for name, lo, hi in HUE_BANDS:
        if lo <= hue <= hi:
            return name
    return None


@dataclass
class Detection:
    category: str
    color_name: str
    hue: int
    saturation: int
    value: int
    pixel_count: int
    mean_hsv: tuple[int, int, int] = (0, 0, 0)
    mean_rgb_hex: str = "#000000"

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "color_name": self.color_name,
            "hue": self.hue,
            "saturation": self.saturation,
            "value": self.value,
            "pixel_count": self.pixel_count,
            "mean_hsv": list(self.mean_hsv),
            "mean_rgb_hex": self.mean_rgb_hex,
        }


def roi_circle(frame_shape: tuple[int, int]) -> tuple[int, int, int]:
    h, w = frame_shape[:2]
    cx, cy = w // 2, h // 2
    r = int(min(h, w) * _roi_fraction)
    return cx, cy, r


def build_roi_mask(frame_shape: tuple[int, int]) -> np.ndarray:
    h, w = frame_shape[:2]
    cx, cy, r = roi_circle(frame_shape)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (cx, cy), r, 255, thickness=-1)
    return mask


def classify(frame_bgr: np.ndarray) -> Detection | None:
    """Return a Detection for the dominant color inside the ROI, or None if ROI is empty."""
    if frame_bgr is None or frame_bgr.size == 0:
        return None

    mask = build_roi_mask(frame_bgr.shape)
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    pixels = hsv[mask > 0]
    bgr_pixels = frame_bgr[mask > 0]
    if pixels.size == 0:
        return None

    h = pixels[:, 0].astype(np.int32)
    s = pixels[:, 1].astype(np.int32)
    v = pixels[:, 2].astype(np.int32)

    # Mean color shown in the UI so the user can sanity-check what the ROI sees.
    mean_b = int(bgr_pixels[:, 0].mean())
    mean_g = int(bgr_pixels[:, 1].mean())
    mean_r = int(bgr_pixels[:, 2].mean())
    mean_rgb_hex = f"#{mean_r:02x}{mean_g:02x}{mean_b:02x}"
    # Circular mean for hue (handles wraparound near red).
    hue_rad = (h.astype(np.float32) / 180.0) * (2 * np.pi)
    mean_hue_rad = np.arctan2(np.sin(hue_rad).mean(), np.cos(hue_rad).mean())
    mean_hue = int((mean_hue_rad / (2 * np.pi)) * 180) % 180
    mean_s = int(s.mean())
    mean_v = int(v.mean())
    mean_hsv = (mean_hue, mean_s, mean_v)

    # Effective chroma = S * V / 255. Dark pixels have low effective chroma even when
    # sensor noise inflates raw saturation -- this is what kills the "black reads as red"
    # failure mode.
    effective_chroma = (s * v) // 255
    mean_chroma = int(effective_chroma.mean())

    # Whole-ROI achromatic checks by means. Black runs first so a dark cap with noisy
    # chroma still lands in black, not in red/orange. White requires LOW chroma AND
    # hue that isn't clearly in a color band -- otherwise pale green / pale blue fall
    # into white.
    if mean_v < 70 and mean_chroma < 40:
        return Detection("C", "black", 0, mean_s, mean_v, pixels.shape[0], mean_hsv, mean_rgb_hex)
    if mean_v > 185 and mean_chroma < 18:
        return Detection("D", "white", 0, mean_s, mean_v, pixels.shape[0], mean_hsv, mean_rgb_hex)
    # Pale-but-still-colored shortcut: if chroma is small but hue is clearly in a
    # color band, classify by mean hue. Catches pale green, pale blue, etc.
    if mean_chroma >= 14:
        name = _hue_to_name(mean_hue)
        if name is not None:
            return Detection(
                CATEGORY_OF[name], name, mean_hue, mean_s, mean_v,
                pixels.shape[0], mean_hsv, mean_rgb_hex,
            )

    # Otherwise look at per-pixel distribution. "Colorful" = has real chroma.
    colorful = effective_chroma > 30
    n_total = pixels.shape[0]
    n_colorful = int(colorful.sum())

    # Not enough colorful pixels -> decide achromatic by mean brightness.
    if n_colorful < max(50, n_total * 0.2):
        if mean_v < 110:
            return Detection("C", "black", 0, mean_s, mean_v, n_total, mean_hsv, mean_rgb_hex)
        return Detection("D", "white", 0, mean_s, mean_v, n_total, mean_hsv, mean_rgb_hex)

    # Only the truly colorful pixels vote on hue. Weight by each pixel's chroma so
    # noisy low-chroma pixels can't swing the vote.
    h_vote = h[colorful]
    w_vote = effective_chroma[colorful].astype(np.float32)
    hist, _ = np.histogram(h_vote, bins=180, range=(0, 180), weights=w_vote)

    best_name = "red"
    best_weight = -1.0
    for name, lo, hi in HUE_BANDS:
        w = float(hist[lo : hi + 1].sum())
        if w > best_weight:
            best_weight = w
            best_name = name

    dominant_hue = int(np.argmax(hist))
    return Detection(
        category=CATEGORY_OF[best_name],
        color_name=best_name,
        hue=dominant_hue,
        saturation=int(s[colorful].mean()),
        value=int(v[colorful].mean()),
        pixel_count=n_colorful,
        mean_hsv=mean_hsv,
        mean_rgb_hex=mean_rgb_hex,
    )


def draw_overlay(frame_bgr: np.ndarray, detection: Detection | None) -> np.ndarray:
    """Draw the ROI circle and the current label onto a copy of the frame."""
    out = frame_bgr.copy()
    cx, cy, r = roi_circle(out.shape)
    cv2.circle(out, (cx, cy), r, (255, 255, 255), 2)
    cv2.circle(out, (cx, cy), r, (20, 20, 20), 1)

    label = "-- no signal --"
    if detection is not None:
        label = f"{detection.category}  {detection.color_name}"

    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(out, label, (20, 36), font, 0.8, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(out, label, (20, 36), font, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
    return out
