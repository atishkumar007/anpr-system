import sys
import os
from pathlib import Path

# Add project root to sys.path so backend imports work seamlessly
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.main import app

# Handler for Vercel Serverless
app = app
