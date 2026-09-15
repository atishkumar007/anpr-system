import os
from pathlib import Path
from fastapi import FastAPI, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

from backend.app.config import STATIC_DIR, UPLOADS_DIR, SAMPLES_DIR, BASE_DIR, APP_TITLE, APP_VERSION
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import VehicleRegistry
from backend.app.routers import recognition, vehicles, logs, simulator, vehicle_lookup

# Initialize database schema
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[DB] Init warning: {e}")

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Software-based AI-powered Automatic Number Plate Recognition (ANPR) System"
)

# Enable CORS for development and cloud deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(recognition.router)
app.include_router(vehicles.router)
app.include_router(logs.router)
app.include_router(simulator.router)
app.include_router(vehicle_lookup.router)


def get_frontend_file(rel_path: str) -> str:
    """Helper to locate and read frontend files across local and serverless environments."""
    possible_roots = [
        BASE_DIR / "frontend",
        Path.cwd() / "frontend",
        Path(__file__).resolve().parent.parent.parent / "frontend",
        Path("/var/task/frontend"),
    ]
    for root in possible_roots:
        target = root / rel_path
        if target.exists():
            with open(target, "r", encoding="utf-8") as f:
                return f.read()
    return ""

# Static file explicit routes for Serverless / Vercel compatibility
@app.get("/static/css/styles.css")
def serve_css():
    content = get_frontend_file("css/styles.css")
    if content:
        return Response(content=content, media_type="text/css")
    return Response(content="", media_type="text/css")

@app.get("/static/js/app.js")
def serve_app_js():
    content = get_frontend_file("js/app.js")
    if content:
        return Response(content=content, media_type="application/javascript")
    return Response(content="", media_type="application/javascript")

@app.get("/static/js/charts.js")
def serve_charts_js():
    content = get_frontend_file("js/charts.js")
    if content:
        return Response(content=content, media_type="application/javascript")
    return Response(content="", media_type="application/javascript")

@app.get("/sample_plates/{filename}")
def serve_sample_plate(filename: str):
    possible_paths = [
        SAMPLES_DIR / filename,
        Path.cwd() / "backend" / "sample_plates" / filename,
        Path(__file__).resolve().parent.parent / "sample_plates" / filename,
        Path("/var/task/backend/sample_plates") / filename
    ]
    for p in possible_paths:
        if p.exists():
            return FileResponse(p)
    raise HTTPException(status_code=404, detail="Sample image not found")

@app.get("/uploads/{filename}")
def serve_uploaded_image(filename: str):
    p = UPLOADS_DIR / filename
    if p.exists():
        return FileResponse(p)
    raise HTTPException(status_code=404, detail="Upload snapshot not found")

# Main Dashboard Route
@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/", response_class=HTMLResponse)
def serve_dashboard():
    html = get_frontend_file("index.html")
    if html:
        return HTMLResponse(content=html, status_code=200)
    return HTMLResponse(content="<h1>AutoPlate AI Dashboard</h1><p>Loading frontend...</p>", status_code=200)

# Mount Static File Handlers (For Local Uvicorn Development)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Auto-seed sample vehicles on startup if empty
@app.on_event("startup")
def seed_initial_data():
    try:
        db = SessionLocal()
        if db.query(VehicleRegistry).count() == 0:
            sample_vehicles = [
                VehicleRegistry(
                    plate_number="MH12DE1433",
                    owner_name="Alex Johnson",
                    vehicle_model="Toyota Fortuner (White)",
                    access_tier="WHITELIST",
                    notes="CEO - VIP Parking Reserved"
                ),
                VehicleRegistry(
                    plate_number="DL01AB1234",
                    owner_name="Sarah Connor",
                    vehicle_model="Tesla Model 3 (Black)",
                    access_tier="WHITELIST",
                    notes="Engineering Director"
                ),
                VehicleRegistry(
                    plate_number="KA05MJ9876",
                    owner_name="David Miller",
                    vehicle_model="Honda Civic (Grey)",
                    access_tier="WHITELIST",
                    notes="Operations Manager"
                ),
                VehicleRegistry(
                    plate_number="HR26DK8392",
                    owner_name="Marcus Vance",
                    vehicle_model="Ford Mustang (Red)",
                    access_tier="BLACKLIST",
                    notes="Suspended Employee - Do Not Permit"
                ),
                VehicleRegistry(
                    plate_number="TN09AZ4321",
                    owner_name="Express Logistics",
                    vehicle_model="Delivery Van",
                    access_tier="GUEST",
                    notes="Authorized Delivery Vendor"
                ),
            ]
            db.add_all(sample_vehicles)
            db.commit()
            print("[DB] Initial vehicle access registry seeded.")
        db.close()
    except Exception as e:
        print(f"[DB] Seed note: {e}")
