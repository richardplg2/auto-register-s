from fastapi import APIRouter, Depends, HTTPException

from app.core.containers import Container
from app.core.dependencies import get_container

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
async def get_users(device_code: str, container: Container = Depends(get_container)):
    dh = container.dahua_netsdk_service()
    dh.add_user_demo("test_newfacereg")
    return {"message": "User endpoint - implement get_user in UserRepo"}
