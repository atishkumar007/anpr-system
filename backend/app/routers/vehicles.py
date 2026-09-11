from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import re

from backend.app.database import get_db
from backend.app.models import VehicleRegistry
from backend.app.schemas import VehicleCreate, VehicleUpdate, VehicleOut

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles Registry"])

@router.get("/", response_model=List[VehicleOut])
def list_vehicles(
    query: Optional[str] = Query(None, description="Search by plate or owner name"),
    access_tier: Optional[str] = Query(None, description="Filter by WHITELIST, BLACKLIST, GUEST"),
    db: Session = Depends(get_db)
):
    q = db.query(VehicleRegistry)
    if access_tier:
        q = q.filter(VehicleRegistry.access_tier == access_tier.upper())
    if query:
        pattern = f"%{query}%"
        q = q.filter(
            (VehicleRegistry.plate_number.ilike(pattern)) |
            (VehicleRegistry.owner_name.ilike(pattern)) |
            (VehicleRegistry.vehicle_model.ilike(pattern))
        )
    return q.order_by(VehicleRegistry.created_at.desc()).all()


@router.post("/", response_model=VehicleOut)
def register_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)):
    clean_plate = re.sub(r'[^A-Za-z0-9]', '', payload.plate_number).upper()
    if not clean_plate:
        raise HTTPException(status_code=400, detail="Invalid license plate number format")

    existing = db.query(VehicleRegistry).filter(VehicleRegistry.plate_number == clean_plate).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Plate '{clean_plate}' is already registered.")

    vehicle = VehicleRegistry(
        plate_number=clean_plate,
        owner_name=payload.owner_name.strip(),
        vehicle_model=payload.vehicle_model.strip() if payload.vehicle_model else None,
        access_tier=payload.access_tier.upper(),
        notes=payload.notes
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(vehicle_id: int, payload: VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = db.query(VehicleRegistry).filter(VehicleRegistry.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    if payload.owner_name is not None:
        vehicle.owner_name = payload.owner_name.strip()
    if payload.vehicle_model is not None:
        vehicle.vehicle_model = payload.vehicle_model.strip()
    if payload.access_tier is not None:
        vehicle.access_tier = payload.access_tier.upper()
    if payload.notes is not None:
        vehicle.notes = payload.notes

    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(VehicleRegistry).filter(VehicleRegistry.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.delete(vehicle)
    db.commit()
    return {"success": True, "message": f"Deleted vehicle {vehicle.plate_number}"}
