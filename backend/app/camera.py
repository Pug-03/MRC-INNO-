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


MAX_PROBE_INDEX = 8


def _configure(cap: cv2.VideoCapture) -> None:
    # MJPG fourcc lets most USB webcams deliver higher FPS at VGA than YUY2.
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)


def _enum_pygrabber() -> list[dict] | None:
    """Use DirectShow via pygrabber to list cameras with friendly names.

    Returns None if pygrabber isn't installed (e.g. non-Windows). The DirectShow
    filter graph reports devices as soon as Windows registers them, which is why
    a freshly-plugged USB camera shows up here but not always via OpenCV's
    MSMF-backed CAP_ANY probe.
    """
    try:
        from pygrabber.dshow_graph import FilterGraph  # type: ignore
    except Exception:
        return None
    try:
        names = FilterGraph().get_input_devices()
    except Exception:
        return None
    return [{"index": i, "name": n or f"Camera {i}"} for i, n in enumerate(names)]


def _open_capture(index: int) -> cv2.VideoCapture | None:
    """Try DirectShow first (most reliable on Windows for USB cams), then any."""
    for backend in (cv2.CAP_DSHOW, cv2.CAP_ANY):
        cap = cv2.VideoCapture(index, backend)
        if cap.isOpened():
            return cap
        cap.release()
    return None


class CameraSource:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._mode = CAMERA_MODE
        self._cap: cv2.VideoCapture | None = None
        self._index: int = CAMERA_INDEX
        self._mock_images: list[np.ndarray] = []
        self._mock_idx = 0
        self._last_swap = time.time()
        self._tick = 0.0

        if self._mode == "real" and not self._open_real(CAMERA_INDEX):
            # Fall back to mock so the server still runs during dev.
            self._mode = "mock"
        if self._mode != "real":
            self._load_mock_images()

    def _open_real(self, index: int) -> bool:
        cap = _open_capture(index)
        if cap is None:
            return False
        _configure(cap)
        self._cap = cap
        self._index = index
        self._mode = "real"
        return True

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

    @property
    def index(self) -> int | None:
        return self._index if self._mode == "real" else None

    def list_devices(self) -> list[dict]:
        """Enumerate cameras Windows currently sees.

        Preferred path is pygrabber (DirectShow), which exposes friendly names
        and picks up freshly-plugged USB cameras. Falls back to probing OpenCV
        with DSHOW + CAP_ANY backends; the active index is reported as-is
        without re-opening the device.
        """
        active = self._index if self._mode == "real" else None

        enumerated = _enum_pygrabber()
        if enumerated is not None:
            for d in enumerated:
                d["active"] = d["index"] == active
            return enumerated

        devices: list[dict] = []
        for i in range(MAX_PROBE_INDEX):
            if active == i and self._cap is not None:
                devices.append({"index": i, "name": f"Camera {i}", "active": True})
                continue
            cap = _open_capture(i)
            if cap is not None:
                cap.release()
                devices.append({"index": i, "name": f"Camera {i}", "active": False})
        return devices

    def switch(self, index: int) -> bool:
        """Switch to camera at `index`. Returns True on success; on failure the
        previous source is restored if possible."""
        with self._lock:
            prev_cap = self._cap
            prev_index = self._index
            prev_mode = self._mode
            self._cap = None
            if prev_cap is not None:
                prev_cap.release()
            if self._open_real(index):
                return True
            # Reopen previous so the stream survives a bad pick.
            if prev_mode == "real" and self._open_real(prev_index):
                return False
            self._mode = "mock"
            if not self._mock_images:
                self._load_mock_images()
            return False

    def release(self) -> None:
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None


camera = CameraSource()
