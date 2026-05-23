"""Two-stage pipeline.

Camera thread: reads at hardware max, draws overlay with the latest cached
detection, encodes JPEG, signals new-frame. This keeps display smooth.

Classifier thread: grabs the most recent raw frame every ~150ms, classifies,
runs debounce + DB insert. Classification and display are decoupled, so the
stream runs at camera FPS regardless of how long inference takes.
"""

from __future__ import annotations

import threading
import time
from collections import deque

import cv2

from .camera import camera
from .config import DETECTION_DEBOUNCE_SEC
from . import db
from .detector import classify, draw_overlay, Detection, get_roi_fraction, set_roi_fraction


ALLOWED_INTERVALS = [0.5, 1.0, 2.0, 3.0]

DEFAULT_INTERVAL = 1.0
DEFAULT_AUTO_NOTIFY = False
DEFAULT_ROI_FRACTION = 0.20


CLASSIFY_INTERVAL_SEC = 0.15
JPEG_QUALITY = 72


class Pipeline:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._cam_thread: threading.Thread | None = None
        self._cls_thread: threading.Thread | None = None

        self._latest_raw_frame = None
        self._latest_frame_jpg: bytes | None = None
        self._frame_event = threading.Event()
        self._frame_count = 0
        self._fps_window_start = time.time()
        self._display_fps = 0.0

        self._latest_detection: Detection | None = None
        self._latest_inference_ms: float = 0.0
        self._recent_categories: deque[str] = deque(maxlen=3)
        self._last_accepted: str | None = None
        self._last_accepted_at: float = 0.0

        self._subscribers: list[threading.Event] = []
        self._latest_event: dict | None = None

        # Runtime-mutable settings.
        self._interval_sec: float = float(DETECTION_DEBOUNCE_SEC)
        self._auto_notify: bool = False
        self._paused: bool = False
        self._on_accept_hook = None  # Callable[[dict], Awaitable[None]] | None

    def start(self) -> None:
        if self._cam_thread is not None:
            return
        self._stop.clear()
        self._cam_thread = threading.Thread(target=self._camera_loop, name="sorter-camera", daemon=True)
        self._cls_thread = threading.Thread(target=self._classifier_loop, name="sorter-classify", daemon=True)
        self._cam_thread.start()
        self._cls_thread.start()

    def stop(self) -> None:
        self._stop.set()
        for t in (self._cam_thread, self._cls_thread):
            if t is not None:
                t.join(timeout=2)
        self._cam_thread = None
        self._cls_thread = None

    # ---- camera loop ----
    def _camera_loop(self) -> None:
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
        while not self._stop.is_set():
            frame = camera.read()
            if frame is None:
                time.sleep(0.01)
                continue

            with self._lock:
                det = self._latest_detection
                paused = self._paused
                self._latest_raw_frame = frame

            overlay = draw_overlay(frame, det)
            if paused:
                cv2.putText(
                    overlay, "PAUSED", (overlay.shape[1] - 140, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4, cv2.LINE_AA,
                )
                cv2.putText(
                    overlay, "PAUSED", (overlay.shape[1] - 140, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA,
                )
            ok, buf = cv2.imencode(".jpg", overlay, encode_params)
            if not ok:
                continue

            now = time.time()
            with self._lock:
                self._latest_frame_jpg = buf.tobytes()
                self._frame_count += 1
                elapsed = now - self._fps_window_start
                if elapsed >= 1.0:
                    self._display_fps = self._frame_count / elapsed
                    self._frame_count = 0
                    self._fps_window_start = now
            self._frame_event.set()

    # ---- classifier loop ----
    def _classifier_loop(self) -> None:
        while not self._stop.is_set():
            with self._lock:
                frame = self._latest_raw_frame
            if frame is None:
                time.sleep(0.05)
                continue

            t0 = time.perf_counter()
            det = classify(frame)
            inference_ms = (time.perf_counter() - t0) * 1000.0

            with self._lock:
                self._latest_detection = det
                self._latest_inference_ms = inference_ms

            if det is not None:
                self._maybe_accept(det)

            time.sleep(CLASSIFY_INTERVAL_SEC)

    def _maybe_accept(self, det: Detection) -> None:
        self._recent_categories.append(det.category)
        if len(self._recent_categories) < self._recent_categories.maxlen:
            return
        if len(set(self._recent_categories)) != 1:
            return

        now = time.time()
        with self._lock:
            if self._paused:
                return
            interval = self._interval_sec
            hook = self._on_accept_hook
            auto = self._auto_notify
        if (now - self._last_accepted_at) < interval:
            return

        record = db.insert_detection(det.category, det.color_name, det.hue, det.saturation, det.value)
        self._last_accepted = det.category
        self._last_accepted_at = now
        with self._lock:
            self._latest_event = record
            for ev in self._subscribers:
                ev.set()

        if auto and hook is not None:
            try:
                hook(record)
            except Exception:
                pass

    # ---- accessors ----
    def latest_frame(self) -> bytes | None:
        with self._lock:
            return self._latest_frame_jpg

    def latest_detection(self) -> Detection | None:
        with self._lock:
            return self._latest_detection

    def latest_inference_ms(self) -> float:
        with self._lock:
            return self._latest_inference_ms

    def display_fps(self) -> float:
        with self._lock:
            return self._display_fps

    def wait_for_frame(self, timeout: float = 1.0) -> bool:
        ok = self._frame_event.wait(timeout=timeout)
        self._frame_event.clear()
        return ok

    def subscribe(self) -> threading.Event:
        ev = threading.Event()
        with self._lock:
            self._subscribers.append(ev)
        return ev

    def unsubscribe(self, ev: threading.Event) -> None:
        with self._lock:
            if ev in self._subscribers:
                self._subscribers.remove(ev)

    def snapshot_event(self) -> dict | None:
        with self._lock:
            return self._latest_event

    # ---- settings ----
    def get_settings(self) -> dict:
        with self._lock:
            return {
                "interval_sec": self._interval_sec,
                "allowed_intervals": ALLOWED_INTERVALS,
                "auto_notify": self._auto_notify,
                "roi_fraction": get_roi_fraction(),
                "paused": self._paused,
            }

    def set_paused(self, paused: bool) -> bool:
        with self._lock:
            self._paused = bool(paused)
            if self._paused:
                self._recent_categories.clear()
        return self._paused

    def set_roi(self, fraction: float) -> float:
        return set_roi_fraction(fraction)

    def reset_settings(self) -> dict:
        with self._lock:
            self._interval_sec = DEFAULT_INTERVAL
            self._auto_notify = DEFAULT_AUTO_NOTIFY
        set_roi_fraction(DEFAULT_ROI_FRACTION)
        return self.get_settings()

    def set_interval(self, seconds: float) -> float:
        if seconds not in ALLOWED_INTERVALS:
            raise ValueError(f"interval must be one of {ALLOWED_INTERVALS}")
        with self._lock:
            self._interval_sec = float(seconds)
        return self._interval_sec

    def set_auto_notify(self, enabled: bool) -> bool:
        with self._lock:
            self._auto_notify = bool(enabled)
        return self._auto_notify

    def set_accept_hook(self, hook) -> None:
        with self._lock:
            self._on_accept_hook = hook

    def reset_counters(self) -> None:
        with self._lock:
            self._recent_categories.clear()
            self._last_accepted = None
            self._last_accepted_at = 0.0
            self._latest_event = None


pipeline = Pipeline()
