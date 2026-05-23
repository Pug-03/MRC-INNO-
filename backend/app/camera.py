"""Camera source that yields BGR frames.

Supports two modes:
  real  -- OpenCV VideoCapture(CAMERA_INDEX)
  mock  -- cycles BGR images from MOCK_IMAGES_DIR; if the dir is empty, generates
          synthetic color swatches so the app still runs with no assets.

A single CameraSource instance is shared across routes. Calls to `read()` are
thread-safe. Frames can be pulled for MJPEG streaming and classification.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import cv2
import numpy as np

from .config import CAMERA_MODE, CAMERA_INDEX, MOCK_IMAGES_DIR


SYNTHETIC_COLORS_BGR = [
    ((40, 40, 200),  "red"),
    ((0, 165, 255),  "orange"),
    ((0, 220, 240),  "yellow"),
    ((60, 180, 70),  "green"),
    ((200, 120, 40), "blue"),
    ((160, 60, 120), "purple"),
    ((20, 20, 20),   "black"),
    ((240, 240, 240),"white"),
]


def _synthetic_frame(color_bgr: tuple[int, int, int], tick: float) -> np.ndarray:
    h, w = 480, 640
    frame = np.full((h, w, 3), 235, dtype=np.uint8)
    cx, cy = w // 2, h // 2
    # gentle wobble so the stream visibly updates
    dx = int(8 * np.sin(tick))
    dy = int(8 * np.cos(tick))
    cv2.circle(frame, (cx + dx, cy + dy), 140, color_bgr, thickness=-1)
    # subtle highlight to mimic a reflective cap
    cv2.circle(frame, (cx + dx - 40, cy + dy - 40), 30, (255, 255, 255), thickness=-1)
    return frame


class CameraSource:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._mode = CAMERA_MODE
        self._cap: cv2.VideoCapture | None = None
        self._mock_images: list[np.ndarray] = []
        self._mock_idx = 0
        self._last_swap = time.time()
        self._tick = 0.0

        if self._mode == "real":
            self._open_real()
        else:
            self._load_mock_images()

    def _open_real(self) -> None:
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_ANY)
        if not cap.isOpened():
            # Fall back to mock so the server still runs during dev.
            self._mode = "mock"
            self._load_mock_images()
            return
        # MJPG fourcc lets most USB webcams deliver higher FPS at VGA than YUY2.
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 60)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap = cap

    def _load_mock_images(self) -> None:
        p = Path(MOCK_IMAGES_DIR)
        if p.is_dir():
            for f in sorted(p.iterdir()):
                if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}:
                    img = cv2.imread(str(f))
                    if img is not None:
                        self._mock_images.append(cv2.resize(img, (640, 480)))

    def _next_mock_frame(self) -> np.ndarray:
        self._tick += 0.15
        now = time.time()
        # Advance every ~2.5s so the classifier sees a steady color, then a new one.
        if now - self._last_swap > 2.5:
            self._mock_idx += 1
            self._last_swap = now

        if self._mock_images:
            idx = self._mock_idx % len(self._mock_images)
            return self._mock_images[idx].copy()

        color, _ = SYNTHETIC_COLORS_BGR[self._mock_idx % len(SYNTHETIC_COLORS_BGR)]
        return _synthetic_frame(color, self._tick)

    def read(self) -> np.ndarray | None:
        with self._lock:
            if self._mode == "real" and self._cap is not None:
                ok, frame = self._cap.read()
                if not ok:
                    return None
                return frame
            return self._next_mock_frame()

    @property
    def mode(self) -> str:
        return self._mode

    def release(self) -> None:
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None


camera = CameraSource()
