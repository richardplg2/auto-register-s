from typing import Optional

from NetSDK.SDK_Enum import EM_AUTOREGISTER_TYPE  # type: ignore


class DeviceAutoRegisterEvent:
    def __init__(
        self, device_code: str, command: EM_AUTOREGISTER_TYPE, ip: str, port: int
    ):
        self.device_code = device_code
        self.command = command
        self.ip = ip
        self.port = port


class UserPayload:
    def __init__(
        self,
        user_id: str,
        card_name: str,
        card_no: str,
        citizen_id_no: Optional[str] = None,
        sz_pw: Optional[str] = None,
        valid_start_time: Optional[int] = None,
        valid_end_time: Optional[int] = None,
        user_name: Optional[str] = None,
        password: Optional[str] = None,
        first_enter: bool = False,
    ):
        self.user_id = user_id
        self.card_name = card_name
        self.card_no = card_no
        self.sz_pw = sz_pw
        self.valid_start_time = valid_start_time
        self.valid_end_time = valid_end_time
        self.user_name = user_name
        self.password = password
        self.first_enter = first_enter
        self.citizen_id_no = citizen_id_no
