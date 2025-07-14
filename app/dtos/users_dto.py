from typing import Optional

from pydantic import BaseModel, Field


class UserPayload(BaseModel):
    user_id: str = Field(description="The unique identifier for the user")

    card_name: str = Field(description="The name on the user's card")
    card_no: str = Field(description="The card number")
    sz_pw: Optional[str] = Field(description="The user's password", default=None)

    valid_start_time: Optional[int] = Field(
        description="The start time of the user's validity period", default=None, gt=0
    )
    valid_end_time: Optional[int] = Field(
        description="The end time of the user's validity period", default=None, gt=0
    )


class AddUserPayload(UserPayload):
    pass


class UpdateUserPayload(UserPayload):
    pass
