"""GPU temperature + utilization, CPU + memory load.

CPU temperature removed intentionally -- Windows has no kernel interface for it
without a helper driver, and the dashboard no longer displays it.

psutil.cpu_percent(interval=None) returns 0.0 on its first call because it needs
a prior sample to diff against. We prime it at import time so the first real
request from the dashboard returns a meaningful reading.
"""

from __future__ import annotations

import shutil
import subprocess

import psutil


# Prime CPU-percent so subsequent non-blocking calls return accurate readings.
psutil.cpu_percent(interval=None)


def _gpu_stats() -> tuple[float | None, float | None, float | None, str | None]:
    """Returns (temperature_c, utilization_percent, memory_used_percent, name).
    Best-effort via nvidia-smi. Returns (None, None, None, None) if unavailable.
    """
    if shutil.which("nvidia-smi") is None:
        return None, None, None, None
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total,name",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True, text=True, timeout=2,
        )
        if out.returncode != 0:
            return None, None, None, None
        parts = [p.strip() for p in out.stdout.strip().splitlines()[0].split(",")]
        temp = float(parts[0])
        util = float(parts[1])
        mem_used = float(parts[2])
        mem_total = float(parts[3])
        name = parts[4]
        mem_pct = (mem_used / mem_total) * 100 if mem_total > 0 else None
        return temp, util, mem_pct, name
    except Exception:
        return None, None, None, None


def _level(temp: float | None) -> str:
    if temp is None:
        return "unknown"
    if temp < 60:
        return "normal"
    if temp < 80:
        return "warm"
    return "hot"


def snapshot() -> dict:
    gpu_t, gpu_util, gpu_mem, gpu_name = _gpu_stats()
    mem = psutil.virtual_memory()
    return {
        "cpu": {
            "load_percent": psutil.cpu_percent(interval=None),
            "cores": psutil.cpu_count(logical=True),
        },
        "gpu": {
            "name": gpu_name,
            "temperature_c": gpu_t,
            "level": _level(gpu_t),
            "load_percent": gpu_util,
            "memory_percent": gpu_mem,
        },
        "memory": {
            "percent": mem.percent,
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "total_gb": round(mem.total / (1024 ** 3), 2),
        },
    }
