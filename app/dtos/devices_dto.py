from typing import Optional

from pydantic import BaseModel, Field


class DevicePayload(BaseModel):
    name: str = Field(..., description="The name of the device")
    code: str = Field(..., description="The code of the device")
    username: str = Field(..., description="The username for the device")
    password: str = Field(..., description="The password for the device")

    enabled_access_control_event: Optional[bool] = Field(
        ..., description="Whether the access control event is enabled"
    )

    company_code: str = Field(..., description="The company code for the device")

    is_active: Optional[bool] = Field(..., description="Whether the device is active")


class UpdateDevicePayload(BaseModel):
    name: Optional[str] = Field(None, description="The name of the device")
    code: Optional[str] = Field(None, description="The code of the device")
    username: Optional[str] = Field(None, description="The username for the device")
    password: Optional[str] = Field(None, description="The password for the device")
    enabled_access_control_event: Optional[bool] = Field(
        None, description="Whether the access control event is enabled"
    )
    company_code: Optional[str] = Field(
        None, description="The company code for the device"
    )
    is_active: Optional[bool] = Field(None, description="Whether the device is active")
