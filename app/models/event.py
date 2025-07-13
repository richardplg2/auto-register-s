"""Event model"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text

from app.models.base import BaseModel


class Event(BaseModel):
    """Event model for storing camera events"""

    __tablename__ = "events"

    # Basic info
    event_type = Column(
        String(50), nullable=False
    )  # face_detection, motion, alarm, etc.
    event_id = Column(String(100), unique=True, nullable=False)

    # Source info
    camera_id = Column(String(36), ForeignKey("cameras.id"), nullable=False)
    occurred_at = Column(DateTime, default=datetime.now, nullable=False)

    # Event data
    payload = Column(JSON, nullable=True)  # Event-specific data
    event_metadata = Column(JSON, nullable=True)  # Additional metadata

    # Processing status
    processed = Column(
        String(20), default="pending", nullable=False
    )  # pending, processed, failed
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Webhook status
    webhook_sent = Column(
        String(20), default="pending", nullable=False
    )  # pending, sent, failed
    webhook_sent_at = Column(DateTime, nullable=True)
    webhook_attempts = Column(String(5), default="0", nullable=False)

    def __repr__(self):
        return f"<Event(event_type='{self.event_type}', camera_id='{self.camera_id}', occurred_at='{self.occurred_at}')>"
