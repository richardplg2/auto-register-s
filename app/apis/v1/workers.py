from typing import Dict, List

from fastapi import APIRouter, Depends

from app.core.containers import Container
from app.core.dependencies import get_container

router = APIRouter()


@router.get("/workers/status")
async def get_workers_status(
    container: Container = Depends(get_container),
) -> Dict[str, int]:
    """Get status of dynamic workers"""
    dynamic_manager = container.dynamic_worker_manager()

    return {
        "running_workers": dynamic_manager.get_worker_count(),
        "total_workers": len(dynamic_manager.workers),
    }


@router.get("/workers/devices")
async def get_device_workers(
    container: Container = Depends(get_container),
) -> List[str]:
    """Get list of devices with running workers"""
    dynamic_manager = container.dynamic_worker_manager()
    running_workers = dynamic_manager.get_running_workers()

    return list(running_workers.keys())


@router.post("/workers/stop/{device_code}")
async def stop_device_worker(
    device_code: str,
    container: Container = Depends(get_container),
) -> Dict[str, str]:
    """Stop worker for specific device"""
    dynamic_manager = container.dynamic_worker_manager()

    success = dynamic_manager.stop_worker(device_code)

    if success:
        return {"message": f"Worker for device {device_code} stopped successfully"}
    else:
        return {"message": f"No worker found for device {device_code}"}


@router.post("/workers/stop-all")
async def stop_all_workers(
    container: Container = Depends(get_container),
) -> Dict[str, str]:
    """Stop all dynamic workers"""
    dynamic_manager = container.dynamic_worker_manager()
    dynamic_manager.stop_all_workers()

    return {"message": "All dynamic workers stopped successfully"}
