import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

CAMERA_MODE = os.getenv("CAMERA_MODE", "mock").lower()
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
MOCK_IMAGES_DIR = Path(os.getenv("MOCK_IMAGES_DIR", BASE_DIR / "mock_caps"))
ROI_RADIUS_FRACTION = float(os.getenv("ROI_RADIUS_FRACTION", "0.25"))
DETECTION_DEBOUNCE_SEC = float(os.getenv("DETECTION_DEBOUNCE_SEC", "1.5"))
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "sorter.db"))
LINE_WEBHOOK_URL = os.getenv("LINE_WEBHOOK_URL", "").strip()
LINE_CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "").strip()
LINE_TARGET_ID = os.getenv("LINE_TARGET_ID", "").strip()
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
MOCK_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
