"""Device management API endpoints."""

from typing import Annotated

from dependency_injector.wiring import Provide
from fastapi import APIRouter, Depends, HTTPException

from app.core.containers import Container
from app.repos.device_repo import DeviceRepo

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/{device_id}")
async def get_device(
    device_id: str,
    device_repo: Annotated[DeviceRepo, Depends(Provide[Container.device_repo])],
):
    """Get device by ID using dependency injection."""
    try:
        device = await device_repo.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        return {
            "id": device.id,
            "name": device.name,
            "code": device.code,
            "ip": device.ip,
            "port": device.port,
            "is_online": device.is_online,
            "is_active": device.is_active,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/")
async def list_devices(
    device_repo: Annotated[DeviceRepo, Depends(Provide[Container.device_repo])],
):
    """List all devices using dependency injection."""
    # This would need a list method in DeviceRepo
    return {"message": "Device list endpoint - implement get_all_devices in DeviceRepo"}
