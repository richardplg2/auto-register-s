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
    ip = Column(String(45), nullable=False)  # Support IPv6
    port = Column(Integer, default=37777, nullable=False)

    # Authentication
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)

    # Status
    is_online = Column(Boolean, default=False, nullable=False)
    last_seen_at = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    # Auto-discovery info
    discovered_at = Column(DateTime, nullable=True)
    auto_registered = Column(Boolean, default=False, nullable=False)
