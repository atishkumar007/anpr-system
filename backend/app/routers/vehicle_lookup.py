from fastapi import APIRouter, HTTPException, Path
from backend.app.services.vehicle_lookup_service import VehicleLookupService

router = APIRouter(prefix="/api/vehicle", tags=["Vehicle & Challan Lookup"])

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
