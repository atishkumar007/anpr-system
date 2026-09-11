import io
import csv
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.app.models import AccessLog
from backend.app.schemas import AccessLogOut, DashboardStats
from backend.app.services.stats_service import StatsService

router = APIRouter(prefix="/api/logs", tags=["Logs & Analytics"])

@router.get("/", response_model=List[AccessLogOut])
def get_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    plate: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    q = db.query(AccessLog)
    if status:
        q = q.filter(AccessLog.status == status.upper())
    if plate:
        q = q.filter(AccessLog.plate_number.ilike(f"%{plate}%"))

    return q.order_by(AccessLog.timestamp.desc()).offset(offset).limit(limit).all()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_statistics(db: Session = Depends(get_db)):
    return StatsService.get_dashboard_summary(db)


@router.get("/analytics/hourly")
def get_hourly_analytics(db: Session = Depends(get_db)):
    return StatsService.get_hourly_traffic(db)


@router.get("/export/csv")
def export_logs_csv(db: Session = Depends(get_db)):
    logs = db.query(AccessLog).order_by(AccessLog.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp (UTC)", "Plate Number", "Confidence (%)", "Status", "Gate Action", "Source", "Notes"])

    for log in logs:
        writer.writerow([
            log.id,
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
            log.plate_number,
            f"{int((log.confidence or 0) * 100)}%",
            log.status,
            log.gate_action,
            log.source,
            log.notes or ""
        ])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=anpr_access_logs.csv"}
    )


@router.delete("/clear")
def clear_all_logs(db: Session = Depends(get_db)):
    deleted = db.query(AccessLog).delete()
    db.commit()
    return {"success": True, "deleted_count": deleted}
