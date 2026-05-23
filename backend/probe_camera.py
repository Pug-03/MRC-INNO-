"""Probe the webcam: try a set of (backend, resolution, fps) combos and report
the ACTUAL delivered FPS for each. Run:  python probe_camera.py
"""
import time
import cv2


CANDIDATES = [
    # (backend_name, cv2 flag, width, height, target_fps)
    ("MSMF",  cv2.CAP_MSMF,  640, 480, 60),
    ("MSMF",  cv2.CAP_MSMF,  640, 480, 30),
    ("MSMF",  cv2.CAP_MSMF,  320, 240, 60),
    ("DSHOW", cv2.CAP_DSHOW, 640, 480, 60),
    ("DSHOW", cv2.CAP_DSHOW, 640, 480, 30),
    ("DSHOW", cv2.CAP_DSHOW, 320, 240, 60),
    ("DSHOW", cv2.CAP_DSHOW, 320, 240, 120),
]


def measure(backend_name, backend, w, h, fps, duration=2.0):
    cap = cv2.VideoCapture(0, backend)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # Read a few warmup frames.
    for _ in range(5):
        cap.read()
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    reported_fps = cap.get(cv2.CAP_PROP_FPS)

    t0 = time.time()
    n = 0
    while time.time() - t0 < duration:
        ok, _ = cap.read()
        if ok:
            n += 1
    elapsed = time.time() - t0
    cap.release()
    return {
        "backend": backend_name,
        "requested": f"{w}x{h}@{fps}",
        "actual_res": f"{actual_w}x{actual_h}",
        "reported_fps": reported_fps,
        "measured_fps": n / elapsed,
    }


if __name__ == "__main__":
    print(f"{'backend':6s}  {'requested':14s}  {'actual':10s}  {'reported':>9s}  {'measured':>9s}")
    print("-" * 60)
    for name, flag, w, h, fps in CANDIDATES:
        r = measure(name, flag, w, h, fps)
        if r is None:
            print(f"{name:6s}  {w}x{h}@{fps:<3d}     [could not open]")
            continue
        print(f"{r['backend']:6s}  {r['requested']:14s}  {r['actual_res']:10s}  {r['reported_fps']:9.1f}  {r['measured_fps']:9.1f}")
