"""FastAPI entrypoint for the bottle cap sorter."""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from . import db, export, notify, system
from .camera import camera
from .config import FRONTEND_ORIGIN
from .pipeline import pipeline


@asynccontextmanager
async def lifespan(_app: FastAPI):
    loop = asyncio.get_running_loop()

    def _notify_hook(record: dict) -> None:
        # Called from a worker thread in the pipeline. Schedule the async LINE send
        # on the main event loop so we don't block the classifier.
        msg = (
            f"Cap Sorter: {record['category']} ({record['color_name']}) "
            f"at {record['ts']}"
        )
        asyncio.run_coroutine_threadsafe(notify.send_line(msg), loop)

    pipeline.set_accept_hook(_notify_hook)
    pipeline.start()
    try:
        yield
    finally:
        pipeline.stop()
        camera.release()


app = FastAPI(title="Bottle Cap Sorter", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- models


class DetectionIn(BaseModel):
    category: str = Field(pattern=r"^[A-E]$")
    color_name: str
    hue: int = 0
    saturation: int = 0
    value: int = 0


class NotifyIn(BaseModel):
    message: str


class IntervalIn(BaseModel):
    seconds: float


class AutoNotifyIn(BaseModel):
    enabled: bool


class ResetIn(BaseModel):
    scope: str = "all"  # "all" or "today"


class RoiIn(BaseModel):
    fraction: float


class PauseIn(BaseModel):
    paused: bool


class CameraSelectIn(BaseModel):
    index: int = Field(ge=0, le=15)


# --------------------------------------------------------------------------- routes


@app.get("/api/stats")
def stats():
    live = pipeline.latest_detection()
    return {
        "today": db.totals_today(),
        "recent": db.recent_events(limit=50),
        "live": live.to_dict() if live else None,
        "camera_mode": camera.mode,
        "camera_index": camera.index,
        "inference_ms": round(pipeline.latest_inference_ms(), 2),
        "display_fps": round(pipeline.display_fps(), 1),
    }


@app.post("/api/detection")
def add_detection(payload: DetectionIn):
    """Manual detection entry -- used for tests or external classifiers."""
    return db.insert_detection(
        payload.category, payload.color_name, payload.hue, payload.saturation, payload.value
    )


@app.get("/api/history")
def history(
    date_: str | None = Query(default=None, alias="date"),
    start: str | None = None,
    end: str | None = None,
):
    if date_:
        return {"days": [db.totals_for_day(date_)]}
    if start and end:
        return {"days": db.totals_range(start, end)}
    # Default: last 14 days
    today = date.today()
    start_d = (today - timedelta(days=13)).isoformat()
    end_d = today.isoformat()
    return {"days": db.totals_range(start_d, end_d)}


@app.get("/api/system")
def system_stats():
    return system.snapshot()


@app.post("/api/notify/line")
async def notify_line(payload: NotifyIn):
    return await notify.send_line(payload.message)


@app.get("/api/notify/history")
def notify_history():
    return {"items": notify.history()}


@app.get("/api/export/excel")
def export_excel(
    start: str | None = None,
    end: str | None = None,
    date_: str | None = Query(default=None, alias="date"),
):
    if date_:
        start = end = date_
    if not start or not end:
        today = date.today().isoformat()
        start = end = today
    try:
        data = export.build_xlsx(start, end)
    except Exception as e:
        raise HTTPException(500, f"export failed: {e}")
    headers = {"Content-Disposition": f'attachment; filename="{export.filename(start, end)}"'}
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


# --------------------------------------------------------------------------- camera


def _mjpeg_generator():
    boundary = b"--frame"
    last: bytes | None = None
    while True:
        if not pipeline.wait_for_frame(timeout=1.0):
            continue
        jpg = pipeline.latest_frame()
        if jpg is None or jpg is last:
            continue
        last = jpg
        yield boundary + b"\r\nContent-Type: image/jpeg\r\nContent-Length: " + \
            str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n"


@app.get("/api/camera/stream")
def camera_stream():
    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/camera/snapshot.jpg")
def camera_snapshot():
    jpg = pipeline.latest_frame()
    if jpg is None:
        raise HTTPException(503, "no frame yet")
    return Response(content=jpg, media_type="image/jpeg")


@app.get("/api/camera/devices")
def camera_devices():
    return {
        "devices": camera.list_devices(),
        "current": camera.index,
        "mode": camera.mode,
    }


@app.post("/api/camera/select")
def camera_select(payload: CameraSelectIn):
    ok = camera.switch(payload.index)
    if not ok:
        raise HTTPException(400, f"failed to open camera index {payload.index}")
    return {"current": camera.index, "mode": camera.mode}


# --------------------------------------------------------------------------- SSE live events


@app.get("/api/events")
async def events():
    """Server-sent-events stream of accepted detections."""
    import json as _json

    async def gen():
        ev = pipeline.subscribe()
        try:
            today = db.totals_today()
            yield f"event: totals\ndata: {_json.dumps(today)}\n\n"
            while True:
                got = await asyncio.get_event_loop().run_in_executor(None, ev.wait, 15)
                if not got:
                    yield ": keepalive\n\n"
                    continue
                ev.clear()
                snap = pipeline.snapshot_event()
                if snap is not None:
                    yield f"event: detection\ndata: {_json.dumps(snap)}\n\n"
        finally:
            pipeline.unsubscribe(ev)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/settings")
def get_settings():
    return pipeline.get_settings()


@app.post("/api/settings/interval")
def set_interval(payload: IntervalIn):
    try:
        seconds = pipeline.set_interval(payload.seconds)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"interval_sec": seconds}


@app.post("/api/settings/auto_notify")
def set_auto_notify(payload: AutoNotifyIn):
    return {"auto_notify": pipeline.set_auto_notify(payload.enabled)}


@app.post("/api/settings/roi")
def set_roi(payload: RoiIn):
    return {"roi_fraction": pipeline.set_roi(payload.fraction)}


@app.post("/api/settings/reset")
def reset_settings():
    return pipeline.reset_settings()


@app.post("/api/settings/pause")
def set_paused(payload: PauseIn):
    return {"paused": pipeline.set_paused(payload.paused)}


@app.post("/api/reset")
def reset(payload: ResetIn):
    if payload.scope == "today":
        from datetime import date as _date
        n = db.clear_day(_date.today().isoformat())
    elif payload.scope == "all":
        n = db.clear_all()
    else:
        raise HTTPException(400, "scope must be 'all' or 'today'")
    pipeline.reset_counters()
    return {"deleted": n, "scope": payload.scope}


@app.get("/api/health")
def health():
    return {"ok": True, "camera_mode": camera.mode}
