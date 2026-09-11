import base64
import cv2
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.database import get_db
from backend.app.models import AccessLog, VehicleRegistry
from backend.app.schemas import RecognitionResult
from backend.app.ai_engine.pipeline import ANPRPipeline
from backend.app.services.barrier_service import BarrierService

router = APIRouter(prefix="/api/recognize", tags=["Recognition"])
barrier_service = BarrierService()

class Base64FramePayload(BaseModel):
    image_base64: str
    source: str = "WEBCAM"

def _evaluate_access_and_log(db: Session, pipeline_res: dict, source: str) -> RecognitionResult:
    plate = pipeline_res.get("plate_number")
    conf = pipeline_res.get("confidence", 0.0)
    annotated_url = pipeline_res.get("annotated_image_path")
    crop_url = pipeline_res.get("plate_crop_path")
    box = pipeline_res.get("bounding_box")
    proc_time = pipeline_res.get("processing_time_ms", 0.0)

    if not pipeline_res["success"] or not plate:
        return RecognitionResult(
            success=False,
            plate_number=None,
            confidence=0.0,
            status="NOT_DETECTED",
            gate_action="DENIED",
            image_url=annotated_url,
            plate_crop_url=None,
            processing_time_ms=proc_time,
            bounding_box=None,
            message="No valid license plate detected in frame."
        )

    # Check vehicle registry
    vehicle = db.query(VehicleRegistry).filter(VehicleRegistry.plate_number == plate).first()

    status = "UNAUTHORIZED"
    gate_action = "DENIED"
    owner_name = None
    vehicle_model = None
    notes = None

    if vehicle:
        owner_name = vehicle.owner_name
        vehicle_model = vehicle.vehicle_model
        if vehicle.access_tier == "WHITELIST":
            status = "AUTHORIZED"
            gate_action = "OPENED"
            barrier_service.trigger_open(plate)
        elif vehicle.access_tier == "BLACKLIST":
            status = "BLACKLISTED"
            gate_action = "DENIED"
        elif vehicle.access_tier == "GUEST":
            status = "AUTHORIZED"
            gate_action = "OPENED"
            barrier_service.trigger_open(plate)
    else:
        status = "UNAUTHORIZED"
        gate_action = "DENIED"

    # Create Access Log record
    log_entry = AccessLog(
        plate_number=plate,
        confidence=conf,
        status=status,
        gate_action=gate_action,
        image_path=annotated_url,
        source=source,
        notes=f"Owner: {owner_name or 'Unregistered'} | Vehicle: {vehicle_model or 'N/A'}"
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    message = (
        f"ACCESS GRANTED - Welcome {owner_name} ({plate})"
        if status == "AUTHORIZED"
        else f"ACCESS DENIED - {status} ({plate})"
    )

    return RecognitionResult(
        success=True,
        plate_number=plate,
        confidence=conf,
        status=status,
        gate_action=gate_action,
        owner_name=owner_name,
        vehicle_model=vehicle_model,
        image_url=annotated_url,
        plate_crop_url=crop_url,
        processing_time_ms=proc_time,
        bounding_box=box,
        message=message
    )


@router.post("/upload", response_model=RecognitionResult)
async def recognize_upload_file(
    file: UploadFile = File(...),
    source: str = Form("UPLOAD"),
    db: Session = Depends(get_db)
):
    """Processes an uploaded vehicle image file."""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Could not decode image file")

        pipeline_res = ANPRPipeline.process_image(img, source_name=source)
        return _evaluate_access_and_log(db, pipeline_res, source)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/frame", response_model=RecognitionResult)
async def recognize_base64_frame(
    payload: Base64FramePayload,
    db: Session = Depends(get_db)
):
    """Processes a base64 encoded image frame from web camera or simulator."""
    try:
        data = payload.image_base64
        if "," in data:
            data = data.split(",", 1)[1]

        image_bytes = base64.b64decode(data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")

        pipeline_res = ANPRPipeline.process_image(img, source_name=payload.source)
        return _evaluate_access_and_log(db, pipeline_res, payload.source)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
