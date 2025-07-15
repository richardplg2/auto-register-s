from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.models.base import BaseModel


class Device(BaseModel):
    """Device model representing a physical or virtual device"""

    __tablename__ = "dms_devices"

    name = Column(String(255), nullable=False)
    code = Column(
        String(100), unique=True, nullable=False
    )  # Device code, unique identifier for the device

    serial_number = Column(String(100), unique=True, nullable=True)
    model = Column(String(100), nullable=True)
    manufacturer = Column(String(100), default="Dahua", nullable=True)
    company_code = Column(String(255), nullable=True)

    # Network info
    ip = Column(String(45), nullable=True)  # Support IPv6
    port = Column(Integer, default=37777, nullable=True)

    # Authentication
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)

    # Status
    is_online = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Auto-discovery info
    last_connected_at = Column(DateTime, nullable=True)
    last_disconnected_at = Column(DateTime, nullable=True)

    enabled_access_control_event = Column(Boolean, default=False, nullable=False)

    last_uploaded_rec_no = Column(Integer, default=-1, nullable=False)
