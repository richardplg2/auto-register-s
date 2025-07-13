from fastapi import APIRouter

from app.apis.v1.devices import router as devices_router
from app.apis.v1.healthy import router as healthy_router
from app.apis.v1.users import router as users_router

router_v1 = APIRouter(prefix="/v1", tags=["v1"])
router_v1.include_router(healthy_router)
router_v1.include_router(devices_router)
router_v1.include_router(users_router)
