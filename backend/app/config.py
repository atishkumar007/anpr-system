import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = BASE_DIR / "backend" / "uploads"
SAMPLES_DIR = BASE_DIR / "backend" / "sample_plates"
DATABASE_URL = f"sqlite:///{BASE_DIR / 'backend' / 'anpr.db'}"

# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)

# Application Settings
APP_TITLE = "AI-Powered Number Plate Recognition System"
APP_VERSION = "2.0.0"
DEBUG = True
OCR_CONFIDENCE_THRESHOLD = 0.40
GATE_AUTO_CLOSE_SECONDS = 5
