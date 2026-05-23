# Bottle Cap Color Sorter

Full-stack dashboard for a 24/7 industrial cap-sorting line. HSV classifier on a
circular ROI, React dashboard with live stream, per-day history, and Excel
export.

## Categories

| Code | Colors |
| ---- | ------ |
| A    | Blue, Navy, Purple |
| B    | Red, Orange, Yellow |
| C    | Black |
| D    | White |
| E    | Green |

## Layout

```
backend/   FastAPI + OpenCV + SQLite + psutil + openpyxl
frontend/  Vite + React + TypeScript + Tailwind + Recharts
```

## Backend

Requires Python 3.10+.

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # optional — edit to taste
python run.py                  # serves on http://localhost:8000
```

### Camera modes (`CAMERA_MODE` in `.env`)

- `mock` — cycles through synthetic swatches (A–E) so the system runs with no
  hardware. Drop JPG/PNG images into `backend/mock_caps/` to use your own.
- `real` — opens OpenCV `VideoCapture(CAMERA_INDEX)`. Falls back to mock if the
  device can't be opened.

### ROI

The circular detection zone is centered in the frame with radius =
`ROI_RADIUS_FRACTION * min(height, width)`. Tune in `.env`.

### Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | `/api/stats` | Totals + recent events + live reading |
| POST   | `/api/detection` | Manual insert (testing / external classifiers) |
| GET    | `/api/history?start=YYYY-MM-DD&end=YYYY-MM-DD` | Per-day totals |
| GET    | `/api/history?date=YYYY-MM-DD` | Single-day totals |
| GET    | `/api/system` | CPU / GPU temp + load |
| POST   | `/api/notify/line` | Send message (see LINE below) |
| GET    | `/api/notify/history` | Recent notify attempts |
| GET    | `/api/export/excel?start=...&end=...` | Download `.xlsx` |
| GET    | `/api/camera/stream` | MJPEG stream with ROI overlay |
| GET    | `/api/camera/snapshot.jpg` | Latest annotated frame |
| GET    | `/api/events` | SSE stream of accepted detections |
| GET    | `/api/health` | Liveness |

### LINE integration

LINE Notify was shut down on 2025-03-31, so `/api/notify/line` instead targets
the LINE Messaging API. Set in `.env`:

```
LINE_CHANNEL_TOKEN=...         # Channel access token for your Official Account
LINE_TARGET_ID=U...            # User / group / room id to push to
```

If these are empty but `LINE_WEBHOOK_URL` is set, the backend POSTs the message
to that webhook (useful for Slack / Discord / Make / n8n). With neither set,
calls are accepted and appear in `/api/notify/history` as `transport=log-only`.

### AI / classifier notes

The HSV classifier in `backend/app/detector.py`:

1. Builds a circular mask around the frame center.
2. Converts to HSV, splits into achromatic (low S) and chromatic pixels.
3. Returns black/white when achromatic dominates; otherwise buckets the chromatic
   hue histogram into the 7 color names and maps to A–E.

Inference is well under 2s per cap (usually <50ms on CPU). To swap in a trained
CNN later, implement `classify(frame_bgr) -> Detection` and keep the same
contract — the pipeline and API stay as-is.

## Frontend

```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

Vite proxies `/api` to `http://localhost:8000`, so just run both in parallel.

### Features

- Live MJPEG feed with ROI overlay + detected category label
- Pie chart with count & percentage per category (Recharts)
- Total-today display with color-coded per-category breakdown
- Live event log + LINE summary button
- CPU / GPU / memory health bars
- History page with date-range filter and per-day totals
- Excel export (date or range)
- EN / TH full UI translation, persisted
- Responsive: 1-col mobile, 2-col tablet, multi-panel desktop
- Real-time clock, updates every second

## Production

Build the frontend and serve it behind the same origin as the API (e.g. nginx +
uvicorn), or keep them split with CORS — `FRONTEND_ORIGIN` is already wired up.
