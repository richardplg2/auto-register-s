from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.device import Device


class DeviceRepo:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """Device repository for managing device-related database operations."""
        self.session_factory = session_factory

    async def get_device_by_id(self, device_id: str) -> Device | None:
        """Retrieve a device by its ID."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not available.")

        async with self.session_factory() as session:
            result = await session.execute(select(Device).where(Device.id == device_id))
            return result.scalar_one_or_none()
