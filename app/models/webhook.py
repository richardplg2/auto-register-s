"""Webhook model"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from app.models.base import BaseModel


class Webhook(BaseModel):
    """Webhook model for storing webhook configurations"""

    __tablename__ = "webhooks"

    # Basic info
    name = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=False)
    method = Column(String(10), default="POST", nullable=False)

    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    event_types = Column(JSON, nullable=True)  # List of event types to trigger

    # Authentication
    auth_type = Column(String(20), nullable=True)  # basic, bearer, api_key
    auth_config = Column(JSON, nullable=True)  # Authentication configuration

    # Headers and payload
    headers = Column(JSON, nullable=True)  # Custom headers
    payload_template = Column(Text, nullable=True)  # Custom payload template

    # Retry configuration
    max_retries = Column(Integer, default=3, nullable=False)
    retry_delay = Column(Integer, default=5, nullable=False)  # seconds
    timeout = Column(Integer, default=30, nullable=False)  # seconds

    # Status
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return (
            f"<Webhook(name='{self.name}', url='{self.url}', active={self.is_active})>"
        )
