from typing import Any, Dict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.dtos.devices_dto import DevicePayload
from app.models.device import Device


class DeviceRepo:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """Device repository for managing device-related database operations."""
        self.session_factory = session_factory

    async def get_all_devices(self) -> list[Device]:
        """Retrieve all devices."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not available.")

        async with self.session_factory() as session:
            result = await session.execute(select(Device))
            return list(result.scalars().all())

    async def get_device_by_id(self, device_id: str) -> Device | None:
        """Retrieve a device by its ID."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not available.")

        async with self.session_factory() as session:
            result = await session.execute(select(Device).where(Device.id == device_id))
            return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Device | None:
        """Retrieve a device by its code."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not available.")

        async with self.session_factory() as session:
            result = await session.execute(select(Device).where(Device.code == code))
            return result.scalar_one_or_none()

    async def update_device(self, device: Device) -> Device:
        """Update an existing device object."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not available.")

        async with self.session_factory() as session:
            session.add(device)
            await session.commit()
            await session.refresh(device)
            return device

    async def update_device_by_id(
        self, device_id: str, updates: Dict[str, Any]
    ) -> Device | None:
        """Update device by ID with specific fields."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not available.")

        async with self.session_factory() as session:
            # Update the device
            await session.execute(
                update(Device).where(Device.id == device_id).values(**updates)
            )
            await session.commit()

            # Return the updated device
            result = await session.execute(select(Device).where(Device.id == device_id))
            return result.scalar_one_or_none()

    async def update_device_by_code(
        self, code: str, updates: Dict[str, Any]
    ) -> Device | None:
        """Update device by code with specific fields."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not available.")

        async with self.session_factory() as session:
            # Update the device
            await session.execute(
                update(Device).where(Device.code == code).values(**updates)
            )
            await session.commit()

            # Return the updated device
            result = await session.execute(select(Device).where(Device.code == code))
            return result.scalar_one_or_none()

    async def create_device(self, payload: DevicePayload) -> Device:
        """Create a new device."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not available.")

        async with self.session_factory() as session:
            device = Device(**payload.model_dump())
            session.add(device)
            await session.commit()
            await session.refresh(device)
            return device

    async def delete_device_by_code(self, code: str) -> None:
        """Delete a device by its code."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not available.")

        async with self.session_factory() as session:
            result = await session.execute(select(Device).where(Device.code == code))
            device = result.scalar_one_or_none()
            if device:
                await session.delete(device)
                await session.commit()

    async def get_device_by_code(self, code: str) -> Device | None:
        """Retrieve a device by its code."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not available.")

        async with self.session_factory() as session:
            result = await session.execute(select(Device).where(Device.code == code))
            return result.scalar_one_or_none()
