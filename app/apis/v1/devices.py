"""Device management API endpoints."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from app.core.containers import Container
from app.dtos.devices_dto import DevicePayload, UpdateDevicePayload
from app.repos.device_repo import DeviceRepo

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/{device_code}")
@inject
async def get_device(
    device_code: str,
    device_repo: Annotated[DeviceRepo, Depends(Provide[Container.device_repo])],
):
    """Get device by code using dependency injection."""
    try:
        device = await device_repo.get_device_by_code(device_code)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        return device
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/")
@inject
async def list_devices(
    device_repo: Annotated[DeviceRepo, Depends(Provide[Container.device_repo])],
):
    """List all devices using dependency injection."""
    devices = await device_repo.get_all_devices()
    return devices


@router.post("/")
@inject
async def create_device(
    device_repo: Annotated[DeviceRepo, Depends(Provide[Container.device_repo])],
    device_data: DevicePayload,
):
    """Create a new device using dependency injection."""
    try:
        device = await device_repo.create_device(device_data)
        return {"id": device.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{device_code}")
@inject
async def update_device(
    device_code: str,
    device_repo: Annotated[DeviceRepo, Depends(Provide[Container.device_repo])],
    device_data: UpdateDevicePayload,
):
    """Update an existing device using dependency injection."""
    try:
        device = await device_repo.update_device_by_code(
            device_code, device_data.model_dump()
        )
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        return {"id": device.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{device_code}")
@inject
async def delete_device(
    device_code: str,
    device_repo: Annotated[DeviceRepo, Depends(Provide[Container.device_repo])],
):
    """Delete a device using dependency injection."""
    try:
        await device_repo.delete_device_by_code(device_code)
        return {"detail": "Device deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
