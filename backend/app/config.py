import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "frontend"
SAMPLES_DIR = BASE_DIR / "backend" / "sample_plates"

# Support Vercel serverless environment (/tmp writable area)
IS_VERCEL = os.environ.get("VERCEL") is not None
if IS_VERCEL:
    UPLOADS_DIR = Path("/tmp/uploads")
    DATABASE_URL = "sqlite:////tmp/anpr.db"
else:
    UPLOADS_DIR = BASE_DIR / "backend" / "uploads"
    DATABASE_URL = f"sqlite:///{BASE_DIR / 'backend' / 'anpr.db'}"

# Ensure directories exist
try:
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(SAMPLES_DIR, exist_ok=True)
except Exception:
    pass

# Application Settings
APP_TITLE = "AI-Powered Number Plate Recognition System"
APP_VERSION = "2.0.0"
DEBUG = True
OCR_CONFIDENCE_THRESHOLD = 0.40
GATE_AUTO_CLOSE_SECONDS = 5

