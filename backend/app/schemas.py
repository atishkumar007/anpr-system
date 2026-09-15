from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class VehicleCreate(BaseModel):
    plate_number: str = Field(..., description="Normalized alphanumeric license plate text")
    owner_name: str = Field(..., description="Vehicle owner or driver name")
    vehicle_model: Optional[str] = Field(None, description="Make and model of vehicle")
    access_tier: str = Field("WHITELIST", description="WHITELIST, BLACKLIST, or GUEST")
    notes: Optional[str] = None

class VehicleUpdate(BaseModel):
    owner_name: Optional[str] = None
    vehicle_model: Optional[str] = None
    access_tier: Optional[str] = None
    notes: Optional[str] = None

class VehicleOut(BaseModel):
    id: int
    plate_number: str
    owner_name: str
    vehicle_model: Optional[str]
    access_tier: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class RecognitionResult(BaseModel):
    success: bool
    plate_number: Optional[str] = None
    confidence: float = 0.0
    vehicle_type: Optional[str] = "Car"
    vehicle_color: Optional[str] = "White"
    camera_id: Optional[str] = "CAM-01"
    direction: Optional[str] = "ENTRY"
    ai_engine: Optional[str] = "Local YOLO + OCR Engine"
    status: str = "UNAUTHORIZED"  # AUTHORIZED, UNAUTHORIZED, BLACKLISTED, NOT_DETECTED
    gate_action: str = "DENIED"   # OPENED, DENIED
    owner_name: Optional[str] = None
    vehicle_model: Optional[str] = None
    image_url: Optional[str] = None
    plate_crop_url: Optional[str] = None
    processing_time_ms: float = 0.0
    bounding_box: Optional[List[int]] = None  # [x, y, w, h]
    vehicle_dossier: Optional[dict] = None
    message: str = ""


class AccessLogOut(BaseModel):
    id: int
    timestamp: datetime
    plate_number: str
    confidence: float
    status: str
    gate_action: str
    image_path: Optional[str]
    source: str
    camera_id: Optional[str] = "CAM-01"
    direction: Optional[str] = "ENTRY"
    vehicle_type: Optional[str] = "Car"
    vehicle_color: Optional[str] = "White"
    notes: Optional[str]


    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_scans: int
    today_scans: int
    authorized_count: int
    unauthorized_count: int
    blacklisted_count: int
    registered_vehicles_count: int
    gate_status: str
    recent_logs: List[AccessLogOut]
