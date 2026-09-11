import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def preflight_setup():
    """Generates sample test vehicle images if needed."""
    try:
        from generate_samples import generate_all_samples
        print("[Setup] Generating realistic test vehicle samples...")
        generate_all_samples()
        print("[Setup] Samples ready in backend/sample_plates/")
    except Exception as e:
        print(f"[Setup] Sample generation note: {e}")

def open_browser():
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print("\n" + "=" * 55)
    print("AI Number Plate Recognition System is LIVE!")
    print(f"Dashboard URL: {url}")
    print(f"API Documentation: {url}/docs")
    print("=" * 55 + "\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    preflight_setup()

    # Launch browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
