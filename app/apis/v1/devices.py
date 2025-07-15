"""Device management API endpoints."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from app.core.containers import Container
from app.dtos.devices_dto import DevicePayload, UpdateDevicePayload
from app.repos.device_repo import DeviceRepo
from app.services.dahua_netsdk_service import DahuaNetSDKService

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/{device_code}/recordings")
@inject
async def get_device_recordings(
    device_code: str,
    dahua_net_sdk_service: DahuaNetSDKService = Depends(
        Provide[Container.dahua_netsdk_service]
    ),
    n_rec: int = 1,
    by_asc_order: bool = False,
):
    """Get device recordings by device code using dependency injection."""
    try:
        records = dahua_net_sdk_service.find_records(
            device_code, n_rec=n_rec, by_asc_order=by_asc_order
        )

        return records

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{device_code}/recordings/from-records")
@inject
async def get_device_recordings_from(
    device_code: str,
    from_rec_no: int,
    dahua_net_sdk_service: DahuaNetSDKService = Depends(
        Provide[Container.dahua_netsdk_service]
    ),
    n_rec: int = 1,
    by_asc_order: bool = False,
):
    """Get device recordings from a specific record number using dependency injection."""
    try:
        records = dahua_net_sdk_service.find_records_by_rec_no(
            device_code, from_rec_no=from_rec_no, n_rec=n_rec, by_asc_order=by_asc_order
        )

        return records

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{device_code}/info")
@inject
async def get_device_info(
    device_code: str,
    dahua_net_sdk_service: DahuaNetSDKService = Depends(
        Provide[Container.dahua_netsdk_service]
    ),
):
    """Get device info by device code using dependency injection."""
    try:
        device_info = dahua_net_sdk_service.get_device_info(device_code)
        return device_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
