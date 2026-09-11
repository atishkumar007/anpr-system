import os
import random
import cv2
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from backend.app.config import SAMPLES_DIR
from backend.app.database import get_db
from backend.app.services.barrier_service import BarrierService
from backend.app.routers.recognition import _evaluate_access_and_log
from backend.app.ai_engine.pipeline import ANPRPipeline

router = APIRouter(prefix="/api/simulator", tags=["Virtual IoT Simulator & Barrier"])
barrier_service = BarrierService()

class BarrierActionPayload(BaseModel):
    action: str  # OPEN, CLOSE

@router.get("/samples")
def list_sample_images():
    """Lists available sample vehicle and plate images for virtual simulation."""
    if not os.path.exists(SAMPLES_DIR):
        return []

    files = [f for f in os.listdir(SAMPLES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return [
        {
            "filename": f,
            "url": f"/sample_plates/{f}",
            "name": f.replace("_", " ").replace(".jpg", "").replace(".png", "").title()
        }
        for f in sorted(files)
    ]

@router.post("/trigger")
def trigger_virtual_scan(
    sample_filename: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Simulates an IoT camera snapshot trigger."""
    if not os.path.exists(SAMPLES_DIR):
        raise HTTPException(status_code=404, detail="Sample plates directory not found")

    sample_files = [f for f in os.listdir(SAMPLES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not sample_files:
        raise HTTPException(status_code=404, detail="No sample images found. Please run the sample generator.")

    target_file = sample_filename if sample_filename in sample_files else random.choice(sample_files)
    img_path = os.path.join(SAMPLES_DIR, target_file)

    img = cv2.imread(img_path)
    if img is None:
        raise HTTPException(status_code=500, detail="Failed to load sample image")

    pipeline_res = ANPRPipeline.process_image(img, source_name="VIRTUAL_IOT_CAMERA")
    return _evaluate_access_and_log(db, pipeline_res, source="VIRTUAL_IOT_CAMERA")

@router.get("/barrier/status")
def get_barrier_status():
    return barrier_service.get_status()

@router.post("/barrier/control")
def control_barrier(payload: BarrierActionPayload):
    action = payload.action.upper()
    if action == "OPEN":
        return barrier_service.trigger_open("MANUAL_OPERATOR_OVERRIDE")
    elif action == "CLOSE":
        return barrier_service.trigger_close()
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'OPEN' or 'CLOSE'.")
