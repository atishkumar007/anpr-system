import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import AccessLog, VehicleRegistry
from backend.app.services.barrier_service import BarrierService

class StatsService:
    @staticmethod
    def get_dashboard_summary(db: Session):
        now = datetime.datetime.utcnow()
        today_start = datetime.datetime(now.year, now.month, now.day)

        total_scans = db.query(AccessLog).count()
        today_scans = db.query(AccessLog).filter(AccessLog.timestamp >= today_start).count()
        authorized_count = db.query(AccessLog).filter(AccessLog.status == "AUTHORIZED").count()
        unauthorized_count = db.query(AccessLog).filter(AccessLog.status == "UNAUTHORIZED").count()
        blacklisted_count = db.query(AccessLog).filter(AccessLog.status == "BLACKLISTED").count()
        registered_count = db.query(VehicleRegistry).count()

        barrier = BarrierService()
        barrier_status = barrier.get_status()["state"]

        recent_logs = (
            db.query(AccessLog)
            .order_by(AccessLog.timestamp.desc())
            .limit(10)
            .all()
        )

        return {
            "total_scans": total_scans,
            "today_scans": today_scans,
            "authorized_count": authorized_count,
            "unauthorized_count": unauthorized_count,
            "blacklisted_count": blacklisted_count,
            "registered_vehicles_count": registered_count,
            "gate_status": barrier_status,
            "recent_logs": recent_logs
        }

    @staticmethod
    def get_hourly_traffic(db: Session):
        """Returns scan counts grouped by hour for analytics charts."""
        logs = db.query(AccessLog.timestamp, AccessLog.status).all()
        hours_data = {f"{h:02d}:00": {"authorized": 0, "unauthorized": 0, "blacklisted": 0} for h in range(24)}

        for log in logs:
            if log.timestamp:
                hr_key = f"{log.timestamp.hour:02d}:00"
                status_lower = (log.status or "").lower()
                if status_lower in hours_data[hr_key]:
                    hours_data[hr_key][status_lower] += 1

        return hours_data
