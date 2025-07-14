from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.containers import Container
from app.dtos.users_dto import AddFacePayload, AddUserPayload
from app.services.dahua_netsdk_service import DahuaNetSDKService
from app.types.dahua_netsdk_types import UserPayload

router = APIRouter(prefix="/device/{device_code}/users", tags=["users"])


@router.post("")
@inject
async def add_user(
    device_code: str,
    body: AddUserPayload,
    dahua_net_sdk_service: DahuaNetSDKService = Depends(
        Provide[Container.dahua_netsdk_service]
    ),
):

    demo_payload = UserPayload(
        card_name=body.card_name,
        card_no=body.card_no,
        user_id=body.user_id,
        sz_pw=body.sz_pw,
    )
    try:

        dahua_net_sdk_service.add_user(device_code, demo_payload)

        if body.face_image_url:
            dahua_net_sdk_service.add_face(
                device_code, demo_payload.user_id, body.face_image_url
            )
    except Exception as e:
        return {"error": str(e)}

    return {"message": "User added successfully"}


@router.get("")
@inject
async def list_users(
    device_code: str,
    dahua_net_sdk_service: DahuaNetSDKService = Depends(
        Provide[Container.dahua_netsdk_service]
    ),
):
    """List users for a specific device using dependency injection."""
    try:
        users = dahua_net_sdk_service.list_users(device_code)
        return users
    except Exception as e:
        return {"error": str(e)}


@router.get("/{user_id}")
@inject
async def get_user(
    device_code: str,
    user_id: str,
    dahua_net_sdk_service: DahuaNetSDKService = Depends(
        Provide[Container.dahua_netsdk_service]
    ),
):
    """Get a specific user for a device."""
    try:
        print("get user id====")
        user = dahua_net_sdk_service.find_user(device_code, user_id)
        return user
    except Exception as e:
        return {"error": str(e)}


@router.post("/{user_id}/face")
async def add_face(
    device_code: str,
    user_id: str,
    body: AddFacePayload,
    dahua_net_sdk_service: DahuaNetSDKService = Depends(
        Provide[Container.dahua_netsdk_service]
    ),
):
    """Add a face to a specific user for a device."""
    try:
        dahua_net_sdk_service.add_face(device_code, user_id, face_data)
        return {"message": "Face added successfully"}
    except Exception as e:
        return {"error": str(e)}
