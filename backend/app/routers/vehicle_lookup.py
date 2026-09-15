from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel
from typing import Optional
from backend.app.services.vehicle_lookup_service import VehicleLookupService

router = APIRouter(prefix="/api/vehicle", tags=["Vehicle & Challan Lookup"])

class ApiKeysPayload(BaseModel):
    rekor_api_key: Optional[str] = None
    rapidapi_key: Optional[str] = None

@router.get("/details/{plate_number}")
def get_vehicle_full_details(plate_number: str = Path(..., description="Vehicle license plate number")):
    """
    Fetches comprehensive vehicle RC registration info, owner details,
    insurance policy status, and traffic e-challans.
    """
    data = VehicleLookupService.get_vehicle_dossier(plate_number)
    if not data or not data.get("success"):
        raise HTTPException(status_code=404, detail="Vehicle details could not be retrieved")
    return data

@router.get("/challans/{plate_number}")
def get_vehicle_challans(plate_number: str = Path(...)):
    """
    Fetches traffic violation history and pending e-challans for a license plate.
    """
    data = VehicleLookupService.get_vehicle_dossier(plate_number)
    if not data or not data.get("success"):
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return data.get("challan_summary", {})

@router.get("/settings/status")
def get_api_settings_status():
    """
    Returns whether live Rekor or RapidAPI keys are configured.
    """
    return VehicleLookupService.get_api_status()

@router.post("/settings/apikey")
def set_live_api_keys(payload: ApiKeysPayload):
    """
    Updates live Rekor CarCheck or RapidAPI keys dynamically.
    """
    VehicleLookupService.set_api_keys(
        rekor_key=payload.rekor_api_key,
        rapidapi_key=payload.rapidapi_key
    )
    return {
        "success": True,
        "message": "API keys updated successfully.",
        "status": VehicleLookupService.get_api_status()
    }
