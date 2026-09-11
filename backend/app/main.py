import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.app.config import STATIC_DIR, UPLOADS_DIR, SAMPLES_DIR, APP_TITLE, APP_VERSION
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import VehicleRegistry
from backend.app.routers import recognition, vehicles, logs, simulator

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Software-based AI-powered Automatic Number Plate Recognition (ANPR) System"
)

# Enable CORS for local development & browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(recognition.router)
app.include_router(vehicles.router)
app.include_router(logs.router)
app.include_router(simulator.router)

# Mount Static File Handlers
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/sample_plates", StaticFiles(directory=SAMPLES_DIR), name="sample_plates")

@app.get("/")
def serve_dashboard():
    return FileResponse(STATIC_DIR / "index.html")

# Auto-seed sample vehicles on startup if empty
@app.on_event("startup")
def seed_initial_data():
    db = SessionLocal()
    try:
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
    except Exception as e:
        print(f"[DB] Seed error: {e}")
    finally:
        db.close()
