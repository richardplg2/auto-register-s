"""Base model for all database entities"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields"""

    __abstract__ = True

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
