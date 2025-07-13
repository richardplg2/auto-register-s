from fastapi import APIRouter, Depends

from app.core.containers import Container
from app.core.dependencies import get_container

router = APIRouter(prefix="/healthy", tags=["healthy"])


@router.get("/")
async def health_check():
    return {"status": "healthy"}


@router.get("/event-bus")
async def event_bus_stats(container: Container = Depends(get_container)):
    """Get event bus statistics"""
    event_bus = container.event_bus()
    stats = event_bus.get_stats()
    return {"status": "healthy", "event_bus": stats}
