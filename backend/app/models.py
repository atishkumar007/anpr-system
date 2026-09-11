import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from backend.app.database import Base

class VehicleRegistry(Base):
    __tablename__ = "vehicle_registry"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(32), unique=True, index=True, nullable=False)
    owner_name = Column(String(128), nullable=False)
    vehicle_model = Column(String(128), nullable=True)
    access_tier = Column(String(32), default="WHITELIST")  # WHITELIST, BLACKLIST, GUEST
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    plate_number = Column(String(32), index=True, nullable=False)
    confidence = Column(Float, default=0.0)
    status = Column(String(32), default="UNAUTHORIZED")  # AUTHORIZED, UNAUTHORIZED, BLACKLISTED
    gate_action = Column(String(32), default="DENIED")   # OPENED, DENIED, MANUAL_OVERRIDE
    image_path = Column(String(256), nullable=True)
    source = Column(String(64), default="WEBCAM")        # WEBCAM, VIRTUAL_CAMERA, UPLOAD, SIMULATOR
    notes = Column(Text, nullable=True)

class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True)
    value = Column(String(256))
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
